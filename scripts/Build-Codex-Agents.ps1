[CmdletBinding()]
param([switch] $Check)

$ErrorActionPreference = 'Stop'
Write-Warning 'DEPRECADO: usa scripts/Build-Office.ps1 -Platform Codex; Build-Codex-Agents.ps1 delega en el núcleo unificado.'
& (Join-Path $PSScriptRoot 'Build-Office.ps1') -Platform Codex -Check:$Check
