function Write-Log {
    param([string]$Message)
    $ts = (Get-Date).ToString('s')
    $line = "[$ts] $Message"
    Write-Output $line
    Add-Content -Path $Global:QA_LOG -Value $line
}

function Ensure-VenvPython {
    # Prefer activated environment, otherwise use .venv path
    if ($env:VIRTUAL_ENV) {
        $py = Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe'
        if (Test-Path $py) { return $py }
    }
    $local = Join-Path (Get-Location) '.venv\Scripts\python.exe'
    if (Test-Path $local) { return $local }
    throw 'Python interpreter not found. Activate venv or create .venv.'
}

function Invoke-Api {
    param(
        [string]$Method = 'GET',
        [string]$Path,
        $Body = $null,
        $Token = $null
    )
    $uri = "$Global:BASE_URL$Path"
    $headers = @{}
    if ($Token) { $headers['Authorization'] = "Bearer $Token" }
    try {
        if ($Body -ne $null) {
            $json = $Body | ConvertTo-Json -Depth 10
            $resp = Invoke-RestMethod -Method $Method -Uri $uri -Body $json -ContentType 'application/json' -Headers $headers -ErrorAction Stop
        } else {
            $resp = Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -ErrorAction Stop
        }
        return @{ ok = $true; status = 200; body = $resp }
    } catch [System.Net.WebException] {
        $resp = $_.Exception.Response
        if ($resp) {
            $status = $resp.StatusCode.value__
        } else { $status = 0 }
        return @{ ok = $false; status = $status; body = $_.Exception.Message }
    } catch {
        return @{ ok = $false; status = 0; body = $_.Exception.Message }
    }
}

function New-UniqueEmail {
    param([string]$prefix = 'qa')
    $ts = Get-Date -Format 'yyyyMMddHHmmssfff'
    return "$prefix+$ts@local.qa"
}

function Register-User {
    param([string]$email, [string]$password = 'Passw0rd!', [string]$role = 'buyer')
    $body = @{ email = $email; password = $password; role = $role }
    return Invoke-Api -Method 'POST' -Path '/api/auth/register' -Body $body
}

function Login-User {
    param([string]$email, [string]$password = 'Passw0rd!')
    $body = @{ email = $email; password = $password }
    $r = Invoke-Api -Method 'POST' -Path '/api/auth/login' -Body $body
    if (-not $r.ok) { return $null }
    $b = $r.body
    # Try common token shapes
    if ($null -ne $b) {
        try {
            if ($b.token) { return $b.token }
        } catch {}
        try {
            if ($b.access_token) { return $b.access_token }
        } catch {}
        try {
            if ($b.data -and $b.data.token) { return $b.data.token }
        } catch {}
        # If body is a raw json string, try parse
        if ($b -is [string]) {
            try {
                $j = $b | ConvertFrom-Json
                if ($j.token) { return $j.token }
                if ($j.access_token) { return $j.access_token }
                if ($j.data -and $j.data.token) { return $j.data.token }
            } catch {}
        }
    }
    return $null
}

function Start-ServerJob {
    param([string]$PythonExe, [string]$AppFile = 'main.py')
    $script = "$PythonExe $AppFile"
    Write-Log "Starting server: $script"
    $job = Start-Job -ScriptBlock { param($cmd) & cmd /c $cmd } -ArgumentList $script
    Start-Sleep -Seconds 2
    return $job
}

function Stop-ServerJob {
    param($job)
    if ($null -ne $job) {
        Write-Log 'Stopping server job'
        try { Stop-Job -Job $job -ErrorAction SilentlyContinue; Receive-Job -Job $job -ErrorAction SilentlyContinue } catch { }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
}

function Wait-Health {
    param([int]$tries=20)
    for ($i=0; $i -lt $tries; $i++) {
        $r = Invoke-Api -Path '/api/health'
        if ($r.ok) { Write-Log 'Health OK'; return $true }
        Start-Sleep -Seconds 1
    }
    Write-Log 'Health check failed'
    return $false
}

function Db-Snapshot {
    param([string]$tag)
    $src = Join-Path (Get-Location) 'instance\fliptrybe.db'
    if (Test-Path $src) {
        $ts = Get-Date -Format 'yyyyMMddHHmmss'
        $dst = Join-Path $Global:ARTIFACT_DIR "db_snapshot_${tag}_$ts.db"
        Copy-Item -Path $src -Destination $dst -Force
        Write-Log "DB snapshot saved: $dst"
        return $dst
    } else {
        Write-Log 'DB not found for snapshot'
        return $null
    }
}
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-QaState {
    param(
        [Parameter(Mandatory = $true)][string]$BackendRoot,
        [Parameter(Mandatory = $true)][string]$BaseUrl
    )

    $qaRoot = Join-Path $BackendRoot "qa"
    $artifactDir = Join-Path $qaRoot "artifacts"
    if (-not (Test-Path $artifactDir)) {
        New-Item -ItemType Directory -Path $artifactDir -Force | Out-Null
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $artifact = Join-Path $artifactDir ("qa_run_{0}.log" -f $stamp)
    New-Item -ItemType File -Path $artifact -Force | Out-Null

    $python = Join-Path $BackendRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        throw "Python not found at $python"
    }

    $state = [ordered]@{
        BackendRoot = $BackendRoot
        QaRoot = $qaRoot
        ArtifactDir = $artifactDir
        ArtifactPath = $artifact
        BaseUrl = $BaseUrl
        Python = $python
        Results = New-Object System.Collections.ArrayList
        ServerProcessId = $null
        Context = @{}
    }

    Write-Log -State $state -Message "QA run started"
    Write-Log -State $state -Message ("BackendRoot={0}" -f $BackendRoot)
    Write-Log -State $state -Message ("BaseUrl={0}" -f $BaseUrl)
    return $state
}

function Write-Log {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Message
    )
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -Path $State.ArtifactPath -Value $line
}

function Add-Result {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Phase,
        [Parameter(Mandatory = $true)][string]$Test,
        [Parameter(Mandatory = $true)][bool]$Pass,
        [Parameter(Mandatory = $true)][string]$Status,
        [string]$Detail = ""
    )

    $row = [pscustomobject]@{
        Phase = $Phase
        Test = $Test
        Result = if ($Pass) { "PASS" } else { "FAIL" }
        Status = $Status
        Detail = $Detail
    }
    [void]$State.Results.Add($row)
    Write-Log -State $State -Message ("[{0}] {1} => {2} ({3}) {4}" -f $Phase, $Test, $row.Result, $Status, $Detail)
}

function Print-ResultTable {
    param([Parameter(Mandatory = $true)]$State)
    Write-Host ""
    Write-Host "=== QA RESULT TABLE ==="
    $State.Results | Format-Table -AutoSize | Out-String -Width 240 | ForEach-Object { Write-Host $_ }
    Add-Content -Path $State.ArtifactPath -Value "`n=== QA RESULT TABLE ==="
    Add-Content -Path $State.ArtifactPath -Value (($State.Results | Format-Table -AutoSize | Out-String -Width 240))
}

function Get-FailCount {
    param([Parameter(Mandatory = $true)]$State)
    return @($State.Results | Where-Object { $_.Result -eq "FAIL" }).Count
}

function Assert-Status {
    param(
        [Parameter(Mandatory = $true)]$Resp,
        [Parameter(Mandatory = $true)][int[]]$Allowed
    )
    return $Allowed -contains [int]$Resp.StatusCode
}

function Invoke-Api {
    param(
        [Parameter(Mandatory = $true)]$State,
        [string]$Method = "GET",
        [Parameter(Mandatory = $true)][string]$Path,
        [hashtable]$Headers = @{},
        $BodyObj = $null
    )

    $uri = "{0}{1}" -f $State.BaseUrl.TrimEnd('/'), $Path
    try {
        if ($null -ne $BodyObj) {
            $body = $BodyObj | ConvertTo-Json -Depth 30 -Compress
            $resp = Invoke-WebRequest -Method $Method -Uri $uri -Headers $Headers -ContentType "application/json" -Body $body -UseBasicParsing
        }
        else {
            $resp = Invoke-WebRequest -Method $Method -Uri $uri -Headers $Headers -UseBasicParsing
        }

        $json = $null
        try { $json = $resp.Content | ConvertFrom-Json } catch {}

        return [pscustomobject]@{
            StatusCode = [int]$resp.StatusCode
            Body = [string]$resp.Content
            Json = $json
            Uri = $uri
            Method = $Method
        }
    }
    catch {
        $status = -1
        $body = ""
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
            $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $body = $sr.ReadToEnd()
        }
        elseif ($_.ErrorDetails) {
            $body = $_.ErrorDetails.Message
        }
        else {
            $body = $_.Exception.Message
        }

        $json = $null
        try { $json = $body | ConvertFrom-Json } catch {}

        return [pscustomobject]@{
            StatusCode = [int]$status
            Body = [string]$body
            Json = $json
            Uri = $uri
            Method = $Method
        }
    }
}

function Register-Role {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Role,
        [Parameter(Mandatory = $true)][hashtable]$Payload
    )
    return Invoke-Api -State $State -Method "POST" -Path ("/api/auth/register/{0}" -f $Role) -BodyObj $Payload
}

function Login-User {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Email,
        [Parameter(Mandatory = $true)][string]$Password
    )
    return Invoke-Api -State $State -Method "POST" -Path "/api/auth/login" -BodyObj @{ email = $Email; password = $Password }
}

function Invoke-DbQuery {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Sql,
        [object[]]$Params = @()
    )

    $oldSql = $env:QA_SQL
    $oldParams = $env:QA_PARAMS
    $env:QA_SQL = $Sql
    $env:QA_PARAMS = ($Params | ConvertTo-Json -Compress)

    try {
        $py = @"
import json, os, sqlite3
sql = os.environ.get("QA_SQL", "")
params = json.loads(os.environ.get("QA_PARAMS", "[]") or "[]")
if not isinstance(params, list):
    params = [params]
con = sqlite3.connect(r"instance/fliptrybe.db")
cur = con.cursor()
cur.execute(sql, tuple(params))
rows = cur.fetchall()
cols = [d[0] for d in (cur.description or [])]
con.close()
print(json.dumps({"columns": cols, "rows": rows}, default=str))
"@
        $raw = $py | & $State.Python -
        $lines = @()
        if ($raw -is [System.Array]) {
            $lines = @($raw | ForEach-Object { [string]$_ } | Where-Object { $_.Trim() -ne "" })
        }
        elseif ($null -ne $raw) {
            $lines = @([string]$raw)
        }

        $reversed = @($lines)
        [array]::Reverse($reversed)
        foreach ($line in $reversed) {
            try {
                $parsed = $line | ConvertFrom-Json
                if ($parsed -and ($parsed.PSObject.Properties.Name -contains "rows")) {
                    return $parsed
                }
            }
            catch {}
        }

        return [pscustomobject]@{ columns = @(); rows = @() }
    }
    finally {
        $env:QA_SQL = $oldSql
        $env:QA_PARAMS = $oldParams
    }
}

function Get-DbScalar {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Sql,
        [object[]]$Params = @()
    )
    $res = Invoke-DbQuery -State $State -Sql $Sql -Params $Params
    if (-not $res -or -not ($res.PSObject.Properties.Name -contains "rows")) { return $null }
    $rows = @($res.rows)
    if ($rows.Count -eq 0) { return $null }
    if (-not ($rows[0] -is [System.Collections.IList])) { return $null }
    if ($rows[0].Count -eq 0) { return $null }
    return $rows[0][0]
}

function Get-AvailToken {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][int]$OrderId
    )
    $sql = "SELECT response_token FROM availability_confirmations WHERE order_id=? ORDER BY id DESC LIMIT 1"
    $token = Get-DbScalar -State $State -Sql $sql -Params @($OrderId)
    return [string]$token
}

function Get-OrderField {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][int]$OrderId,
        [Parameter(Mandatory = $true)][string]$Field
    )
    $sql = "SELECT " + $Field + " FROM orders WHERE id=?"
    return [string](Get-DbScalar -State $State -Sql $sql -Params @($OrderId))
}

function Get-LatestOrderByRef {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][string]$Reference
    )
    $sql = "SELECT id, buyer_id, merchant_id, status, escrow_status, payment_reference FROM orders WHERE payment_reference=? ORDER BY id DESC LIMIT 1"
    $res = Invoke-DbQuery -State $State -Sql $sql -Params @($Reference)
    return $res
}

function Db-SnapOrder {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][int]$OrderId,
        [Parameter(Mandatory = $true)][string]$Label
    )

    Write-Log -State $State -Message ("DB SNAP {0} order={1}" -f $Label, $OrderId)

    $q1 = Invoke-DbQuery -State $State -Sql "SELECT id, order_id, step, attempts, max_attempts, locked, qr_required, qr_verified, unlocked_at, expires_at, admin_unlock_expires_at FROM escrow_unlocks WHERE order_id=? ORDER BY id ASC" -Params @($OrderId)
    $q2 = Invoke-DbQuery -State $State -Sql "SELECT id, order_id, step, issued_to_role, status, scanned_by_user_id, issued_at, scanned_at, expires_at FROM qr_challenges WHERE order_id=? ORDER BY id ASC" -Params @($OrderId)
    $q3 = Invoke-DbQuery -State $State -Sql "SELECT id, status, pickup_code, dropoff_code, pickup_code_attempts, dropoff_code_attempts, pickup_confirmed_at, dropoff_confirmed_at, escrow_status, escrow_hold_amount, escrow_release_at FROM orders WHERE id=?" -Params @($OrderId)

    $q1Rows = if ($q1 -and ($q1.PSObject.Properties.Name -contains "rows")) { $q1.rows } else { @() }
    $q2Rows = if ($q2 -and ($q2.PSObject.Properties.Name -contains "rows")) { $q2.rows } else { @() }
    $q3Rows = if ($q3 -and ($q3.PSObject.Properties.Name -contains "rows")) { $q3.rows } else { @() }
    Write-Log -State $State -Message ("escrow_unlocks=" + (($q1Rows | ConvertTo-Json -Compress)))
    Write-Log -State $State -Message ("qr_challenges=" + (($q2Rows | ConvertTo-Json -Compress)))
    Write-Log -State $State -Message ("orders=" + (($q3Rows | ConvertTo-Json -Compress)))
}

function Get-CodeFromApiOrDb {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][int]$OrderId,
        [Parameter(Mandatory = $true)][hashtable]$BuyerHeaders,
        [Parameter(Mandatory = $true)][ValidateSet('pickup','dropoff')][string]$Kind
    )

    $codesResp = Invoke-Api -State $State -Method "GET" -Path ("/api/orders/{0}/codes" -f $OrderId) -Headers $BuyerHeaders
    $fromApi = $null
    if ($codesResp.Json) {
        $props = $codesResp.Json.PSObject.Properties.Name
        if ($Kind -eq 'pickup' -and ($props -contains 'pickup_code') -and $codesResp.Json.pickup_code) { $fromApi = [string]$codesResp.Json.pickup_code }
        if ($Kind -eq 'dropoff' -and ($props -contains 'dropoff_code') -and $codesResp.Json.dropoff_code) { $fromApi = [string]$codesResp.Json.dropoff_code }
    }
    if ($fromApi) { return $fromApi }
    if ($Kind -eq 'pickup') { return (Get-OrderField -State $State -OrderId $OrderId -Field 'pickup_code') }
    return (Get-OrderField -State $State -OrderId $OrderId -Field 'dropoff_code')
}

function Approve-RoleRequest {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][hashtable]$AdminHeaders,
        [Parameter(Mandatory = $true)][int]$UserId,
        [Parameter(Mandatory = $true)][string]$RequestedRole,
        [string]$AdminNote = "QA approve"
    )

    $pending = Invoke-Api -State $State -Method "GET" -Path "/api/admin/role-requests?status=PENDING" -Headers $AdminHeaders
    if ($pending.StatusCode -ne 200 -or -not $pending.Json -or -not $pending.Json.items) {
        return [pscustomobject]@{ StatusCode = $pending.StatusCode; Body = $pending.Body; Ok = $false }
    }

    $req = $pending.Json.items | Where-Object {
        [int]$_.user_id -eq [int]$UserId -and ([string]$_.requested_role).ToLower() -eq $RequestedRole.ToLower()
    } | Select-Object -First 1

    if (-not $req) {
        return [pscustomobject]@{ StatusCode = 404; Body = "pending request not found"; Ok = $false }
    }

    $resp = Invoke-Api -State $State -Method "POST" -Path ("/api/admin/role-requests/{0}/approve" -f $req.id) -Headers $AdminHeaders -BodyObj @{ admin_note = $AdminNote }
    $ok = $resp.StatusCode -in @(200, 201)
    return [pscustomobject]@{ StatusCode = $resp.StatusCode; Body = $resp.Body; Ok = $ok }
}

function Wait-Health {
    param(
        [Parameter(Mandatory = $true)]$State,
        [int]$TimeoutSeconds = 45
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $h = Invoke-Api -State $State -Method "GET" -Path "/api/health"
        if ($h.StatusCode -eq 200) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Stop-Port5000 {
    $conns = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) { return }
    $owningPids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $owningPids) {
        try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch {}
    }
}

function Start-QaServer {
    param([Parameter(Mandatory = $true)]$State)

    Stop-Port5000
    Start-Sleep -Milliseconds 600

    $outLog = Join-Path $State.ArtifactDir ("server_out_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $errLog = Join-Path $State.ArtifactDir ("server_err_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

    $args = "-m flask run --host 127.0.0.1 --port 5000 --no-reload --no-debugger"
    $proc = Start-Process -FilePath $State.Python -ArgumentList $args -WorkingDirectory $State.BackendRoot -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    $State.ServerProcessId = [int]$proc.Id
    Write-Log -State $State -Message ("Server started PID={0}" -f $State.ServerProcessId)

    if (-not (Wait-Health -State $State -TimeoutSeconds 45)) {
        throw "Server did not become healthy in time"
    }
}

function Stop-QaServer {
    param([Parameter(Mandatory = $true)]$State)
    if ($State.ServerProcessId) {
        try {
            Stop-Process -Id ([int]$State.ServerProcessId) -Force -ErrorAction Stop
            Write-Log -State $State -Message ("Server stopped PID={0}" -f $State.ServerProcessId)
        }
        catch {
            Write-Log -State $State -Message ("Server stop skipped PID={0}" -f $State.ServerProcessId)
        }
        $State.ServerProcessId = $null
    }
}

function New-UniqueEmail {
    param([Parameter(Mandatory = $true)][string]$Prefix)
    return ("{0}_{1}@t.com" -f $Prefix, (Get-Random))
}

function New-DeliveryOrder {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)][int]$MerchantId,
        [Parameter(Mandatory = $true)][int]$DriverId,
        [Parameter(Mandatory = $true)][hashtable]$BuyerHeaders,
        [Parameter(Mandatory = $true)][hashtable]$MerchantHeaders,
        [string]$Reference = ""
    )

    if (-not $Reference) { $Reference = ("qa_ref_{0}" -f (Get-Random)) }

    $create = Invoke-Api -State $State -Method "POST" -Path "/api/orders" -Headers $BuyerHeaders -BodyObj @{
        merchant_id = $MerchantId
        amount = 25000
        delivery_fee = 2000
        inspection_fee = 0
        pickup = "Ikeja"
        dropoff = "Yaba"
        payment_reference = $Reference
    }
    if ($create.StatusCode -notin @(200, 201)) {
        return [pscustomobject]@{ Ok = $false; Step = "create"; Resp = $create; Reference = $Reference }
    }

    $orderId = [int]$create.Json.order.id
    $tok = (Get-AvailToken -State $State -OrderId $orderId).Trim()
    $av = Invoke-Api -State $State -Method "POST" -Path "/api/availability/confirm" -BodyObj @{ token = $tok }
    if ($av.StatusCode -notin @(200, 201)) {
        return [pscustomobject]@{ Ok = $false; Step = "availability"; Resp = $av; OrderId = $orderId; Reference = $Reference }
    }

    $ful = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/fulfillment" -f $orderId) -Headers $BuyerHeaders -BodyObj @{ mode = "delivery" }
    if ($ful.StatusCode -notin @(200, 201)) {
        return [pscustomobject]@{ Ok = $false; Step = "fulfillment"; Resp = $ful; OrderId = $orderId; Reference = $Reference }
    }

    $acc = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/merchant/accept" -f $orderId) -Headers $MerchantHeaders -BodyObj @{}
    if ($acc.StatusCode -notin @(200, 201)) {
        return [pscustomobject]@{ Ok = $false; Step = "accept"; Resp = $acc; OrderId = $orderId; Reference = $Reference }
    }

    $asg = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/driver/assign" -f $orderId) -Headers $MerchantHeaders -BodyObj @{ driver_id = $DriverId }
    if ($asg.StatusCode -notin @(200, 201)) {
        return [pscustomobject]@{ Ok = $false; Step = "assign"; Resp = $asg; OrderId = $orderId; Reference = $Reference }
    }

    return [pscustomobject]@{ Ok = $true; OrderId = $orderId; Reference = $Reference; CreateResp = $create }
}
