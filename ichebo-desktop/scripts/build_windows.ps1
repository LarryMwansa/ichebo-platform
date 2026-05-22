# build_windows.ps1 — Build Ichebo Desktop as a Windows MSIX installer.
#
# Requirements:
#   - Flutter SDK on PATH
#   - Go 1.21+ on PATH (CGO with MinGW-w64 gcc)
#   - makeappx.exe and signtool.exe (Windows SDK)
#   - A code-signing certificate in the Windows Certificate Store
#
# Usage (PowerShell, from ichebo-desktop/):
#   .\scripts\build_windows.ps1
#
# Output: dist\IcheboDesktop-x64.msix

param(
    [switch]$SkipGo,
    [string]$Publisher = "CN=Ichebo Christian Services"
)

$ErrorActionPreference = "Stop"
$Root       = Split-Path $PSScriptRoot -Parent
$Dist       = Join-Path $Root "dist"
$MsixStage  = Join-Path $Dist "msix_stage"

Write-Host "==> Ichebo Desktop — Windows MSIX build"

# ── 1. Rebuild sync engine DLL ─────────────────────────────────────────────────
if (-not $SkipGo) {
    Write-Host "--> Building ichebo_sync.dll"
    Push-Location (Join-Path $Root "..\ichebo-sync")
    $env:CGO_ENABLED = "1"
    go build -buildmode=c-shared `
        -o (Join-Path $Root "windows\runner\Resources\ichebo_sync.dll") `
        .\ffi\
    Pop-Location
}

# ── 2. Flutter release build ──────────────────────────────────────────────────
Write-Host "--> flutter build windows --release"
Push-Location $Root
flutter build windows --release
Pop-Location

$Bundle = Join-Path $Root "build\windows\x64\runner\Release"

# ── 3. Assemble MSIX stage ────────────────────────────────────────────────────
Write-Host "--> Assembling MSIX package"
Remove-Item -Recurse -Force $MsixStage -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $MsixStage | Out-Null
New-Item -ItemType Directory -Path $Dist -ErrorAction SilentlyContinue | Out-Null

Copy-Item -Recurse "$Bundle\*" $MsixStage

@"
<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
  <Identity Name="IcheboChristianServices.IcheboDesktop"
            Publisher="$Publisher"
            Version="1.0.0.0"
            ProcessorArchitecture="x64"/>
  <Properties>
    <DisplayName>Ichebo Desktop</DisplayName>
    <PublisherDisplayName>Ichebo Christian Services</PublisherDisplayName>
    <Logo>Assets\ichebo_icon.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22621.0"/>
  </Dependencies>
  <Resources><Resource Language="en-us"/></Resources>
  <Applications>
    <Application Id="IcheboDesktop" Executable="ichebo_desktop.exe"
                 EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="Ichebo Desktop"
                          Description="Ichebo Community Operating System"
                          BackgroundColor="transparent"
                          Square150x150Logo="Assets\ichebo_icon.png"
                          Square44x44Logo="Assets\ichebo_icon.png"/>
    </Application>
  </Applications>
  <Capabilities><rescap:Capability Name="runFullTrust"/></Capabilities>
</Package>
"@ | Set-Content (Join-Path $MsixStage "AppxManifest.xml") -Encoding UTF8

$Out = Join-Path $Dist "IcheboDesktop-x64.msix"
makeappx pack /d $MsixStage /p $Out /overwrite

Write-Host ""
Write-Host "==> Done: $Out"
