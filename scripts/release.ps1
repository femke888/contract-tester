param(
    [ValidateSet("none", "patch", "minor", "major")]
    [string]$Bump = "none"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Get-Python {
    if (Test-Path ".venv\\Scripts\\python.exe") {
        return ".venv\\Scripts\\python.exe"
    }
    if (Test-Path ".venv_test\\Scripts\\python.exe") {
        return ".venv_test\\Scripts\\python.exe"
    }
    return "python"
}

function Invoke-External([string]$label, [scriptblock]$cmd) {
    Write-Host $label
    & $cmd
    if ($LASTEXITCODE -ne 0) {
        throw "$label failed with exit code $LASTEXITCODE"
    }
}

function Bump-Version([string]$kind) {
    if ($kind -eq "none") {
        return
    }
    $initPath = "src\\contract_tester\\__init__.py"
    $content = Get-Content -Path $initPath -Raw
    $m = [regex]::Match($content, '__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"')
    if (-not $m.Success) {
        throw "Could not find semantic __version__ in $initPath"
    }
    $major = [int]$m.Groups[1].Value
    $minor = [int]$m.Groups[2].Value
    $patch = [int]$m.Groups[3].Value

    switch ($kind) {
        "patch" { $patch += 1 }
        "minor" { $minor += 1; $patch = 0 }
        "major" { $major += 1; $minor = 0; $patch = 0 }
    }

    $newVersion = "$major.$minor.$patch"
    $updated = [regex]::Replace(
        $content,
        '__version__\s*=\s*"\d+\.\d+\.\d+"',
        "__version__ = `"$newVersion`"",
        1
    )
    Set-Content -Path $initPath -Value $updated -Encoding ASCII
    Write-Host "Version bumped to $newVersion"
}

$python = Get-Python

Bump-Version -kind $Bump

Invoke-External "Syncing dependencies..." { & $python -m pip install -r requirements.txt }
Invoke-External "Ensuring Ruff is installed..." { & $python -m pip install ruff }
Invoke-External "Running factory readiness check..." { & $python ".\\scripts\\check_factory_readiness.py" }
Invoke-External "Running lint..." { & $python -m ruff check . }
Invoke-External "Running tests..." { & $python -m unittest }
Invoke-External "Building binary..." { & ".\\scripts\\build.ps1" }
Invoke-External "Writing checksums..." { & $python ".\\scripts\\write_checksums.py" --dist dist }

Write-Host "Release checks complete."
