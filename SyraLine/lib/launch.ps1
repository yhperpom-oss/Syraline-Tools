param([switch]$Setup, [Parameter(ValueFromRemainingArguments=$true)][string[]]$AppArguments)
$ErrorActionPreference = 'Stop'
$env:NO_COLOR = $null
$env:COLORTERM = 'truecolor'
$env:TERM = 'xterm-256color'
$syralineApp = Split-Path -Parent $PSScriptRoot
$syralineRoot = Split-Path -Parent $syralineApp
$syralineVenvDir = Join-Path $syralineRoot '.venv'
$syralineVenv = Join-Path $syralineVenvDir 'Scripts\python.exe'
function Test-SyraLinePython([string]$Executable) {
    if (-not $Executable -or -not (Test-Path -LiteralPath $Executable)) {return $false}
    try {
        & $Executable -I -c 'import sys,struct; sys.exit(0 if (3,12) <= sys.version_info[:2] <= (3,14) and struct.calcsize(chr(80))==8 else 1)' *> $null
        return $LASTEXITCODE -eq 0
    } catch {return $false}
}
function Save-SyraLineDownload([string]$Url, [string]$Destination, [string]$Sha256) {
    if (Test-Path -LiteralPath $Destination) {
        if ((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash -eq $Sha256) {return}
    }
    for ($syralineAttempt = 1; $syralineAttempt -le 3; $syralineAttempt++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $Destination
            if ((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash -ne $Sha256) {throw 'Download checksum mismatch.'}
            return
        } catch {
            if ($syralineAttempt -eq 3) {throw}
        }
    }
}
function Install-SyraLinePortablePip {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $syralineCache = Join-Path $syralineRoot '.python-download'
    $syralineSite = Join-Path $syralineVenvDir 'Scripts\Lib\site-packages'
    New-Item -ItemType Directory -Force -Path $syralineCache, $syralineSite | Out-Null
    @('python313.zip','.', '..\..\SyraLine', 'Lib\site-packages','import site') | Set-Content -LiteralPath (Join-Path $syralineVenvDir 'Scripts\python313._pth') -Encoding ascii
    $syralinePipMetadata = Invoke-RestMethod -Uri 'https://pypi.org/pypi/pip/25.3/json'
    $syralinePipWheel = $syralinePipMetadata.urls | Where-Object { $_.filename -eq 'pip-25.3-py3-none-any.whl' } | Select-Object -First 1
    if (-not $syralinePipWheel -or -not $syralinePipWheel.url.StartsWith('https://files.pythonhosted.org/')) {throw 'Invalid pip download metadata.'}
    $syralinePipArchive = Join-Path $syralineCache 'pip-25.3.zip'
    Save-SyraLineDownload $syralinePipWheel.url $syralinePipArchive $syralinePipWheel.digests.sha256
    Expand-Archive -LiteralPath $syralinePipArchive -DestinationPath $syralineSite -Force
}
try {
    $syralineExe = $null
    if (Test-SyraLinePython $syralineVenv) {$syralineExe = $syralineVenv}
    if (-not $syralineExe) {
        foreach ($syralineVersion in @('3.13','3.12','3.14')) {
            if (Get-Command py -ErrorAction SilentlyContinue) {
                try {
                    $syralineResult = & py "-$syralineVersion" -I -c 'import sys; print(sys.executable)' 2>$null
                    if ($LASTEXITCODE -eq 0 -and (Test-SyraLinePython "$syralineResult")) {$syralineExe = "$syralineResult"; break}
                } catch {}
            }
        }
    }
    if (-not $syralineExe -and (Get-Command python -ErrorAction SilentlyContinue)) {
        try {
            $syralineResult = & python -I -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and (Test-SyraLinePython "$syralineResult")) {$syralineExe = "$syralineResult"}
        } catch {}
    }
    if (-not (Test-SyraLinePython $syralineVenv)) {
        if (Test-Path -LiteralPath $syralineVenvDir) {
            $syralineBackup = Join-Path $syralineRoot ('.venv-backup-' + [guid]::NewGuid().ToString('N'))
            Move-Item -LiteralPath $syralineVenvDir -Destination $syralineBackup
            Write-Host 'Previous environment preserved; creating a compatible environment.'
        }
        if ($syralineExe) {
            & $syralineExe -m venv $syralineVenvDir
            if ($LASTEXITCODE -ne 0) {throw 'Could not create the Python environment.'}
        } else {
            Write-Host 'Preparing portable Python / Preparation automatique de Python...'
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            $syralineCache = Join-Path $syralineRoot '.python-download'
            New-Item -ItemType Directory -Force -Path $syralineCache | Out-Null
            $syralineArchive = Join-Path $syralineCache 'python-3.13.12-embed-amd64.zip'
            Save-SyraLineDownload 'https://www.python.org/ftp/python/3.13.12/python-3.13.12-embed-amd64.zip' $syralineArchive '76f238f606250c87c6beac75dccd35ee99070a13490555936abb6cb64ecce3d0'
            $syralineRuntime = Join-Path $syralineVenvDir 'Scripts'
            Expand-Archive -LiteralPath $syralineArchive -DestinationPath $syralineRuntime -Force
            $syralineSite = Join-Path $syralineRuntime 'Lib\site-packages'
            New-Item -ItemType Directory -Force -Path $syralineSite | Out-Null
            @('python313.zip','.', '..\..\SyraLine', 'Lib\site-packages','import site') | Set-Content -LiteralPath (Join-Path $syralineRuntime 'python313._pth') -Encoding ascii
            Install-SyraLinePortablePip
        }
        if (-not (Test-SyraLinePython $syralineVenv)) {throw 'Python environment verification failed. Run setup.bat again.'}
    }
    & $syralineVenv -m pip --version *> $null
    if ($LASTEXITCODE -ne 0) {
        if (Test-Path -LiteralPath (Join-Path $syralineVenvDir 'Scripts\python313._pth')) {
            Install-SyraLinePortablePip
        } else {
            & $syralineVenv -m ensurepip --upgrade
            if ($LASTEXITCODE -ne 0) {throw 'pip repair failed. Run setup.bat again.'}
        }
        & $syralineVenv -m pip --version *> $null
        if ($LASTEXITCODE -ne 0) {throw 'pip repair could not be verified.'}
    }
    & $syralineVenv (Join-Path $PSScriptRoot 'setup_modules.py')
    if ($LASTEXITCODE -ne 0) {exit $LASTEXITCODE}
    if ($Setup) {exit 0}
    & $syralineVenv (Join-Path $syralineApp 'main.py') @AppArguments
    exit $LASTEXITCODE
} catch {
    Write-Host ('Setup failed / Installation impossible: ' + $_.Exception.Message + ' Check your connection and run setup.bat again.') -ForegroundColor Red
    exit 1
}
