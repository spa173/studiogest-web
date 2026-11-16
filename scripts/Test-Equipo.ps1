$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path -Parent $PSScriptRoot

$configPath = Join-Path $kitRoot 'opencode.jsonc'
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
if ($config.default_agent -ne 'directora') { throw 'La agente predeterminada debe ser directora.' }
if ($config.PSObject.Properties.Name -contains 'model') { throw 'El kit no debe fijar un modelo.' }

$requiredAgents = @('directora', 'desarrollo', 'diseno', 'diseno-web', 'marketing', 'social-contenido', 'finanzas', 'operaciones', 'legal', 'producto', 'arquitectura', 'ux-web', 'frontend-web', 'backend', 'calidad', 'seguridad', 'plataforma-devops', 'datos-ia', 'documentacion', 'experiencia-cliente', 'direccion-arte', 'movimiento', 'imagenes')
$agentFiles = @(Get-ChildItem -LiteralPath (Join-Path $kitRoot '.opencode\agents') -Filter '*.md' -File)
$actualAgents = @($agentFiles | ForEach-Object { $_.BaseName } | Sort-Object)
$expectedAgents = @($requiredAgents | Sort-Object)
if (Compare-Object $expectedAgents $actualAgents) { throw 'Los perfiles OpenCode no coinciden con el roster requerido.' }
foreach ($file in $agentFiles) {
    $body = Get-Content -LiteralPath $file.FullName -Raw
    if (-not $body.StartsWith("---`r`n") -and -not $body.StartsWith("---`n")) { throw "Falta frontmatter en $($file.Name)." }
    if ($body -notmatch '(?m)^mode: (primary|subagent|all)$') { throw "Modo inválido en $($file.Name)." }
    if ($body -match '(?im)^model:') { throw "No se debe fijar modelo en $($file.Name)." }
}

$codexRoles = @(Get-ChildItem -LiteralPath (Join-Path $kitRoot 'codex\roles') -Filter '*.md' -File)
if ($codexRoles.Count -ne 22) { throw "Se esperaban ocho departamentos y catorce especialistas para Codex; hay $($codexRoles.Count)." }
$codexAgentsDir = Join-Path $kitRoot '.codex\agents'
$codexAgents = @(Get-ChildItem -LiteralPath $codexAgentsDir -Filter '*.toml' -File -ErrorAction SilentlyContinue)
if ($codexAgents.Count -ne 22) { throw "Codex debe tener 22 perfiles TOML invocables; hay $($codexAgents.Count)." }
if (Compare-Object @($codexRoles.BaseName | Sort-Object) @($codexAgents.BaseName | Sort-Object)) {
    throw 'Los perfiles TOML de Codex no coinciden con los 22 prompts fuente.'
}
foreach ($agent in $codexAgents) {
    $toml = [System.IO.File]::ReadAllText($agent.FullName, [System.Text.Encoding]::UTF8)
    foreach ($field in @('name', 'description', 'developer_instructions')) {
        if ($toml -notmatch "(?m)^$field\s*=") { throw "Falta el campo TOML '$field' en $($agent.Name)." }
    }
    if ($toml -match '(?im)^model\s*=') { throw "No se debe fijar modelo en $($agent.Name)." }
    if ($toml -match 'PSPath|PSDrive|PSProvider|PSSnapIn') { throw "El TOML $($agent.Name) embebe metadatos de PowerShell; regenera con scripts\\Build-Codex-Agents.ps1." }
    if ($toml -match '(?m)^developer_instructions\s*=\s*"#') { } else { throw "El TOML $($agent.Name) no empieza developer_instructions por '#'; el generador está corrompiendo el contenido o la codificación." }
}
foreach ($md in @($agentFiles) + @(Get-ChildItem -LiteralPath (Join-Path $kitRoot 'codex\roles') -Filter '*.md' -File)) {
    $text = [System.IO.File]::ReadAllText($md.FullName, [System.Text.Encoding]::UTF8)
    if ($text -match 'Ã') { throw "Posible doble codificación (mojibake) en $($md.Name)." }
}

# Ensayo de instalación: conserva AGENTS.md, es idempotente y bloquea conflictos.
$sandbox = Join-Path ([System.IO.Path]::GetTempPath()) ("equipo-agentes-test-" + [guid]::NewGuid().ToString('N'))
$sandbox = [System.IO.Path]::GetFullPath($sandbox)
$tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
if (-not $sandbox.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "La carpeta temporal de validación quedó fuera de la ruta temporal esperada: $sandbox"
}
New-Item -ItemType Directory -Path $sandbox | Out-Null
try {
    Set-Content -LiteralPath (Join-Path $sandbox 'AGENTS.md') -Value "Regla previa del proyecto." -Encoding utf8
    & (Join-Path $kitRoot 'scripts\Install-Equipo.ps1') -Target $sandbox | Out-Null
    & (Join-Path $kitRoot 'scripts\Install-Equipo.ps1') -Target $sandbox | Out-Null
    $installedGuidance = Get-Content -LiteralPath (Join-Path $sandbox 'AGENTS.md') -Raw
    if (-not $installedGuidance.Contains('Regla previa del proyecto.')) { throw 'El instalador eliminó el AGENTS existente.' }
    if ([regex]::Matches($installedGuidance, [regex]::Escape('<!-- equipo-agentes:inicio -->')).Count -ne 1 -or
        [regex]::Matches($installedGuidance, [regex]::Escape('<!-- equipo-agentes:fin -->')).Count -ne 1) {
        throw 'La instalación duplicó o desbalanceó el bloque de reglas.'
    }
    if (@(Get-ChildItem -LiteralPath (Join-Path $sandbox '.codex\agents') -Filter '*.toml' -File).Count -ne 22) {
        throw 'La instalación no copió los 22 subagentes Codex.'
    }
    $conflictFile = Join-Path $sandbox '.opencode\agents\backend.md'
    Set-Content -LiteralPath $conflictFile -Value 'contenido de usuario' -Encoding utf8
    $conflictBlocked = $false
    try { & (Join-Path $kitRoot 'scripts\Install-Equipo.ps1') -Target $sandbox | Out-Null } catch { $conflictBlocked = $true }
    if (-not $conflictBlocked) { throw 'El instalador no bloqueó una sobrescritura sin -Force.' }
    if ((Get-Content -LiteralPath $conflictFile -Raw).Trim() -ne 'contenido de usuario') { throw 'El perfil en conflicto se modificó.' }
    $selfTargetBlocked = $false
    try { & (Join-Path $kitRoot 'scripts\Install-Equipo.ps1') -Target $kitRoot | Out-Null } catch { $selfTargetBlocked = $true }
    if (-not $selfTargetBlocked) { throw 'El instalador aceptó instalar dentro del propio kit.' }
} finally {
    Remove-Item -LiteralPath $sandbox -Recurse -Force
}

Write-Output 'VALIDACIÓN OK: 23 perfiles OpenCode y 22 subagentes Codex, ocho departamentos, modelo sin fijar, instalación idempotente y sin sobrescritura implícita.'
