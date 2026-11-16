[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path -Parent $PSScriptRoot
$targetItem = Resolve-Path -LiteralPath $Target
if (-not (Test-Path -LiteralPath $targetItem.Path -PathType Container)) {
    throw "La ruta de destino no es una carpeta: $Target"
}

$targetRoot = [System.IO.Path]::GetFullPath($targetItem.Path).TrimEnd('\', '/')
$kitPath = [System.IO.Path]::GetFullPath($kitRoot).TrimEnd('\', '/')
if ([string]::Equals($targetRoot, $kitPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'El destino no puede ser la carpeta del kit.'
}

$sourceAgentDir = Join-Path $kitRoot '.opencode\agents'
$sourceCodexDir = Join-Path $kitRoot 'codex\roles'
$sourceCodexAgentDir = Join-Path $kitRoot '.codex\agents'
$destOpenCodeDir = Join-Path $targetRoot '.opencode\agents'
$destCodexDir = Join-Path $targetRoot '.codex\roles'
$destCodexAgentDir = Join-Path $targetRoot '.codex\agents'
$sourceAgents = @(Get-ChildItem -LiteralPath $sourceAgentDir -Filter '*.md' -File)
$sourceCodexRoles = @(Get-ChildItem -LiteralPath $sourceCodexDir -Filter '*.md' -File)
$sourceCodexAgents = @(Get-ChildItem -LiteralPath $sourceCodexAgentDir -Filter '*.toml' -File)

if ($sourceAgents.Count -ne 23 -or $sourceCodexRoles.Count -ne 22 -or $sourceCodexAgents.Count -ne 22) {
    throw "El inventario del kit no coincide con lo esperado (OpenCode=$($sourceAgents.Count), roles Codex=$($sourceCodexRoles.Count), agentes Codex=$($sourceCodexAgents.Count))."
}

# Revisa todos los conflictos antes de copiar archivos.
$conflicts = @()
foreach ($source in @($sourceAgents + $sourceCodexRoles + $sourceCodexAgents)) {
    $destinationDir = switch ($source.DirectoryName) {
        $sourceAgentDir { $destOpenCodeDir; break }
        $sourceCodexDir { $destCodexDir; break }
        $sourceCodexAgentDir { $destCodexAgentDir; break }
        default { throw "Origen de perfil no reconocido: $($source.FullName)" }
    }
    $destination = Join-Path $destinationDir $source.Name
    if (Test-Path -LiteralPath $destination -PathType Leaf) {
        $sourceHash = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash
        $destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
        if ($sourceHash -ne $destinationHash) { $conflicts += $destination }
    }
}
if ($conflicts.Count -gt 0 -and -not $Force) {
    throw "Hay perfiles existentes con contenido distinto. No se sobrescribió nada. Revísalos y vuelve a ejecutar con -Force si deseas reemplazarlos: $($conflicts -join ', ')"
}

New-Item -ItemType Directory -Path $destOpenCodeDir -Force | Out-Null
New-Item -ItemType Directory -Path $destCodexDir -Force | Out-Null
New-Item -ItemType Directory -Path $destCodexAgentDir -Force | Out-Null
foreach ($source in $sourceAgents) {
    Copy-Item -LiteralPath $source.FullName -Destination (Join-Path $destOpenCodeDir $source.Name) -Force
}
foreach ($source in $sourceCodexRoles) {
    Copy-Item -LiteralPath $source.FullName -Destination (Join-Path $destCodexDir $source.Name) -Force
}
foreach ($source in $sourceCodexAgents) {
    Copy-Item -LiteralPath $source.FullName -Destination (Join-Path $destCodexAgentDir $source.Name) -Force
}

$openCodeConfig = Join-Path $targetRoot '.opencode\opencode.jsonc'
if (-not (Test-Path -LiteralPath $openCodeConfig)) {
    @'
{
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "directora"
}
'@ | Set-Content -LiteralPath $openCodeConfig -Encoding utf8
}

$agentsPath = Join-Path $targetRoot 'AGENTS.md'
$startMarker = '<!-- equipo-agentes:inicio -->'
$endMarker = '<!-- equipo-agentes:fin -->'
$template = Get-Content -LiteralPath (Join-Path $kitRoot 'templates\AGENTS-equipo.md') -Raw
$officeBlock = "$startMarker`r`n$template`r`n$endMarker"
if (Test-Path -LiteralPath $agentsPath -PathType Leaf) {
    $existing = Get-Content -LiteralPath $agentsPath -Raw
} else {
    $existing = ''
}
$hasStart = $existing.Contains($startMarker)
$hasEnd = $existing.Contains($endMarker)
if ($hasStart -xor $hasEnd) {
    throw "AGENTS.md tiene un marcador de oficina incompleto. Corrige '$agentsPath' antes de instalar."
}
if ($hasStart) {
    $startIndex = $existing.IndexOf($startMarker, [System.StringComparison]::Ordinal)
    $endIndex = $existing.IndexOf($endMarker, $startIndex, [System.StringComparison]::Ordinal) + $endMarker.Length
    $updated = $existing.Substring(0, $startIndex) + $officeBlock + $existing.Substring($endIndex)
} else {
    $updated = $existing.TrimEnd() + "`r`n`r`n$officeBlock`r`n"
}
Set-Content -LiteralPath $agentsPath -Value $updated -Encoding utf8

Write-Output "Equipo instalado en: $targetRoot"
Write-Output 'OpenCode: selecciona el agente directora en una sesión nueva.'
Write-Output 'Codex: AGENTS.md coordina y los perfiles TOML quedan disponibles en .codex/agents/.'
