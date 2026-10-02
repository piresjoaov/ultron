param(
    [string]$ServerPath = $env:ULTRON_SERVER_PATH,
    [string]$ModelPath = $env:ULTRON_MODEL_PATH,
    [string]$ModelDraftPath = $env:ULTRON_MODEL_DRAFT_PATH,
    [string]$Device = $(if ($env:ULTRON_DEVICE) { $env:ULTRON_DEVICE } else { "Vulkan0" }),
    [int]$ContextSize = $(if ($env:ULTRON_SERVER_CTX_SIZE) { [int]$env:ULTRON_SERVER_CTX_SIZE } else { 8192 })
)

if (-not $ServerPath) { $ServerPath = "C:\Users\joaov\llama.cpp\build\bin\Release\llama-server.exe" }
if (-not $ModelPath) { $ModelPath = Join-Path $PSScriptRoot "..\models\qwen3-8b-q4_k_m.gguf" }
if (-not $ModelDraftPath) { $ModelDraftPath = Join-Path $PSScriptRoot "..\models\qwen2.5-0.5b-instruct-q4_k_m.gguf" }

$arguments = @(
    "-m", (Resolve-Path $ModelPath -ErrorAction Stop).Path,
    "-ngl", "99",
    "--device", $Device,
    "-fa", "on",
    "--cache-type-k", "q8_0",
    "--cache-type-v", "q8_0",
    "-c", $ContextSize,
    "--fit", "on"
)

if (Test-Path -LiteralPath $ModelDraftPath -PathType Leaf) {
    $arguments += @("--model-draft", (Resolve-Path $ModelDraftPath).Path)
} else {
    Write-Warning "Draft model not found at '$ModelDraftPath'; starting without speculative decoding."
}

Write-Host "Starting llama-server with Flash Attention and q8_0 KV cache..."
& $ServerPath @arguments
exit $LASTEXITCODE