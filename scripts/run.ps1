param(
  [Parameter(Mandatory=$true,Position=0)]
  [ValidateSet('doctor','extract','validate','render','verify')]
  [string]$Action,
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$ScriptArguments
)
$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
  $taskPythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if (-not $taskPythonCommand) { throw 'Python was not found. Use a verified runtime with reportlab, pypdf and Pillow.' }
  $taskPython = $taskPythonCommand.Source
}
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
if ($Action -eq 'doctor') {
  & $taskPython -c "import sys,importlib.util,json; names=['reportlab','pypdf','PIL']; result={x:bool(importlib.util.find_spec(x)) for x in names}; print(json.dumps({'python':sys.executable,'packages':result})); sys.exit(0 if all(result.values()) else 1)"
} else {
  $taskScripts = @{extract='extract_sentences.py';validate='validate_content.py';render='render_notes.py';verify='verify_artifacts.py'}
  & $taskPython (Join-Path $PSScriptRoot $taskScripts[$Action]) @ScriptArguments
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
