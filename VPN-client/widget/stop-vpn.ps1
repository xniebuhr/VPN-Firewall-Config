$ErrorActionPreference = "SilentlyContinue"

$xrayDir = "<path to xray items>"
$configPath = Join-Path $xrayDir "config.json"
$wgExe = "C:\Program Files\WireGuard\wireguard.exe"

# Get IP and kill route
$configData = Get-Content -Raw $configPath | ConvertFrom-Json
$vmIp = $configData.outbounds[0].settings.vnext[0].address
route delete $vmIp

# Kill wireguard
& $wgExe /uninstalltunnelservice VPN

# Kill xray
Stop-Process -Name "xray" -Force

# Always return 0
exit 0