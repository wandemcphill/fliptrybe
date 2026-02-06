$ErrorActionPreference = 'Stop'

$base = "http://127.0.0.1:5000"

function Wait-For-Health {
  $ok = $false
  for ($i = 0; $i -lt 30; $i++) {
    try {
      $res = Invoke-JsonGet "$base/api/health"
      if ($res -and $res.ok -eq $true) { $ok = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
  }
  if (-not $ok) { throw "Health check failed. Ensure backend is running." }
}

function Log-Step {
  param(
    [string]$Name,
    [string]$Endpoint,
    [string]$Role
  )
  Write-Host ("STEP: {0} | endpoint={1} | role={2}" -f $Name, $Endpoint, $Role)
}

function New-AuthHeaders {
  param([string]$Token)
  if (-not $Token) { return $null }
  return @{ 
    "Authorization" = "Bearer $Token"
    "Content-Type"  = "application/json"
  }
}

function Invoke-JsonPost {
  param(
    [string]$Url,
    [hashtable]$Body,
    [hashtable]$Headers = $null
  )
  if (-not $Headers) { $Headers = @{ "Content-Type" = "application/json" } }
  return Invoke-RestMethod -Method Post -Uri $Url -Headers $Headers -Body ($Body | ConvertTo-Json -Depth 6)
}

function Invoke-JsonPostWithStatus {
  param(
    [string]$Url,
    [hashtable]$Body,
    [hashtable]$Headers = $null
  )
  if (-not $Headers) { $Headers = @{ "Content-Type" = "application/json" } }
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $Url -Headers $Headers -Body ($Body | ConvertTo-Json -Depth 6)
    return @{ StatusCode = 200; Body = $resp }
  } catch {
    $status = $null
    $errBody = $null
    if ($_.Exception -and $_.Exception.Response) {
      try { $status = [int]$_.Exception.Response.StatusCode } catch { $status = $null }
      try {
        $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $raw = $sr.ReadToEnd()
        if ($raw) { $errBody = $raw | ConvertFrom-Json }
      } catch { }
    }
    if (-not $status) { throw $_ }
    return @{ StatusCode = $status; Body = $errBody }
  }
}
function Invoke-JsonGetWithStatus {
  param(
    [string]$Url,
    [hashtable]$Headers = $null
  )
  if (-not $Headers) { $Headers = @{ "Content-Type" = "application/json" } }
  try {
    $resp = Invoke-RestMethod -Method Get -Uri $Url -Headers $Headers
    return @{ StatusCode = 200; Body = $resp }
  } catch {
    $status = $null
    $errBody = $null
    if ($_.Exception -and $_.Exception.Response) {
      try { $status = [int]$_.Exception.Response.StatusCode } catch { $status = $null }
      try {
        $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $raw = $sr.ReadToEnd()
        if ($raw) { $errBody = $raw | ConvertFrom-Json }
      } catch { }
    }
    if (-not $status) { throw $_ }
    return @{ StatusCode = $status; Body = $errBody }
  }
}
function Invoke-JsonGet {
  param(
    [string]$Url,
    [hashtable]$Headers = $null
  )
  if (-not $Headers) { $Headers = @{ "Content-Type" = "application/json" } }
  return Invoke-RestMethod -Method Get -Uri $Url -Headers $Headers
}

function Invoke-JsonDelete {
  param(
    [string]$Url,
    [hashtable]$Headers = $null
  )
  if (-not $Headers) { $Headers = @{ "Content-Type" = "application/json" } }
  return Invoke-RestMethod -Method Delete -Uri $Url -Headers $Headers
}

function Cleanup-Listings {
  param([hashtable]$Headers)
  try {
    $mine = Invoke-JsonGet "$base/api/merchant/listings" $Headers
    if ($mine -and $mine.items) {
      foreach ($l in $mine.items) {
        try { Invoke-JsonDelete "$base/api/listings/$($l.id)" $Headers | Out-Null } catch { }
      }
    }
  } catch { }
}

function Create-Listing {
  param(
    [hashtable]$Headers,
    [string]$Title,
    [double]$Price
  )
  return Invoke-JsonPost "$base/api/listings" @{
    title = $Title
    description = "Cap test"
    price = $Price
    state = "Lagos"
    city = "Ikeja"
    locality = "Ikeja"
  } $Headers
}

function Create-Shortlet {
  param(
    [hashtable]$Headers,
    [string]$Title,
    [double]$NightlyPrice
  )
  return Invoke-JsonPost "$base/api/shortlets" @{
    title = $Title
    description = "Cap test"
    nightly_price = $NightlyPrice
    cleaning_fee = 0
    beds = 1
    baths = 1
    guests = 2
    state = "Lagos"
    city = "Ikeja"
    locality = "Ikeja"
  } $Headers
}

function Expect-Forbidden {
  param([scriptblock]$Action, [string]$Message)
  try {
    & $Action | Out-Null
    throw "Expected 403 but request succeeded: $Message"
  } catch {
    $status = $null
    if ($_.Exception -and $_.Exception.Response) {
      try { $status = [int]$_.Exception.Response.StatusCode } catch { $status = $null }
    }
    if ($status -ne 403) { throw $_ }
  }
}

function Login-User {
  param([string]$Email, [string]$Password)
  return Invoke-JsonPost -Url "$base/api/auth/login" -Body @{ email = $Email; password = $Password }
}

function Get-RoleHeaders {
  param(
    [string]$Role,
    [hashtable]$Headers,
    [string]$Email,
    [string]$Password
  )

  if (-not $Headers) {
    Write-Host "AUTH REQUIRED: POST /api/orders requires buyer auth. 401 is expected without it."
    $login = Login-User $Email $Password
    return New-AuthHeaders $login.token
  }

  $me = Invoke-JsonGet -Url "$base/api/auth/me" -Headers $Headers

  $actual = "buyer"
  if ($me -and $me.role) {
    $actual = $me.role
  }
  elseif ($me -and $me.user -and $me.user.role) {
    $actual = $me.user.role
  }

  $actual = $actual.ToString().ToLower()

  if ($actual -ne $Role.ToLower()) {
    $login = Login-User $Email $Password
    return New-AuthHeaders $login.token
  }
  return $Headers
}

function Assert-Role {
  param(
    [string]$Role,
    [hashtable]$Headers,
    [string]$Step
  )
  if (-not $Headers) {
    Write-Host "AUTH REQUIRED: $Step requires role=$Role"
    throw "Missing auth headers"
  }
  $me = Invoke-JsonGet -Url "$base/api/auth/me" -Headers $Headers
  $actual = "buyer"
  if ($me -and $me.role) { $actual = $me.role }
  elseif ($me -and $me.user -and $me.user.role) { $actual = $me.user.role }
  $actual = $actual.ToString().ToLower()
  if ($actual -ne $Role.ToLower()) {
    Write-Host "Role mismatch at $Step. Expected=$Role Actual=$actual"
    throw "Role mismatch"
  }
}

function Get-TimelineEvents {
  param([object]$Timeline)
  $events = @()
  if ($Timeline -and $Timeline.items) { $events = $Timeline.items }
  elseif ($Timeline -and $Timeline.events) { $events = $Timeline.events }
  elseif ($Timeline -and $Timeline.value) { $events = $Timeline.value }
  return ,$events
}

function Write-RegressionDiagnostics {
  param(
    [string]$Context,
    [int]$OrderId,
    [object]$TimelineBefore,
    [object]$TimelineAfter,
    [object]$LedgerBefore,
    [object]$LedgerAfter
  )
  Write-Host ""
  Write-Host ("REGRESSION GUARD FAIL: {0}" -f $Context)
  Write-Host ("Order ID: {0}" -f $OrderId)
  $evBefore = Get-TimelineEvents $TimelineBefore
  $evAfter = Get-TimelineEvents $TimelineAfter
  Write-Host ("Timeline before: {0}" -f $evBefore.Count)
  Write-Host ("Timeline after : {0}" -f $evAfter.Count)
  if ($evAfter.Count -gt 0) {
    Write-Host "Timeline last 5 events:"
    $last = $evAfter | Select-Object -Last 5
    foreach ($e in $last) {
      $ename = ""
      $ets = ""
      if ($e.event) { $ename = $e.event }
      elseif ($e.name) { $ename = $e.name }
      if ($e.created_at) { $ets = $e.created_at }
      elseif ($e.timestamp) { $ets = $e.timestamp }
      Write-Host (" - {0} @ {1}" -f $ename, $ets)
    }
  }
  if ($LedgerBefore -or $LedgerAfter) {
    Write-Host ("MoneyBox count before: {0}" -f $(if ($LedgerBefore) { $LedgerBefore.moneybox_count } else { "N/A" }))
    Write-Host ("MoneyBox count after : {0}" -f $(if ($LedgerAfter) { $LedgerAfter.moneybox_count } else { "N/A" }))
    Write-Host ("Wallet txn count before: {0}" -f $(if ($LedgerBefore) { $LedgerBefore.wallet_txn_count } else { "N/A" }))
    Write-Host ("Wallet txn count after : {0}" -f $(if ($LedgerAfter) { $LedgerAfter.wallet_txn_count } else { "N/A" }))
    Write-Host ("MoneyBox principal before: {0}" -f $(if ($LedgerBefore) { $LedgerBefore.moneybox_principal } else { "N/A" }))
    Write-Host ("MoneyBox principal after : {0}" -f $(if ($LedgerAfter) { $LedgerAfter.moneybox_principal } else { "N/A" }))
    Write-Host ("Wallet balance before: {0}" -f $(if ($LedgerBefore) { $LedgerBefore.wallet_balance } else { "N/A" }))
    Write-Host ("Wallet balance after : {0}" -f $(if ($LedgerAfter) { $LedgerAfter.wallet_balance } else { "N/A" }))
    if ($LedgerAfter -and $LedgerAfter.moneybox_last) {
      Write-Host "MoneyBox last 5:"
      Write-Host ($LedgerAfter.moneybox_last | ConvertTo-Json -Depth 6)
    }
    if ($LedgerAfter -and $LedgerAfter.wallet_last) {
      Write-Host "Wallet last 5:"
      Write-Host ($LedgerAfter.wallet_last | ConvertTo-Json -Depth 6)
    }
  }
  Write-Host ""
}

Write-Host "Preflight: /api/health..."
Wait-For-Health

Log-Step "Admin Signup Block" "/api/auth/register" "guest"
$adminEmail = ("admin_block_{0}@fliptrybe.dev" -f [Guid]::NewGuid().ToString("N").Substring(0,8))
$adminSignup = Invoke-JsonPostWithStatus "$base/api/auth/register" @{ name="Admin Block"; email=$adminEmail; password="demo12345"; role="admin" }
if ($adminSignup.StatusCode -eq 200 -or $adminSignup.StatusCode -eq 201) {
  throw "Admin signup unexpectedly allowed"
}
if ($adminSignup.StatusCode -ne 400 -and $adminSignup.StatusCode -ne 403) {
  throw ("Admin signup unexpected status: {0}" -f $adminSignup.StatusCode)
}

Log-Step "Seed Demo" "/api/demo/seed" "guest"
$seed = Invoke-JsonPost -Url "$base/api/demo/seed" -Body @{}
$seededOrderId = $null
if ($seed -and $seed.seeded_order_id) { $seededOrderId = [int]$seed.seeded_order_id }

Write-Host "Logging in demo users..."
$buyer     = Login-User "buyer@fliptrybe.com"     "demo12345"
$merchant  = Login-User "merchant@fliptrybe.com"  "demo12345"
$driver    = Login-User "driver@fliptrybe.com"    "demo12345"
$inspector = Login-User "inspector@fliptrybe.com" "demo12345"
$admin     = Login-User "admin@fliptrybe.com"     "demo12345"

$buyerHeaders     = New-AuthHeaders $buyer.token
$merchantHeaders  = New-AuthHeaders $merchant.token
$driverHeaders    = New-AuthHeaders $driver.token
$inspectorHeaders = New-AuthHeaders $inspector.token
$adminHeaders     = New-AuthHeaders $admin.token

Log-Step "Seed Idempotency Check" "/api/demo/seed" "guest"
$seedTimelineLen1 = $null
$seedTimeline1 = $null
if ($seededOrderId) {
  $seedTimeline1 = Invoke-JsonGet "$base/api/orders/$seededOrderId/timeline" $buyerHeaders
  $seedEvents1 = Get-TimelineEvents $seedTimeline1
  $seedTimelineLen1 = $seedEvents1.Count
  if ($seedTimelineLen1 -lt 1) {
    $raw = $seedTimeline1 | ConvertTo-Json -Depth 6
    throw ("Seeded order timeline empty before reseed. order_id={0} response={1}" -f $seededOrderId, $raw)
  }
}
$ledgerSummary1 = $null
$ledgerSummary1Resp = Invoke-JsonGetWithStatus "$base/api/demo/ledger_summary?user=merchant@fliptrybe.com"
if ($ledgerSummary1Resp.StatusCode -eq 200) {
  $ledgerSummary1 = $ledgerSummary1Resp.Body
} else {
  Write-Host ("Ledger summary gated or unavailable (status={0}); skipping reseed ledger checks." -f $ledgerSummary1Resp.StatusCode)
}
$seed2 = Invoke-JsonPost -Url "$base/api/demo/seed" -Body @{}
$seededOrderId2 = $seededOrderId
if ($seed2 -and $seed2.seeded_order_id) { $seededOrderId2 = [int]$seed2.seeded_order_id }
$seedTimeline2 = $null
if ($seededOrderId2) {
  $seedTimeline2 = Invoke-JsonGet "$base/api/orders/$seededOrderId2/timeline" $buyerHeaders
  $seedEvents2 = Get-TimelineEvents $seedTimeline2
  $seedTimelineLen2 = $seedEvents2.Count
  if ($seedTimelineLen1 -ne $null -and $seedTimelineLen2 -ne $seedTimelineLen1) {
    Write-RegressionDiagnostics -Context "reseed timeline length changed" -OrderId $seededOrderId2 -TimelineBefore $seedTimeline1 -TimelineAfter $seedTimeline2 -LedgerBefore $ledgerSummary1 -LedgerAfter $null
    throw ("Seeded timeline length changed after reseed. before={0} after={1}" -f $seedTimelineLen1, $seedTimelineLen2)
  }
}
$ledgerSummary2 = $null
$ledgerSummary2Resp = Invoke-JsonGetWithStatus "$base/api/demo/ledger_summary?user=merchant@fliptrybe.com"
if ($ledgerSummary2Resp.StatusCode -eq 200) {
  $ledgerSummary2 = $ledgerSummary2Resp.Body
} else {
  Write-Host ("Ledger summary gated or unavailable after reseed (status={0}); skipping reseed ledger checks." -f $ledgerSummary2Resp.StatusCode)
}
if ($ledgerSummary1 -and $ledgerSummary2) {
  if ($ledgerSummary1.moneybox_count -ne $ledgerSummary2.moneybox_count) {
    Write-RegressionDiagnostics -Context "reseed moneybox_count changed" -OrderId $seededOrderId2 -TimelineBefore $seedTimeline1 -TimelineAfter $seedTimeline2 -LedgerBefore $ledgerSummary1 -LedgerAfter $ledgerSummary2
    throw ("MoneyBox ledger count changed after reseed. before={0} after={1}" -f $ledgerSummary1.moneybox_count, $ledgerSummary2.moneybox_count)
  }
  if ($ledgerSummary1.wallet_txn_count -ne $ledgerSummary2.wallet_txn_count) {
    Write-RegressionDiagnostics -Context "reseed wallet_txn_count changed" -OrderId $seededOrderId2 -TimelineBefore $seedTimeline1 -TimelineAfter $seedTimeline2 -LedgerBefore $ledgerSummary1 -LedgerAfter $ledgerSummary2
    throw ("Wallet ledger count changed after reseed. before={0} after={1}" -f $ledgerSummary1.wallet_txn_count, $ledgerSummary2.wallet_txn_count)
  }
  if ([math]::Abs([double]$ledgerSummary1.moneybox_principal - [double]$ledgerSummary2.moneybox_principal) -gt 0.01) {
    Write-RegressionDiagnostics -Context "reseed moneybox_principal changed" -OrderId $seededOrderId2 -TimelineBefore $seedTimeline1 -TimelineAfter $seedTimeline2 -LedgerBefore $ledgerSummary1 -LedgerAfter $ledgerSummary2
    throw ("MoneyBox principal changed after reseed. before={0} after={1}" -f $ledgerSummary1.moneybox_principal, $ledgerSummary2.moneybox_principal)
  }
  if ([math]::Abs([double]$ledgerSummary1.wallet_balance - [double]$ledgerSummary2.wallet_balance) -gt 0.01) {
    Write-RegressionDiagnostics -Context "reseed wallet_balance changed" -OrderId $seededOrderId2 -TimelineBefore $seedTimeline1 -TimelineAfter $seedTimeline2 -LedgerBefore $ledgerSummary1 -LedgerAfter $ledgerSummary2
    throw ("Wallet balance changed after reseed. before={0} after={1}" -f $ledgerSummary1.wallet_balance, $ledgerSummary2.wallet_balance)
  }
  if ($ledgerSummary1.demo_user_count -ne $ledgerSummary2.demo_user_count) {
    Write-RegressionDiagnostics -Context "reseed demo_user_count changed" -OrderId $seededOrderId2 -TimelineBefore $seedTimeline1 -TimelineAfter $seedTimeline2 -LedgerBefore $ledgerSummary1 -LedgerAfter $ledgerSummary2
    throw ("Demo user count changed after reseed. before={0} after={1}" -f $ledgerSummary1.demo_user_count, $ledgerSummary2.demo_user_count)
  }
  if ($ledgerSummary1.demo_listing_count -ne $ledgerSummary2.demo_listing_count) {
    Write-RegressionDiagnostics -Context "reseed demo_listing_count changed" -OrderId $seededOrderId2 -TimelineBefore $seedTimeline1 -TimelineAfter $seedTimeline2 -LedgerBefore $ledgerSummary1 -LedgerAfter $ledgerSummary2
    throw ("Demo listing count changed after reseed. before={0} after={1}" -f $ledgerSummary1.demo_listing_count, $ledgerSummary2.demo_listing_count)
  }
  if ($ledgerSummary1.demo_order_count -ne $ledgerSummary2.demo_order_count) {
    Write-RegressionDiagnostics -Context "reseed demo_order_count changed" -OrderId $seededOrderId2 -TimelineBefore $seedTimeline1 -TimelineAfter $seedTimeline2 -LedgerBefore $ledgerSummary1 -LedgerAfter $ledgerSummary2
    throw ("Demo order count changed after reseed. before={0} after={1}" -f $ledgerSummary1.demo_order_count, $ledgerSummary2.demo_order_count)
  }
}

Write-Host "Concurrency seed probe..."
$probeOrderId = $seededOrderId2
if (-not $probeOrderId) { $probeOrderId = $seededOrderId }
$probeTimelineLenBefore = $null
$probeTimelineBefore = $null
if ($probeOrderId) {
  $probeTimelineBefore = Invoke-JsonGet "$base/api/orders/$probeOrderId/timeline" $buyerHeaders
  $probeEventsBefore = Get-TimelineEvents $probeTimelineBefore
  $probeTimelineLenBefore = $probeEventsBefore.Count
}
$probeSummaryBefore = $ledgerSummary2
if (-not $probeSummaryBefore) { $probeSummaryBefore = $ledgerSummary1 }
$job1 = Start-Job -ScriptBlock { param($u) Invoke-RestMethod -Method Post -Uri $u -Body '{}' -ContentType 'application/json' | Out-Null } -ArgumentList "$base/api/demo/seed"
$job2 = Start-Job -ScriptBlock { param($u) Invoke-RestMethod -Method Post -Uri $u -Body '{}' -ContentType 'application/json' | Out-Null } -ArgumentList "$base/api/demo/seed"
Wait-Job -Job $job1, $job2 | Out-Null
Receive-Job -Job $job1, $job2 | Out-Null
Remove-Job -Job $job1, $job2 | Out-Null
if ($probeOrderId) {
  $probeTimelineAfter = Invoke-JsonGet "$base/api/orders/$probeOrderId/timeline" $buyerHeaders
  $probeEventsAfter = Get-TimelineEvents $probeTimelineAfter
  $probeTimelineLenAfter = $probeEventsAfter.Count
  if ($probeTimelineLenBefore -ne $null -and $probeTimelineLenAfter -ne $probeTimelineLenBefore) {
    Write-RegressionDiagnostics -Context "concurrency timeline length changed" -OrderId $probeOrderId -TimelineBefore $probeTimelineBefore -TimelineAfter $probeTimelineAfter -LedgerBefore $probeSummaryBefore -LedgerAfter $null
    throw ("Concurrency seed changed timeline length. before={0} after={1}" -f $probeTimelineLenBefore, $probeTimelineLenAfter)
  }
}
$probeSummaryAfterResp = Invoke-JsonGetWithStatus "$base/api/demo/ledger_summary?user=merchant@fliptrybe.com"
if ($probeSummaryBefore -and $probeSummaryAfterResp.StatusCode -eq 200) {
  $probeSummaryAfter = $probeSummaryAfterResp.Body
  if ($probeSummaryBefore.moneybox_count -ne $probeSummaryAfter.moneybox_count) {
    Write-RegressionDiagnostics -Context "concurrency moneybox_count changed" -OrderId $probeOrderId -TimelineBefore $probeTimelineBefore -TimelineAfter $probeTimelineAfter -LedgerBefore $probeSummaryBefore -LedgerAfter $probeSummaryAfter
    throw ("Concurrency seed changed moneybox_count. before={0} after={1}" -f $probeSummaryBefore.moneybox_count, $probeSummaryAfter.moneybox_count)
  }
  if ($probeSummaryBefore.wallet_txn_count -ne $probeSummaryAfter.wallet_txn_count) {
    Write-RegressionDiagnostics -Context "concurrency wallet_txn_count changed" -OrderId $probeOrderId -TimelineBefore $probeTimelineBefore -TimelineAfter $probeTimelineAfter -LedgerBefore $probeSummaryBefore -LedgerAfter $probeSummaryAfter
    throw ("Concurrency seed changed wallet_txn_count. before={0} after={1}" -f $probeSummaryBefore.wallet_txn_count, $probeSummaryAfter.wallet_txn_count)
  }
  if ([math]::Abs([double]$probeSummaryBefore.moneybox_principal - [double]$probeSummaryAfter.moneybox_principal) -gt 0.01) {
    Write-RegressionDiagnostics -Context "concurrency moneybox_principal changed" -OrderId $probeOrderId -TimelineBefore $probeTimelineBefore -TimelineAfter $probeTimelineAfter -LedgerBefore $probeSummaryBefore -LedgerAfter $probeSummaryAfter
    throw ("Concurrency seed changed moneybox_principal. before={0} after={1}" -f $probeSummaryBefore.moneybox_principal, $probeSummaryAfter.moneybox_principal)
  }
  if ([math]::Abs([double]$probeSummaryBefore.wallet_balance - [double]$probeSummaryAfter.wallet_balance) -gt 0.01) {
    Write-RegressionDiagnostics -Context "concurrency wallet_balance changed" -OrderId $probeOrderId -TimelineBefore $probeTimelineBefore -TimelineAfter $probeTimelineAfter -LedgerBefore $probeSummaryBefore -LedgerAfter $probeSummaryAfter
    throw ("Concurrency seed changed wallet_balance. before={0} after={1}" -f $probeSummaryBefore.wallet_balance, $probeSummaryAfter.wallet_balance)
  }
  if ($probeSummaryBefore.demo_user_count -ne $probeSummaryAfter.demo_user_count) {
    Write-RegressionDiagnostics -Context "concurrency demo_user_count changed" -OrderId $probeOrderId -TimelineBefore $probeTimelineBefore -TimelineAfter $probeTimelineAfter -LedgerBefore $probeSummaryBefore -LedgerAfter $probeSummaryAfter
    throw ("Concurrency seed changed demo_user_count. before={0} after={1}" -f $probeSummaryBefore.demo_user_count, $probeSummaryAfter.demo_user_count)
  }
  if ($probeSummaryBefore.demo_listing_count -ne $probeSummaryAfter.demo_listing_count) {
    Write-RegressionDiagnostics -Context "concurrency demo_listing_count changed" -OrderId $probeOrderId -TimelineBefore $probeTimelineBefore -TimelineAfter $probeTimelineAfter -LedgerBefore $probeSummaryBefore -LedgerAfter $probeSummaryAfter
    throw ("Concurrency seed changed demo_listing_count. before={0} after={1}" -f $probeSummaryBefore.demo_listing_count, $probeSummaryAfter.demo_listing_count)
  }
  if ($probeSummaryBefore.demo_order_count -ne $probeSummaryAfter.demo_order_count) {
    Write-RegressionDiagnostics -Context "concurrency demo_order_count changed" -OrderId $probeOrderId -TimelineBefore $probeTimelineBefore -TimelineAfter $probeTimelineAfter -LedgerBefore $probeSummaryBefore -LedgerAfter $probeSummaryAfter
    throw ("Concurrency seed changed demo_order_count. before={0} after={1}" -f $probeSummaryBefore.demo_order_count, $probeSummaryAfter.demo_order_count)
  }
} elseif ($probeSummaryAfterResp.StatusCode -ne 200) {
  Write-Host ("Ledger summary gated or unavailable for concurrency probe (status={0}); skipping ledger checks." -f $probeSummaryAfterResp.StatusCode)
}

Log-Step "Inspector Bond Topup" "/api/admin/inspectors/<id>/bond/topup" "admin"
try {
  $bondInfo = Invoke-JsonGet "$base/api/admin/inspectors/$($inspector.user.id)/bond" $adminHeaders
  if ($bondInfo -and $bondInfo.bond) {
    $required = [double]$bondInfo.bond.bond_required_amount
    $available = [double]$bondInfo.bond.bond_available_amount
    if ($required -gt $available) {
      $need = [math]::Round(($required - $available), 2)
      Invoke-JsonPost "$base/api/admin/inspectors/$($inspector.user.id)/bond/topup" @{ amount = $need; note = "Smoke test topup" } $adminHeaders | Out-Null
    }
  }
} catch { }

Log-Step "Role Change Request" "/api/role-requests" "buyer->merchant"
$newEmail = ("rolechange_{0}@fliptrybe.local" -f [Guid]::NewGuid().ToString("N").Substring(0,8))
$newReg = Invoke-JsonPost "$base/api/auth/register" @{ name = "RoleChange Tester"; email = $newEmail; password = "demo12345" }
$newHeaders = New-AuthHeaders $newReg.token
Invoke-JsonPost "$base/api/role-requests" @{ requested_role = "merchant"; reason = "upgrade" } $newHeaders | Out-Null
$requests = Invoke-JsonGet "$base/api/admin/role-requests?status=PENDING" $adminHeaders
$reqId = $null
if ($requests -and $requests.items) {
  foreach ($r in $requests.items) {
    if ($r.user_id -eq $newReg.user.id) { $reqId = $r.id }
  }
}
if (-not $reqId) { throw "Role change request not found" }
Invoke-JsonPost "$base/api/admin/role-requests/$reqId/approve" @{} $adminHeaders | Out-Null
$newMe = Invoke-JsonGet "$base/api/auth/me" $newHeaders
if ($newMe.role -ne "merchant") { throw "Role change not applied" }
$myReq = Invoke-JsonGet "$base/api/role-requests/me" $newHeaders
if (-not $myReq -or -not $myReq.request -or $myReq.request.status -ne "APPROVED") { throw "Role request status endpoint failed" }

Log-Step "Listing Caps (Buyer/Driver/Inspector)" "/api/listings" "role limits"
Cleanup-Listings $buyerHeaders
Cleanup-Listings $driverHeaders
Cleanup-Listings $inspectorHeaders

$buyerListings = @()
for ($i=1; $i -le 10; $i++) {
  $res = Create-Listing $buyerHeaders ("Buyer Cap " + $i) 1000
  $buyerListings += $res.listing.id
}
Expect-Forbidden { Create-Listing $buyerHeaders "Buyer Cap 11" 1000 } "buyer listing limit"
foreach ($id in $buyerListings) { Invoke-JsonDelete "$base/api/listings/$id" $buyerHeaders | Out-Null }

$driverListings = @()
for ($i=1; $i -le 20; $i++) {
  $res = Create-Listing $driverHeaders ("Driver Cap " + $i) 1000
  if ($i -eq 1) {
    if ([math]::Abs([double]$res.listing.final_price - ([double]$res.listing.base_price + [double]$res.listing.platform_fee)) -gt 0.01) {
      throw "Driver selling did not apply add-on pricing"
    }
  }
  $driverListings += $res.listing.id
}
Expect-Forbidden { Create-Listing $driverHeaders "Driver Cap 21" 1000 } "driver listing limit"
foreach ($id in $driverListings) { Invoke-JsonDelete "$base/api/listings/$id" $driverHeaders | Out-Null }

$inspectorListings = @()
for ($i=1; $i -le 20; $i++) {
  $res = Create-Listing $inspectorHeaders ("Inspector Cap " + $i) 1000
  if ($i -eq 1) {
    if ([math]::Abs([double]$res.listing.final_price - ([double]$res.listing.base_price + [double]$res.listing.platform_fee)) -gt 0.01) {
      throw "Inspector selling did not apply add-on pricing"
    }
  }
  $inspectorListings += $res.listing.id
}
Expect-Forbidden { Create-Listing $inspectorHeaders "Inspector Cap 21" 1000 } "inspector listing limit"
foreach ($id in $inspectorListings) { Invoke-JsonDelete "$base/api/listings/$id" $inspectorHeaders | Out-Null }

$merchantListings = @()
for ($i=1; $i -le 12; $i++) {
  $res = Create-Listing $merchantHeaders ("Merchant Cap " + $i) 1000
  $merchantListings += $res.listing.id
}
foreach ($id in $merchantListings) { Invoke-JsonDelete "$base/api/listings/$id" $merchantHeaders | Out-Null }

Log-Step "Shortlet Caps (Buyer)" "/api/shortlets" "role limits"
$shortletEmail = ("shortletcap_{0}@fliptrybe.local" -f [Guid]::NewGuid().ToString("N").Substring(0,8))
$shortletReg = Invoke-JsonPost "$base/api/auth/register" @{ name = "Shortlet Cap Tester"; email = $shortletEmail; password = "demo12345" }
$shortletHeaders = New-AuthHeaders $shortletReg.token
for ($i=1; $i -le 10; $i++) {
  Create-Shortlet $shortletHeaders ("Shortlet Cap " + $i) 1000 | Out-Null
}
Expect-Forbidden { Create-Shortlet $shortletHeaders "Shortlet Cap 11" 1000 } "shortlet listing limit"

Log-Step "MoneyBox Open" "/api/moneybox/open" "merchant"
$merchantHeaders = Get-RoleHeaders "merchant" $merchantHeaders "merchant@fliptrybe.com" "demo12345"
Assert-Role "merchant" $merchantHeaders "MoneyBox Open"
$mbOpen = Invoke-JsonPostWithStatus "$base/api/moneybox/open" @{ tier = 1; lock_days = 10 } $merchantHeaders
if ($mbOpen.StatusCode -eq 200) {
  Write-Host "MoneyBox opened."
} elseif ($mbOpen.StatusCode -eq 409) {
  Write-Host "MoneyBox already open; continuing."
} else {
  throw ("MoneyBox open failed with status {0}" -f $mbOpen.StatusCode)
}
$mbAuto = Invoke-JsonPostWithStatus "$base/api/moneybox/autosave" @{ enabled = $true; percent = 10 } $merchantHeaders
if ($mbAuto.StatusCode -eq 200) {
  Write-Host "MoneyBox autosave updated."
} elseif ($mbAuto.StatusCode -eq 409) {
  Write-Host "MoneyBox autosave already set; continuing."
} else {
  throw ("MoneyBox autosave failed with status {0}" -f $mbAuto.StatusCode)
}
$mbBeforeRes = Invoke-JsonGet "$base/api/moneybox/me" $merchantHeaders
$mbBefore = 0.0
if ($mbBeforeRes -and $mbBeforeRes.account -and $mbBeforeRes.account.principal_balance -ne $null) {
  $mbBefore = [double]$mbBeforeRes.account.principal_balance
}
$merchantLedgerBefore = Invoke-JsonGet "$base/api/wallet/ledger" $merchantHeaders
$ledgerBeforeMaxId = 0
foreach ($t in $merchantLedgerBefore) {
  if ($t.id -gt $ledgerBeforeMaxId) { $ledgerBeforeMaxId = $t.id }
}

Log-Step "Fetch Feed" "/api/feed?state=Lagos&radius_km=10" "guest"
$feed = Invoke-JsonGet "$base/api/feed?state=Lagos&radius_km=10"
if (-not $feed.items -or $feed.items.Count -lt 1) { throw "No listings found" }

$listing    = $feed.items[0]
$listingId  = $listing.id
$merchantId = $listing.owner_id

Log-Step "Validate Listing Pricing" "/api/feed?state=Lagos&radius_km=10" "guest"
$basePrice = [double]$listing.base_price
$platformFee = [double]$listing.platform_fee
$finalPrice = [double]$listing.final_price
$calcFinal = [math]::Round(($basePrice + $platformFee), 2)
if ($basePrice -le 0) { throw "Listing base_price missing or invalid" }
if ([math]::Abs($calcFinal - $finalPrice) -gt 0.01) { throw "final_price mismatch: expected $calcFinal, got $finalPrice" }
if ([math]::Abs($finalPrice - [double]$listing.price) -gt 0.01) { throw "price mismatch: expected $finalPrice, got $($listing.price)" }

Log-Step "Create Merchant Listing" "/api/listings" "merchant"
$merchantHeaders = Get-RoleHeaders "merchant" $merchantHeaders "merchant@fliptrybe.com" "demo12345"
Assert-Role "merchant" $merchantHeaders "Create Listing"
$newTitle = ("Smoke Listing {0}" -f [Guid]::NewGuid().ToString("N").Substring(0,8))
$created = Create-Listing $merchantHeaders $newTitle 6500
if (-not $created -or -not $created.listing) { throw "Failed to create merchant listing for order flow" }
$orderListing = $created.listing
$listingId = $orderListing.id
$merchantId = $orderListing.owner_id
$basePrice = [double]$orderListing.base_price
$platformFee = [double]$orderListing.platform_fee
$finalPrice = [double]$orderListing.final_price
if ($basePrice -le 0) { throw "Order listing base_price missing or invalid" }

Log-Step "Price Preview" "/api/listings/price-preview" "guest"
$preview = Invoke-JsonPost "$base/api/listings/price-preview" @{ base_price = 1000; listing_type = "declutter"; seller_role = "merchant" }
if (-not $preview.ok) { throw "Price preview failed" }
if ([math]::Abs([double]$preview.final_price - 1030) -gt 0.01) { throw "Price preview final mismatch" }

Log-Step "Create Order" "/api/orders" "buyer"
$buyerHeaders = Get-RoleHeaders "buyer" $buyerHeaders "buyer@fliptrybe.com" "demo12345"
Assert-Role "buyer" $buyerHeaders "Create Order"
$order = Invoke-JsonPost "$base/api/orders" @{
  buyer_id = $buyer.user.id
  merchant_id = $merchantId
  listing_id = $listingId
  amount = $finalPrice
  delivery_fee = 1500
  inspection_required = $true
} $buyerHeaders

$orderId = $order.order.id

Log-Step "Mark Paid" "/api/orders/<id>/mark-paid" "buyer"
$buyerHeaders = Get-RoleHeaders "buyer" $buyerHeaders "buyer@fliptrybe.com" "demo12345"
Assert-Role "buyer" $buyerHeaders "Mark Paid"
Invoke-JsonPost "$base/api/orders/$orderId/mark-paid" @{
  reference = "demo-$([Guid]::NewGuid().ToString('N').Substring(0,12))"
} $buyerHeaders | Out-Null

Log-Step "Request Inspection" "/api/orders/<id>/inspection/request" "buyer"
$buyerHeaders = Get-RoleHeaders "buyer" $buyerHeaders "buyer@fliptrybe.com" "demo12345"
Assert-Role "buyer" $buyerHeaders "Inspection Request"
Invoke-JsonPost "$base/api/orders/$orderId/inspection/request" @{} $buyerHeaders | Out-Null

Log-Step "Inspector Flow" "/api/inspections/<id>/*" "inspector"
$inspectorHeaders = Get-RoleHeaders "inspector" $inspectorHeaders "inspector@fliptrybe.com" "demo12345"
Assert-Role "inspector" $inspectorHeaders "Inspector Flow"
Invoke-JsonPost "$base/api/inspections/$orderId/status" @{ status="ON_MY_WAY" } $inspectorHeaders | Out-Null
Invoke-JsonPost "$base/api/inspections/$orderId/status" @{ status="ARRIVED" }   $inspectorHeaders | Out-Null
Invoke-JsonPost "$base/api/inspections/$orderId/status" @{ status="INSPECTED" } $inspectorHeaders | Out-Null
Invoke-JsonPost "$base/api/inspections/$orderId/outcome" @{ outcome="PASS" }    $inspectorHeaders | Out-Null

Log-Step "Escrow Runner" "/api/admin/escrow/run" "admin"
$adminHeaders = Get-RoleHeaders "admin" $adminHeaders "admin@fliptrybe.com" "demo12345"
Assert-Role "admin" $adminHeaders "Escrow Automation"
Invoke-JsonPost "$base/api/admin/escrow/run" @{ limit=50 } $adminHeaders | Out-Null

Log-Step "Verify Pricing Ledger" "/api/wallet/ledger" "merchant/admin"
$merchantProfile = Invoke-JsonGet "$base/api/merchants/$merchantId"
$isTopTier = $false
if ($merchantProfile -and $merchantProfile.merchant -and $merchantProfile.merchant.is_top_tier) {
  $isTopTier = [bool]$merchantProfile.merchant.is_top_tier
}
$expectedIncentive = 0.0
$expectedPlatformShare = $platformFee
if ($isTopTier) {
  $expectedIncentive = [math]::Round(($platformFee * 11.0 / 13.0), 2)
  $expectedPlatformShare = [math]::Round(($platformFee - $expectedIncentive), 2)
}
$autosavePercent = 10.0
$expectedAutosave = 0.0
if ($expectedIncentive -gt 0) {
  $expectedAutosave = [math]::Round(($expectedIncentive * $autosavePercent / 100.0), 2)
}

$merchantLedger = Invoke-JsonGet "$base/api/wallet/ledger" $merchantHeaders
$merchantSale = $null
$merchantIncentive = $null
foreach ($txn in $merchantLedger) {
  if ($txn.reference -eq "order:$orderId" -and $txn.kind -eq "order_sale" -and $txn.direction -eq "credit") {
    $merchantSale = [double]$txn.amount
  }
  if ($txn.reference -eq "order:$orderId" -and $txn.kind -eq "top_tier_incentive") {
    $merchantIncentive = [double]$txn.amount
  }
}
if ($merchantSale -eq $null) { throw "Missing merchant order_sale ledger entry" }
if ([math]::Abs($merchantSale - $basePrice) -gt 0.01) { throw "Merchant payout mismatch: expected $basePrice, got $merchantSale" }
if ($isTopTier) {
  if ($merchantIncentive -eq $null) { throw "Missing top-tier incentive ledger entry" }
  $expectedIncentiveNet = [math]::Round(($expectedIncentive - $expectedAutosave), 2)
  if ([math]::Abs($merchantIncentive - $expectedIncentiveNet) -gt 0.01) { throw "Top-tier incentive net mismatch: expected $expectedIncentiveNet, got $merchantIncentive" }
} else {
  if ($merchantIncentive) { throw "Unexpected top-tier incentive for non-top-tier merchant" }
}

$adminLedger = Invoke-JsonGet "$base/api/wallet/ledger" $adminHeaders
$platformFeeEntry = $null
foreach ($txn in $adminLedger) {
  if ($txn.reference -eq "order:$orderId" -and $txn.kind -eq "platform_fee") {
    $platformFeeEntry = [double]$txn.amount
  }
}
if ($expectedPlatformShare -gt 0 -and $platformFeeEntry -eq $null) { throw "Missing platform fee ledger entry" }
if ($expectedPlatformShare -gt 0 -and [math]::Abs($platformFeeEntry - $expectedPlatformShare) -gt 0.01) {
  throw "Platform fee mismatch: expected $expectedPlatformShare, got $platformFeeEntry"
}

Log-Step "MoneyBox Autosave Verify" "/api/moneybox/me" "merchant"
$eligibleKinds = @("top_tier_incentive","delivery_fee","inspection_fee","commission_credit")
$eligibleCredits = @()
foreach ($txn in $merchantLedger) {
  if ($txn.id -gt $ledgerBeforeMaxId -and $txn.reference -eq "order:$orderId" -and $eligibleKinds -contains $txn.kind) {
    $eligibleCredits += $txn
  }
}
$moneybox = Invoke-JsonGet "$base/api/moneybox/me" $merchantHeaders
$mbAfter = 0.0
if ($moneybox -and $moneybox.account -and $moneybox.account.principal_balance -ne $null) {
  $mbAfter = [double]$moneybox.account.principal_balance
}
$mbDelta = [math]::Round(($mbAfter - $mbBefore), 2)

if ($eligibleCredits.Count -lt 1) {
  $ref = "order:$orderId"
  $mbAutoCount = 0
  try {
    $mbAutoCount = [int](python -c "import sqlite3; c=sqlite3.connect('backend/instance/fliptrybe.db'); cur=c.cursor(); print(cur.execute(\"select count(*) from moneybox_ledger where entry_type='AUTOSAVE' and reference='$ref'\").fetchone()[0])")
  } catch { $mbAutoCount = 0 }
  if ($mbAutoCount -ge 1) {
    Write-Host "MoneyBox autosave already applied for this reference; continuing."
  } else {
    throw "No eligible commission credits found for autosave test (expected top_tier_incentive or commission credit)."
  }
} else {
  $autosavePercent = 10.0
  $expectedAutosave = 0.0
  foreach ($txn in $eligibleCredits) {
    $net = [double]$txn.amount
    $sweep = [math]::Round(($net * $autosavePercent / (100.0 - $autosavePercent)), 2)
    if ($sweep -lt 0) { $sweep = 0.0 }
    $expectedAutosave += $sweep
  }
  if ([math]::Abs($mbDelta - $expectedAutosave) -gt 0.05) {
    throw "MoneyBox autosave mismatch: expected delta $expectedAutosave, got $mbDelta"
  }
  Write-Host ("MoneyBox autosave verified. delta={0} expected={1}" -f $mbDelta, $expectedAutosave)
}

Write-Host "SQLite verification (moneybox + wallet ledgers)..."
python -c "import sqlite3; c=sqlite3.connect('backend/instance/fliptrybe.db'); cur=c.cursor(); print('moneybox_accounts:', cur.execute('select count(*) from moneybox_accounts').fetchone()[0]); print('moneybox_ledger:', cur.execute('select count(*) from moneybox_ledger').fetchone()[0]); print('latest moneybox_ledger:', cur.execute('select id, account_id, amount, entry_type, created_at from moneybox_ledger order by id desc limit 5').fetchall()); print('latest wallet_txns:', cur.execute('select id, user_id, amount, kind, created_at, reference from wallet_txns order by id desc limit 5').fetchall())" | Out-Host

if ($expectedAutosave -gt 0) {
  Log-Step "MoneyBox Early Withdraw" "/api/moneybox/withdraw" "merchant"
  $withdrawMb = Invoke-JsonPost "$base/api/moneybox/withdraw" @{} $merchantHeaders
  $penaltyRate = [double]$withdrawMb.penalty_rate
  $penaltyAmount = [double]$withdrawMb.penalty_amount
  $expectedPenalty = [math]::Round(($expectedAutosave * 0.07), 2)
  if ([math]::Abs($penaltyRate - 0.07) -gt 0.001) { throw "MoneyBox penalty rate mismatch: expected 0.07, got $penaltyRate" }
  if ([math]::Abs($penaltyAmount - $expectedPenalty) -gt 0.02) { throw "MoneyBox penalty amount mismatch: expected $expectedPenalty, got $penaltyAmount" }
}

Log-Step "Merchant Accept" "/api/orders/<id>/merchant/accept" "merchant"
$merchantHeaders = Get-RoleHeaders "merchant" $merchantHeaders "merchant@fliptrybe.com" "demo12345"
Assert-Role "merchant" $merchantHeaders "Merchant Accept"
Invoke-JsonPost "$base/api/orders/$orderId/merchant/accept" @{} $merchantHeaders | Out-Null

Log-Step "Driver Accept" "/api/driver/jobs/<id>/accept" "driver"
$driverHeaders = Get-RoleHeaders "driver" $driverHeaders "driver@fliptrybe.com" "demo12345"
Assert-Role "driver" $driverHeaders "Driver Accept"
Invoke-JsonPost "$base/api/driver/jobs/$orderId/accept" @{} $driverHeaders | Out-Null
Invoke-JsonPost "$base/api/orders/$orderId/driver/status" @{ status="picked_up" } $driverHeaders | Out-Null
Invoke-JsonPost "$base/api/orders/$orderId/driver/status" @{ status="delivered" } $driverHeaders | Out-Null

Log-Step "Driver Verify" "/api/driver/jobs/<id>" "driver"
$driverHeaders = Get-RoleHeaders "driver" $driverHeaders "driver@fliptrybe.com" "demo12345"
Assert-Role "driver" $driverHeaders "Driver Verify"
Invoke-JsonGet "$base/api/driver/jobs/$orderId" $driverHeaders | Out-Null

Log-Step "Final Verify" "/api/orders/<id>" "buyer"
$buyerHeaders = Get-RoleHeaders "buyer" $buyerHeaders "buyer@fliptrybe.com" "demo12345"
Assert-Role "buyer" $buyerHeaders "Final Verify"
$orderFinal = Invoke-JsonGet "$base/api/orders/$orderId" $buyerHeaders
$timeline   = Invoke-JsonGet "$base/api/orders/$orderId/timeline" $buyerHeaders

Log-Step "Timeline Verify" "/api/orders/<id>/timeline" "buyer"
$events = @()
if ($timeline -and $timeline.items) { $events = $timeline.items }
elseif ($timeline -and $timeline.events) { $events = $timeline.events }
elseif ($timeline -and $timeline.value) { $events = $timeline.value }
if ($events.Count -lt 1) { throw "Timeline has no events for order $orderId" }
Write-Host "Timeline last 5 events:"
$last = $events | Select-Object -Last 5
foreach ($e in $last) {
  $ename = ""
  $ets = ""
  if ($e.event) { $ename = $e.event }
  elseif ($e.name) { $ename = $e.name }
  if ($e.created_at) { $ets = $e.created_at }
  elseif ($e.timestamp) { $ets = $e.timestamp }
  Write-Host (" - {0} @ {1}" -f $ename, $ets)
}

if ($seededOrderId) {
  Log-Step "Seeded Timeline Verify" "/api/orders/<id>/timeline" "buyer"
  $seedTimeline = Invoke-JsonGet "$base/api/orders/$seededOrderId/timeline" $buyerHeaders
  $seedEvents = @()
  if ($seedTimeline -and $seedTimeline.items) { $seedEvents = $seedTimeline.items }
  elseif ($seedTimeline -and $seedTimeline.events) { $seedEvents = $seedTimeline.events }
  elseif ($seedTimeline -and $seedTimeline.value) { $seedEvents = $seedTimeline.value }
  if ($seedEvents.Count -lt 1) { throw "Seeded order timeline has no events for order $seededOrderId" }
}

Log-Step "Merchant Withdrawal" "/api/wallet/*" "merchant"
$merchantHeaders = Get-RoleHeaders "merchant" $merchantHeaders "merchant@fliptrybe.com" "demo12345"
Assert-Role "merchant" $merchantHeaders "Merchant Withdrawal"

Invoke-JsonPost "$base/api/wallet/topup-demo" @{ amount = 100000 } $merchantHeaders | Out-Null
$walletBefore = Invoke-JsonGet "$base/api/wallet" $merchantHeaders
$balanceBefore = [double]$walletBefore.wallet.balance
$withdrawAmount = 5000

$payoutReq = Invoke-JsonPost "$base/api/wallet/payouts" @{
  amount = $withdrawAmount
  bank_name = "Demo Bank"
  account_number = "0001112223"
  account_name = "Demo Merchant"
} $merchantHeaders

$payoutId = $payoutReq.payout.id
if (-not $payoutId) { throw "Payout request failed" }
$merchantFee = 0.0
if ($payoutReq -and $payoutReq.payout -and $payoutReq.payout.fee_amount) {
  $merchantFee = [double]$payoutReq.payout.fee_amount
}
if ($merchantFee -gt 0.0) { throw "Merchant withdrawal fee detected in payout request" }

$adminHeaders = Get-RoleHeaders "admin" $adminHeaders "admin@fliptrybe.com" "demo12345"
Assert-Role "admin" $adminHeaders "Admin Payout Process"
Invoke-JsonPost "$base/api/wallet/payouts/$payoutId/admin/process" @{} $adminHeaders | Out-Null

$walletAfter = Invoke-JsonGet "$base/api/wallet" $merchantHeaders
$balanceAfter = [double]$walletAfter.wallet.balance
$expected = $balanceBefore - $withdrawAmount
if ([math]::Abs($balanceAfter - $expected) -gt 0.01) {
  throw "Withdrawal fee detected: expected balance $expected, actual $balanceAfter"
}

$ledger = Invoke-JsonGet "$base/api/wallet/ledger" $merchantHeaders
$commissionFound = $false
foreach ($txn in $ledger) {
  if ($txn.reference -eq "payout:$payoutId" -and ($txn.kind -match "commission")) {
    $commissionFound = $true
  }
}
if ($commissionFound) { throw "Commission ledger entry found for withdrawal" }

Log-Step "Buyer Withdrawal Fee" "/api/wallet/payouts" "buyer"
$buyerHeaders = Get-RoleHeaders "buyer" $buyerHeaders "buyer@fliptrybe.com" "demo12345"
Assert-Role "buyer" $buyerHeaders "Buyer Withdrawal"
Invoke-JsonPost "$base/api/wallet/topup-demo" @{ amount = 10000 } $buyerHeaders | Out-Null
$buyerWalletBefore = Invoke-JsonGet "$base/api/wallet" $buyerHeaders
$buyerBalanceBefore = [double]$buyerWalletBefore.wallet.balance
$buyerWithdrawAmount = 2000
$buyerPayout = Invoke-JsonPost "$base/api/wallet/payouts" @{
  amount = $buyerWithdrawAmount
  bank_name = "Demo Bank"
  account_number = "1112223334"
  account_name = "Demo Buyer"
} $buyerHeaders
$buyerPayoutId = $buyerPayout.payout.id
if (-not $buyerPayoutId) { throw "Buyer payout request failed" }
$buyerFee = 0.0
if ($buyerPayout -and $buyerPayout.payout -and $buyerPayout.payout.fee_amount) {
  $buyerFee = [double]$buyerPayout.payout.fee_amount
}
$expectedBuyerFee = [math]::Round(($buyerWithdrawAmount * 0.015), 2)
if ([math]::Abs($buyerFee - $expectedBuyerFee) -gt 0.01) { throw "Buyer withdrawal fee mismatch: expected $expectedBuyerFee, got $buyerFee" }
Invoke-JsonPost "$base/api/wallet/payouts/$buyerPayoutId/admin/process" @{} $adminHeaders | Out-Null
$buyerWalletAfter = Invoke-JsonGet "$base/api/wallet" $buyerHeaders
$buyerBalanceAfter = [double]$buyerWalletAfter.wallet.balance
$buyerExpected = $buyerBalanceBefore - $buyerWithdrawAmount
if ([math]::Abs($buyerBalanceAfter - $buyerExpected) -gt 0.01) {
  throw "Buyer withdrawal balance mismatch: expected $buyerExpected, got $buyerBalanceAfter"
}

Log-Step "Driver Instant Withdrawal Fee" "/api/wallet/payouts" "driver"
$driverHeaders = Get-RoleHeaders "driver" $driverHeaders "driver@fliptrybe.com" "demo12345"
Assert-Role "driver" $driverHeaders "Driver Instant Withdrawal"
Invoke-JsonPost "$base/api/wallet/topup-demo" @{ amount = 10000 } $driverHeaders | Out-Null
$driverWalletBefore = Invoke-JsonGet "$base/api/wallet" $driverHeaders
$driverBalanceBefore = [double]$driverWalletBefore.wallet.balance
$driverWithdrawAmount = 1000
$driverPayout = Invoke-JsonPost "$base/api/wallet/payouts" @{
  amount = $driverWithdrawAmount
  bank_name = "Demo Bank"
  account_number = "2223334445"
  account_name = "Demo Driver"
  instant = $true
} $driverHeaders
$driverPayoutId = $driverPayout.payout.id
if (-not $driverPayoutId) { throw "Driver payout request failed" }
$driverFee = 0.0
if ($driverPayout -and $driverPayout.payout -and $driverPayout.payout.fee_amount) {
  $driverFee = [double]$driverPayout.payout.fee_amount
}
$expectedDriverFee = [math]::Round(($driverWithdrawAmount * 0.01), 2)
if ([math]::Abs($driverFee - $expectedDriverFee) -gt 0.01) { throw "Driver instant fee mismatch: expected $expectedDriverFee, got $driverFee" }
Invoke-JsonPost "$base/api/wallet/payouts/$driverPayoutId/admin/process" @{} $adminHeaders | Out-Null
$driverWalletAfter = Invoke-JsonGet "$base/api/wallet" $driverHeaders
$driverBalanceAfter = [double]$driverWalletAfter.wallet.balance
$driverExpected = $driverBalanceBefore - $driverWithdrawAmount
if ([math]::Abs($driverBalanceAfter - $driverExpected) -gt 0.01) {
  throw "Driver withdrawal balance mismatch: expected $driverExpected, got $driverBalanceAfter"
}

Write-Host ""
Write-Host "================ SMOKE TEST SUMMARY ================"
Write-Host ("Order ID        : {0}" -f $orderFinal.id)
Write-Host ("Buyer ID        : {0}" -f $orderFinal.buyer_id)
Write-Host ("Merchant ID     : {0}" -f $orderFinal.merchant_id)

$driverOut = "N/A"
if ($orderFinal.driver_id) { $driverOut = $orderFinal.driver_id }
Write-Host ("Driver ID       : {0}" -f $driverOut)

Write-Host ("Final Status    : {0}" -f $orderFinal.status)

$tlCount = 0
if ($timeline -and $timeline.items) { $tlCount = $timeline.items.Count }
elseif ($timeline -and $timeline.events) { $tlCount = $timeline.events.Count }
elseif ($timeline -and $timeline.value) { $tlCount = $timeline.value.Count }
Write-Host ("Timeline Events : {0}" -f $tlCount)

Write-Host "===================================================="
Write-Host "TIP: Run twice back-to-back to confirm idempotence."
Write-Host ""
Write-Host "IDEMPOTENT: PASS"
Write-Host "Smoke test completed successfully."
