Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Invariants {
    param(
        [Parameter(Mandatory = $true)]$State,
        [Parameter(Mandatory = $true)]$Context
    )

    Write-Log -State $State -Message "Running invariants"

    # 1) Seller cannot buy own listing
    $selfRef = "inv_selfbuy_{0}" -f (Get-Random)
    $beforeCount = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM orders WHERE payment_reference=?" -Params @($selfRef))
    $selfBuy = Invoke-Api -State $State -Method "POST" -Path "/api/orders" -Headers $Context.Headers.Merchant -BodyObj @{
        merchant_id = [int]$Context.Users.Merchant.id
        amount = 15000
        delivery_fee = 1000
        inspection_fee = 0
        pickup = "Ikeja"
        dropoff = "Yaba"
        payment_reference = $selfRef
    }
    $afterCount = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM orders WHERE payment_reference=?" -Params @($selfRef))
    $walletRefRows = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM wallet_txns WHERE reference=?" -Params @($selfRef))
    $selfPass = ($selfBuy.StatusCode -in @(400,403,409)) -and ($beforeCount -eq 0) -and ($afterCount -eq 0) -and ($walletRefRows -eq 0)
    Add-Result -State $State -Phase "INVARIANTS" -Test "seller_cannot_buy_own" -Pass $selfPass -Status ($selfBuy.StatusCode.ToString()) -Detail ("orders_before={0}, orders_after={1}, wallet_ref_rows={2}" -f $beforeCount,$afterCount,$walletRefRows)

    # 2) Follow rules
    $followBuyer = Invoke-Api -State $State -Method "POST" -Path ("/api/merchants/{0}/follow" -f $Context.Users.Merchant.id) -Headers $Context.Headers.Buyer
    $followMerchantToBuyer = Invoke-Api -State $State -Method "POST" -Path ("/api/merchants/{0}/follow" -f $Context.Users.Buyer.id) -Headers $Context.Headers.Merchant
    $followMerchantToMerchant = Invoke-Api -State $State -Method "POST" -Path ("/api/merchants/{0}/follow" -f $Context.Users.Merchant.id) -Headers $Context.Headers.Merchant

    $merchantFollowRows = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM merchant_follows WHERE follower_id=?" -Params @([int]$Context.Users.Merchant.id))
    $buyerFollowRows = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM merchant_follows WHERE follower_id=? AND merchant_id=?" -Params @([int]$Context.Users.Buyer.id, [int]$Context.Users.Merchant.id))

    $followPass = ($followBuyer.StatusCode -in @(200,201)) -and ($followMerchantToBuyer.StatusCode -in @(400,403,404,409)) -and ($followMerchantToMerchant.StatusCode -in @(400,403,404,409)) -and ($merchantFollowRows -eq 0) -and ($buyerFollowRows -ge 1)
    Add-Result -State $State -Phase "INVARIANTS" -Test "follow_rules" -Pass $followPass -Status ("{0}/{1}/{2}" -f $followBuyer.StatusCode,$followMerchantToBuyer.StatusCode,$followMerchantToMerchant.StatusCode) -Detail ("merchant_follow_rows={0}, buyer_follow_rows={1}" -f $merchantFollowRows,$buyerFollowRows)

    # 3) Chat rules via support chat
    $buyerToAdmin = Invoke-Api -State $State -Method "POST" -Path "/api/support/messages" -Headers $Context.Headers.Buyer -BodyObj @{ body = "buyer support ping" }
    $driverToAdmin = Invoke-Api -State $State -Method "POST" -Path "/api/support/messages" -Headers $Context.Headers.Driver -BodyObj @{ body = "driver support ping" }
    $adminToBuyer = Invoke-Api -State $State -Method "POST" -Path ("/api/admin/support/messages/{0}" -f $Context.Users.Buyer.id) -Headers $Context.Headers.Admin -BodyObj @{ body = "admin response" }

    $buyerToDriver = Invoke-Api -State $State -Method "POST" -Path ("/api/admin/support/messages/{0}" -f $Context.Users.Driver.id) -Headers $Context.Headers.Buyer -BodyObj @{ body = "should fail" }
    $buyerToMerchant = Invoke-Api -State $State -Method "POST" -Path ("/api/admin/support/messages/{0}" -f $Context.Users.Merchant.id) -Headers $Context.Headers.Buyer -BodyObj @{ body = "should fail" }
    $merchantToDriver = Invoke-Api -State $State -Method "POST" -Path ("/api/admin/support/messages/{0}" -f $Context.Users.Driver.id) -Headers $Context.Headers.Merchant -BodyObj @{ body = "should fail" }
    $directChatTry = Invoke-Api -State $State -Method "POST" -Path "/api/chat/messages" -Headers $Context.Headers.Buyer -BodyObj @{ to_user_id = $Context.Users.Driver.id; body = "blocked" }

    $chatPass = ($buyerToAdmin.StatusCode -in @(200,201)) -and ($driverToAdmin.StatusCode -in @(200,201)) -and ($adminToBuyer.StatusCode -in @(200,201)) -and ($buyerToDriver.StatusCode -in @(401,403,404)) -and ($buyerToMerchant.StatusCode -in @(401,403,404)) -and ($merchantToDriver.StatusCode -in @(401,403,404)) -and ($directChatTry.StatusCode -in @(400,401,403,404,405))
    Add-Result -State $State -Phase "INVARIANTS" -Test "chat_rules" -Pass $chatPass -Status ("{0}/{1}/{2}/{3}/{4}/{5}/{6}" -f $buyerToAdmin.StatusCode,$driverToAdmin.StatusCode,$adminToBuyer.StatusCode,$buyerToDriver.StatusCode,$buyerToMerchant.StatusCode,$merchantToDriver.StatusCode,$directChatTry.StatusCode) -Detail "support chat/admin gating validated"

    # 4) Role switch strict + admin controlled
    $roleEmail = New-UniqueEmail -Prefix "inv_role"
    $roleReg = Register-Role -State $State -Role "buyer" -Payload @{ email = $roleEmail; password = $Context.Password; name = "Role Invariant Buyer" }
    $roleLogin = Login-User -State $State -Email $roleEmail -Password $Context.Password
    $roleToken = [string]$roleLogin.Json.token
    $roleHeaders = @{ Authorization = "Bearer $roleToken" }

    $setRoleAttempt = Invoke-Api -State $State -Method "POST" -Path "/api/auth/set-role" -Headers $roleHeaders -BodyObj @{ role = "merchant" }
    $requestChange = Invoke-Api -State $State -Method "POST" -Path "/api/role-requests" -Headers $roleHeaders -BodyObj @{ requested_role = "driver"; reason = "invariant" }
    $requestMe = Invoke-Api -State $State -Method "GET" -Path "/api/role-requests/me" -Headers $roleHeaders
    $meBefore = Invoke-Api -State $State -Method "GET" -Path "/api/auth/me" -Headers $roleHeaders

    $roleUserId = [int]$roleReg.Json.user.id
    $approveRole = Approve-RoleRequest -State $State -AdminHeaders $Context.Headers.Admin -UserId $roleUserId -RequestedRole "driver" -AdminNote "invariant approve"
    $roleRelogin = Login-User -State $State -Email $roleEmail -Password $Context.Password
    $roleHeadersAfter = @{ Authorization = "Bearer $($roleRelogin.Json.token)" }
    $meAfter = Invoke-Api -State $State -Method "GET" -Path "/api/auth/me" -Headers $roleHeadersAfter

    $rcr = Invoke-DbQuery -State $State -Sql "SELECT status, requested_role FROM role_change_requests WHERE user_id=? ORDER BY id DESC LIMIT 1" -Params @($roleUserId)
    $rcrRows = @()
    if ($rcr -and ($rcr.PSObject.Properties.Name -contains "rows")) { $rcrRows = @($rcr.rows) }
    $rcrStatus = if ($rcrRows.Count -gt 0 -and $rcrRows[0] -is [System.Collections.IList] -and $rcrRows[0].Count -gt 0) { [string]$rcrRows[0][0] } else { "NONE" }
    $rolePass = ($setRoleAttempt.StatusCode -in @(403,404)) -and ($requestChange.StatusCode -in @(200,201)) -and ($requestMe.StatusCode -eq 200) -and (([string]$meBefore.Json.role) -eq "buyer") -and ($approveRole.Ok) -and (([string]$meAfter.Json.role) -eq "driver") -and ($rcrStatus -eq "APPROVED")
    Add-Result -State $State -Phase "INVARIANTS" -Test "role_switch_control" -Pass $rolePass -Status ("set={0},req={1},approve={2},after={3}" -f $setRoleAttempt.StatusCode,$requestChange.StatusCode,$approveRole.StatusCode,$meAfter.StatusCode) -Detail ("role_after={0}, request_status={1}" -f $meAfter.Json.role,$rcrStatus)

    # 5) Idempotency + replay safety
    $dupRef = "inv_dup_{0}" -f (Get-Random)
    $firstCreate = Invoke-Api -State $State -Method "POST" -Path "/api/orders" -Headers $Context.Headers.Buyer -BodyObj @{
        merchant_id = [int]$Context.Users.Merchant.id
        amount = 22000
        delivery_fee = 1500
        inspection_fee = 0
        pickup = "Ikeja"
        dropoff = "Yaba"
        payment_reference = $dupRef
    }
    $secondCreate = Invoke-Api -State $State -Method "POST" -Path "/api/orders" -Headers $Context.Headers.Buyer -BodyObj @{
        merchant_id = [int]$Context.Users.Merchant.id
        amount = 22000
        delivery_fee = 1500
        inspection_fee = 0
        pickup = "Ikeja"
        dropoff = "Yaba"
        payment_reference = $dupRef
    }

    $dupOrderId = [int]$firstCreate.Json.order.id
    $dupCount = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM orders WHERE payment_reference=?" -Params @($dupRef))

    $mark1 = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/mark-paid" -f $dupOrderId) -Headers $Context.Headers.Buyer -BodyObj @{ reference = $dupRef }
    $beforeTxn = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM wallet_txns WHERE reference=?" -Params @("order:$dupOrderId"))
    $mark2 = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/mark-paid" -f $dupOrderId) -Headers $Context.Headers.Buyer -BodyObj @{ reference = $dupRef }
    $afterTxn = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM wallet_txns WHERE reference=?" -Params @("order:$dupOrderId"))

    $flow = New-DeliveryOrder -State $State -MerchantId ([int]$Context.Users.Merchant.id) -DriverId ([int]$Context.Users.Driver.id) -BuyerHeaders $Context.Headers.Buyer -MerchantHeaders $Context.Headers.Merchant -Reference ("inv_flow_{0}" -f (Get-Random))
    $flowId = [int]$flow.OrderId
    $issueP = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/qr/issue" -f $flowId) -Headers $Context.Headers.Driver -BodyObj @{ step = "pickup_seller" }
    $scanP = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/qr/scan" -f $flowId) -Headers $Context.Headers.Merchant -BodyObj @{ token = $issueP.Json.token }
    $pickCode = Get-CodeFromApiOrDb -State $State -OrderId $flowId -BuyerHeaders $Context.Headers.Buyer -Kind pickup
    $pickOk = Invoke-Api -State $State -Method "POST" -Path ("/api/seller/orders/{0}/confirm-pickup" -f $flowId) -Headers $Context.Headers.Merchant -BodyObj @{ code = $pickCode }
    $pickReplay = Invoke-Api -State $State -Method "POST" -Path ("/api/seller/orders/{0}/confirm-pickup" -f $flowId) -Headers $Context.Headers.Merchant -BodyObj @{ code = $pickCode }

    $driverPicked = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/driver/status" -f $flowId) -Headers $Context.Headers.Driver -BodyObj @{ status = "picked_up" }
    $issueD = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/qr/issue" -f $flowId) -Headers $Context.Headers.Buyer -BodyObj @{ step = "delivery_driver" }
    $scanD = Invoke-Api -State $State -Method "POST" -Path ("/api/orders/{0}/qr/scan" -f $flowId) -Headers $Context.Headers.Driver -BodyObj @{ token = $issueD.Json.token }
    $dropCode = Get-CodeFromApiOrDb -State $State -OrderId $flowId -BuyerHeaders $Context.Headers.Buyer -Kind dropoff
    $dropOk = Invoke-Api -State $State -Method "POST" -Path ("/api/driver/orders/{0}/confirm-delivery" -f $flowId) -Headers $Context.Headers.Driver -BodyObj @{ code = $dropCode }
    $dropReplay = Invoke-Api -State $State -Method "POST" -Path ("/api/driver/orders/{0}/confirm-delivery" -f $flowId) -Headers $Context.Headers.Driver -BodyObj @{ code = $dropCode }

    $releaseEvents = [int](Get-DbScalar -State $State -Sql "SELECT COUNT(*) FROM order_events WHERE order_id=? AND event='escrow_released'" -Params @($flowId))
    $idempotentPass = ($firstCreate.StatusCode -eq 201) -and ($secondCreate.StatusCode -in @(200,409)) -and ($dupCount -eq 1) -and ($mark1.StatusCode -in @(200,409)) -and ($mark2.StatusCode -in @(200,409)) -and ($beforeTxn -eq $afterTxn) -and ($pickReplay.StatusCode -eq 409) -and ($dropReplay.StatusCode -eq 409) -and ($releaseEvents -eq 1)
    Add-Result -State $State -Phase "INVARIANTS" -Test "idempotency_replay" -Pass $idempotentPass -Status ("create={0}/{1}, mark={2}/{3}, replay={4}/{5}" -f $firstCreate.StatusCode,$secondCreate.StatusCode,$mark1.StatusCode,$mark2.StatusCode,$pickReplay.StatusCode,$dropReplay.StatusCode) -Detail ("dup_count={0}, tx_before_after={1}/{2}, release_events={3}, flow_id={4}" -f $dupCount,$beforeTxn,$afterTxn,$releaseEvents,$flowId)

    Db-SnapOrder -State $State -OrderId $flowId -Label "INV_IDEMPOTENCY"
}
