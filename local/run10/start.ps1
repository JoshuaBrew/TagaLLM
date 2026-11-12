param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 19471,
    [Parameter(Mandatory)][string]$RuntimePath,
    [Parameter(Mandatory)][string]$ModelPath,
    [Parameter(Mandatory)][string]$SourceLibrary
)

$ErrorActionPreference = 'Stop'
$runtime = (Resolve-Path -LiteralPath $RuntimePath).Path
$model = (Resolve-Path -LiteralPath $ModelPath).Path
$python = Get-Command python -CommandType Application | Select-Object -First 1 -ExpandProperty Source
$chatArgs = @('-X', 'utf8', (Join-Path $PSScriptRoot 'serve.py'))

$health = "http://127.0.0.1:$Port/health"
$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listener) { throw "Port $Port is in use. Choose another port with -Port." }

$previousPort = $env:TAGALLM_GEMMA_PORT
$previousLibrary = $env:TAGALLM_SOURCE_LIBRARY
$SourceLibrary = (Resolve-Path -LiteralPath $SourceLibrary).Path
$server = Start-Process -FilePath $runtime -WindowStyle Hidden -PassThru -ArgumentList (
    "--model `"$model`" --host 127.0.0.1 --port $Port --ctx-size 4096 " +
    '--parallel 1 --threads 4 --n-gpu-layers 0 --reasoning off --alias TagaLLM'
)
try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($server.HasExited) { throw "Gemma exited during startup (code $($server.ExitCode))." }
        try {
            $ready = (Invoke-RestMethod -Uri $health -TimeoutSec 1).status -eq 'ok'
        } catch {
            $ready = $false
        }
        if ($ready) { break }
        Start-Sleep -Milliseconds 500
    }
    if (!$ready) { throw "Gemma did not become ready on port $Port." }
    $env:TAGALLM_GEMMA_PORT = "$Port"
    $env:TAGALLM_SOURCE_LIBRARY = $SourceLibrary
    Write-Host "Open http://127.0.0.1:7879/ to chat with Run 10."
    & $python @chatArgs
    if ($LASTEXITCODE -ne 0) { throw "Chat exited with code $LASTEXITCODE." }
} finally {
    $env:TAGALLM_GEMMA_PORT = $previousPort
    $env:TAGALLM_SOURCE_LIBRARY = $previousLibrary
    if (!$server.HasExited) { Stop-Process -InputObject $server }
}
