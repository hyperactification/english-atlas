# Optional PowerShell convenience wrapper; scripts/run.py is the portable entry.
param(
  [Parameter(Mandatory=$true,Position=0)]
  [ValidateSet('doctor','extract','validate','render','verify')]
  [string]$Action,
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$ScriptArguments
)
$ErrorActionPreference = 'Stop'
$taskPython = $env:ENGLISH_ATLAS_PYTHON
$taskPythonArguments = @()
if ($taskPython) {
  if (-not (Test-Path -LiteralPath $taskPython)) {
    $taskCommand = Get-Command $taskPython -ErrorAction SilentlyContinue
    if (-not $taskCommand) { throw 'ENGLISH_ATLAS_PYTHON does not identify a Python executable.' }
    $taskPython = $taskCommand.Source
  }
} else {
  foreach ($taskName in @('python','python3','py')) {
    $taskCommand = Get-Command $taskName -ErrorAction SilentlyContinue
    if ($taskCommand) {
      $taskPython = $taskCommand.Source
      if ($taskName -eq 'py') { $taskPythonArguments = @('-3') }
      break
    }
  }
}
if (-not $taskPython) { throw 'Python 3.10+ was not found. Install Python or set ENGLISH_ATLAS_PYTHON to its executable.' }
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
& $taskPython @taskPythonArguments (Join-Path $PSScriptRoot 'run.py') $Action @ScriptArguments
exit $LASTEXITCODE
