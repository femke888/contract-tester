$ErrorActionPreference = "Stop"

$python = "python"
if (Test-Path ".venv\\Scripts\\python.exe") {
    $python = ".venv\\Scripts\\python.exe"
} elseif (Test-Path ".venv_test\\Scripts\\python.exe") {
    $python = ".venv_test\\Scripts\\python.exe"
}

if (-not (& $python -m PyInstaller --version 2>$null)) {
    Write-Error "PyInstaller not found in $python. Install with: $python -m pip install pyinstaller"
}

# Single source of truth: read version from contract_tester.__version__ and
# regenerate the Windows version resource before each build.
$initPath = "src\\contract_tester\\__init__.py"
if (-not (Test-Path $initPath)) {
    Write-Error "Version source not found: $initPath"
}

$initContent = Get-Content -Path $initPath -Raw
$versionMatch = [regex]::Match($initContent, '__version__\s*=\s*"([^"]+)"')
if (-not $versionMatch.Success) {
    Write-Error "Could not parse __version__ from $initPath"
}
$version = $versionMatch.Groups[1].Value

$parts = $version.Split(".")
if ($parts.Length -lt 3) {
    Write-Error "Version must use major.minor.patch format. Found: $version"
}
$major = [int]$parts[0]
$minor = [int]$parts[1]
$patch = [int]$parts[2]

$versionTxt = @"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($major, $minor, $patch, 0),
    prodvers=($major, $minor, $patch, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          "040904b0",
          [
            StringStruct("CompanyName", "Local API Contract Tester"),
            StringStruct("FileDescription", "Local API Contract Tester"),
            StringStruct("FileVersion", "$version"),
            StringStruct("InternalName", "contract-tester"),
            StringStruct("OriginalFilename", "contract-tester.exe"),
            StringStruct("ProductName", "Local API Contract Tester"),
            StringStruct("ProductVersion", "$version"),
          ],
        )
      ]
    ),
    VarFileInfo([VarStruct("Translation", [1033, 1200])]),
  ],
)
"@
Set-Content -Path "version.txt" -Value $versionTxt -Encoding ASCII

& $python -m PyInstaller --clean --noconfirm pyinstaller.spec
Write-Host "Build complete. See dist/contract-tester/"
