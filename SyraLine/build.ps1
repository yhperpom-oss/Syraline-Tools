# SyraLine — Nuitka build (standalone onefile .exe)
# Run from this folder (the one containing main.py):
#     powershell -ExecutionPolicy Bypass -File build.ps1
#
# Produces: build-out\SyraLine.exe  (a single native .exe)
# Then protect that .exe with Themida or VMProtect (see ../PROTECTION.md).
#
# Recommended interpreter: Python 3.12 (matches the pinned wheels in
# requirements.txt). Nuitka downloads its own MinGW64 C compiler on first run.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Pick a Python: prefer 3.12 via the launcher, else whatever `python` resolves to.
$pyExe  = "python"
$pyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $has312 = $false
    try { py -3.12 --version *> $null; $has312 = $? } catch {}
    if ($has312) { $pyExe = "py"; $pyArgs = @("-3.12") }
}
# Call Python directly (not through a function): a function would bind the
# leading -m/-r as its own parameter, so pass every token straight to the exe.
function Invoke-Py {
    & $pyExe @pyArgs @args
    if ($LASTEXITCODE -ne 0) { throw "Python command failed: $($args -join ' ')" }
}
Write-Host "Using interpreter: $pyExe $($pyArgs -join ' ')"

# 1) Dependencies + Nuitka
Write-Host "`n[1/2] Installing dependencies and Nuitka..."
Invoke-Py -m pip install --upgrade pip
Invoke-Py -m pip install -r requirements.txt
Invoke-Py -m pip install nuitka ordered-set zstandard

# 2) Compile
Write-Host "`n[2/2] Compiling with Nuitka (10-30 min on the first run)..."
Invoke-Py -m nuitka `
    --standalone --onefile `
    --assume-yes-for-downloads `
    --output-dir=build-out `
    --output-filename=SyraLine.exe `
    --company-name=SyraLine --product-name=SyraLine --file-version=1.0.0.0 --product-version=1.0.0.0 `
    --windows-console-mode=force `
    --noinclude-pytest-mode=nofollow `
    --python-flag=no_asserts --python-flag=no_docstrings `
    --include-package=lib `
    --include-package=textual --include-package=rich `
    --include-data-dir=locales=locales `
    --include-data-dir=styles=styles `
    --include-data-dir=config=config `
    main.py
# NOTE: all other third-party libs (numpy, PIL, requests, dns, pyfiglet,
# psutil, qrcode, phonenumbers, pypdf, detect_secrets, arabic_reshaper, bidi,
# charset_normalizer, cryptography, zxing-cpp) are imported by the compiled
# code, so Nuitka's follow-imports includes exactly the needed parts WITHOUT
# their heavy test suites. Do NOT re-add --include-package=numpy: it drags in
# numpy's test modules and the C compile fails.

Write-Host "`nDone. Output: build-out\SyraLine.exe"
Write-Host "Next: protect build-out\SyraLine.exe with Themida/VMProtect (see ../PROTECTION.md)."
