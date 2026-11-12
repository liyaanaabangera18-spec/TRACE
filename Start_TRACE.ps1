$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$traceCandidates = @()
foreach ($traceName in @('py', 'python')) {
    $traceCommand = Get-Command $traceName -ErrorAction SilentlyContinue
    if ($traceCommand) { $traceCandidates += $traceCommand.Source }
}
$traceCandidates += "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$traceRuntime = $null
foreach ($traceCandidate in $traceCandidates) {
    if (Test-Path -LiteralPath $traceCandidate) {
        try {
            & $traceCandidate -c 'import sys; assert sys.version_info >= (3,10)' 2>$null
            if ($LASTEXITCODE -eq 0) { $traceRuntime = $traceCandidate; break }
        } catch { }
    }
}
if (-not $traceRuntime) {
    Write-Host 'Python 3.10 or newer could not be found. Install Python, then run Start_TRACE again.'
    exit 1
}
& $traceRuntime app.py --open
exit $LASTEXITCODE
