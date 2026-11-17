[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [string[]] $Path,

    [ValidateRange(1, 5)]
    [int] $Profile = 3,

    [switch] $Json,
    [switch] $Quiet
)

$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path -Parent $PSScriptRoot
$auditor = Join-Path $kitRoot 'skills/taste-skill/scripts/audit_taste.py'
$auditableExtensions = @('.css', '.scss', '.sass', '.less', '.html', '.htm', '.jsx', '.tsx', '.vue', '.svelte', '.astro', '.php')

function Stop-TasteAuditPreflight {
    param([string] $Message)
    [Console]::Error.WriteLine($Message)
    exit 2
}

if (-not (Test-Path -LiteralPath $auditor -PathType Leaf)) {
    Stop-TasteAuditPreflight "Taste auditor does not exist: '$auditor'."
}

$resolvedInputs = @()
foreach ($inputPath in $Path) {
    if (-not (Test-Path -LiteralPath $inputPath)) {
        Stop-TasteAuditPreflight "Taste audit input does not exist: '$inputPath'."
    }

    $resolved = (Resolve-Path -LiteralPath $inputPath).Path
    $auditableFiles = if (Test-Path -LiteralPath $resolved -PathType Leaf) {
        if ([IO.Path]::GetExtension($resolved) -cin $auditableExtensions) { @($resolved) } else { @() }
    } else {
        @(Get-ChildItem -LiteralPath $resolved -Recurse -File | Where-Object { $_.Extension -cin $auditableExtensions })
    }
    if ($auditableFiles.Count -eq 0) {
        Stop-TasteAuditPreflight "Taste audit input has no auditable files: '$inputPath'."
    }
    $resolvedInputs += $resolved
}

if (-not (Get-Command python -CommandType Application -ErrorAction SilentlyContinue)) {
    Stop-TasteAuditPreflight 'Python executable was not found on PATH.'
}

$arguments = @($auditor) + $resolvedInputs + @('--profile', [string] $Profile)
if ($Json) { $arguments += '--json' }
if ($Quiet) { $arguments += '--quiet' }

$hadPythonIoEncoding = Test-Path Env:PYTHONIOENCODING
$previousPythonIoEncoding = $env:PYTHONIOENCODING
$nativePreference = $PSNativeCommandUseErrorActionPreference
try {
    $env:PYTHONIOENCODING = 'utf-8'
    $PSNativeCommandUseErrorActionPreference = $false
    & python @arguments
    $auditExitCode = $LASTEXITCODE
} finally {
    $PSNativeCommandUseErrorActionPreference = $nativePreference
    if ($hadPythonIoEncoding) {
        $env:PYTHONIOENCODING = $previousPythonIoEncoding
    } else {
        Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue
    }
}

exit $auditExitCode
