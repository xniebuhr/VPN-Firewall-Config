$ErrorActionPreference = "Stop"

$xrayDir = "<path to xray items>"
$configPath = Join-Path $xrayDir "config.json"
$wgConfigPath = Join-Path $xrayDir "VPN.conf"
$wgExe = "C:\Program Files\WireGuard\wireguard.exe"

try {
    # Get VM IP
    $configData = Get-Content -Raw $configPath | ConvertFrom-Json
    $vmIp = $configData.outbounds[0].settings.vnext[0].address

    # Add route
    $gw = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Sort-Object RouteMetric | Select-Object -First 1).NextHop
    route -p add $vmIp mask 255.255.255.255 $gw


    # Start xray
    Start-Process -FilePath "$xrayDir\xray.exe" -ArgumentList "run -c config.json" -WorkingDirectory $xrayDir -WindowStyle Hidden

    # Start wireguard
    & $wgExe /installtunnelservice $wgConfigPath
    
    # Success
    exit 0

} catch {
    # Rollback on fail
    $ErrorActionPreference = "SilentlyContinue" # Ignore errors during cleanup
    
    # Try to grab IP again
    if ($null -eq $vmIp) {
        $configData = Get-Content -Raw $configPath | ConvertFrom-Json
        $vmIp = $configData.outbounds[0].settings.vnext[0].address
    }

    # Cleanup route
    route delete $vmIp
    
    # Stop wireguard
    & $wgExe /uninstalltunnelservice VPN
    
    # Stop xray
    Stop-Process -Name "xray" -Force

    # Failure
    exit 1
}