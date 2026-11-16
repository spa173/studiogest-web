[CmdletBinding()]
param([string] $Section = 'All')

$ErrorActionPreference = 'Stop'
Write-Warning 'DEPRECADO: usa scripts/Test-Office.Core.ps1; Test-Equipo.ps1 delega en el núcleo unificado.'
& (Join-Path $PSScriptRoot 'Test-Office.Core.ps1') -Section $Section
