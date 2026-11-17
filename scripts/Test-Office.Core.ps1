param([ValidateSet('Registry', 'Contracts', 'Roles', 'OpenCode', 'Codex', 'Compatibility', 'All')][string] $Section = 'All')
$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path -Parent $PSScriptRoot
function Assert-True($Condition, [string] $Message) { if (-not $Condition) { throw $Message } }
function Assert-Throws([scriptblock] $Action, [string] $Pattern) {
    $caught = $null
    try { & $Action } catch { $caught = $_.Exception.Message }
    Assert-True ($null -ne $caught -and $caught -match $Pattern) "Expected error '$Pattern'; got '$caught'."
}
function Copy-Value($Value) { $Value | ConvertTo-Json -Depth 30 | ConvertFrom-Json }
Assert-True (Test-Path (Join-Path $PSScriptRoot 'Office.Common.ps1')) 'Missing Office.Common.ps1 and canonical office registry.'
. (Join-Path $PSScriptRoot 'Office.Common.ps1')

if ($Section -in @('Compatibility', 'All')) {
    # Legacy commands must consume office/ even when the old prompt tree is absent.
    $sandbox = Join-Path ([IO.Path]::GetTempPath()) ('office-compatibility-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    try {
        foreach ($dir in @('office', 'scripts', 'templates')) { Copy-Item -LiteralPath (Join-Path $kitRoot $dir) -Destination $sandbox -Recurse }
        $build = Join-Path $sandbox 'scripts/Build-Codex-Agents.ps1'
        $test = Join-Path $sandbox 'scripts/Test-Equipo.ps1'
        & (Join-Path $sandbox 'scripts/Build-Office.ps1') -Platform Both | Out-Null
        $configPath = Join-Path $sandbox 'opencode.jsonc'
        $configBefore = [IO.File]::ReadAllText($configPath)
        $openCodePath = Join-Path $sandbox '.opencode/agents/backend.md'
        $openCodeBefore = [IO.File]::ReadAllText($openCodePath)
        $warnings = @()
        $result = @(& $test -Section Registry -WarningVariable warnings -WarningAction SilentlyContinue)
        Assert-True (($result -join "`n").Contains('PASS: 31 profiles; 4 contracts; 3 permission sets')) 'Legacy test did not run the canonical registry checks.'
        Assert-True (($warnings -join "`n") -match '(?i)depreca.*Test-Office.Core.ps1') 'Legacy test must name its replacement in a deprecation warning.'
        $registryPath = Join-Path $sandbox 'office/registry.json'
        $source = [IO.File]::ReadAllText($registryPath)
        $invalid = $source | ConvertFrom-Json
        $invalid.profiles[1].id = 'directora'
        [IO.File]::WriteAllText($registryPath, ($invalid | ConvertTo-Json -Depth 30))
        Assert-Throws { & $test -Section Registry -WarningAction SilentlyContinue } 'Expected unique IDs'
        [IO.File]::WriteAllText($registryPath, $source)
        $warnings = @()
        & $build -WarningVariable warnings -WarningAction SilentlyContinue | Out-Null
        Assert-True (($warnings -join "`n") -match '(?i)depreca.*Build-Office.ps1') 'Legacy build must name its replacement in a deprecation warning.'
        $agentDir = Join-Path $sandbox '.codex/agents'
        Assert-True (@(Get-ChildItem -LiteralPath $agentDir -Filter '*.toml' -File).Count -eq 30) 'Legacy build must generate thirty canonical Codex subagents.'
        Assert-True ([IO.File]::ReadAllText($configPath) -ceq $configBefore -and [IO.File]::ReadAllText($openCodePath) -ceq $openCodeBefore) 'Legacy Codex build changed OpenCode output.'
        $guidancePath = Join-Path $sandbox 'AGENTS.md'
        $guidance = [IO.File]::ReadAllText($guidancePath)
        Assert-True ([regex]::Matches($guidance, '<!-- oficina-unificada:inicio -->').Count -eq 1) 'Legacy build must generate one Director block.'
        & $build -Check -WarningAction SilentlyContinue | Out-Null
        $driftPath = Join-Path $agentDir 'backend.toml'
        [IO.File]::AppendAllText($driftPath, 'manual drift')
        Assert-Throws { & $build -Check -WarningAction SilentlyContinue } 'drift.*backend.toml'
        Assert-True ([IO.File]::ReadAllText($driftPath).EndsWith('manual drift')) 'Legacy check repaired drift instead of reporting it.'
        & $build -WarningAction SilentlyContinue | Out-Null
        & $build -Check -WarningAction SilentlyContinue | Out-Null
        Assert-True ([IO.File]::ReadAllText($guidancePath) -ceq $guidance) 'Legacy regeneration changed or duplicated Director guidance.'
    } finally {
        $resolved = [IO.Path]::GetFullPath($sandbox)
        $temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $resolved.StartsWith($temp, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe cleanup path.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    $readme = [IO.File]::ReadAllText((Join-Path $kitRoot 'README.md'))
    Assert-True ($readme.Contains('office/registry.json') -and $readme -match '(?i)fuente (canónica|única)') 'README must identify office/registry.json as the canonical source.'
    Write-Output 'PASS: legacy entrypoints delegate to office core; canonical source documented'
}

if ($Section -in @('OpenCode', 'All')) {
    $rendererPath = Join-Path $PSScriptRoot 'render/Render-OpenCodeAgent.ps1'
    Assert-True (Test-Path -LiteralPath $rendererPath) 'Missing OpenCode renderer.'
    . $rendererPath
    # This deliberately reads the emitted YAML subset, not renderer internals.
    function Read-OpenCodeAgent([string] $Text) {
        $match = [regex]::Match($Text, '\A---\n(?<header>.*?)\n---\n(?<body>.*)\z', 'Singleline')
        Assert-True $match.Success 'Invalid OpenCode frontmatter boundaries.'
        $header = $match.Groups['header'].Value
        Assert-True ($header -notmatch '(?im)^model\s*:') 'Generated agents must inherit their model.'
        $description = [regex]::Match($header, '(?m)^description: (?<value>.+)$')
        $mode = [regex]::Match($header, '(?m)^mode: (?<value>primary|subagent)$')
        $permissions = [regex]::Match($header, '(?ms)^permissions: (?<value>\[.*\])$')
        Assert-True ($description.Success -and $mode.Success -and $permissions.Success) 'Invalid OpenCode frontmatter fields.'
        [pscustomobject]@{
            description = ($description.Groups['value'].Value | ConvertFrom-Json)
            mode = $mode.Groups['value'].Value
            permissions = @($permissions.Groups['value'].Value | ConvertFrom-Json)
            body = $match.Groups['body'].Value
        }
    }
    function Get-OpenCodeEffect($Rules, [string] $Action, [string] $Resource) {
        $effect = 'ask'
        foreach ($rule in $Rules) {
            $matchesResource = $Resource -like $rule.resource -or ($rule.resource.EndsWith(' *') -and $Resource -eq $rule.resource.Substring(0, $rule.resource.Length - 2))
            if ($Action -like $rule.action -and $matchesResource) { $effect = $rule.effect }
        }
        $effect
    }
    $registry = Get-OfficeRegistry $kitRoot
    Assert-OfficeRegistry $registry $kitRoot
    $routes = @{
        directora = 'coord-producto-experiencia,coord-ingenieria-datos,coord-calidad-seguridad,coord-operaciones-entrega,coord-negocio-gobernanza'
        'coord-producto-experiencia' = 'producto,diseno-web,ux-accesibilidad,seo-growth,data-analytics'
        'coord-ingenieria-datos' = 'arquitectura,frontend,backend,mobile,datos-ia,integraciones'
        'coord-calidad-seguridad' = 'qa,seguridad,auditoria,rendimiento'
        'coord-operaciones-entrega' = 'devops,sre-observabilidad,forensics,release,documentacion'
        'coord-negocio-gobernanza' = 'marketing,social-contenido,finanzas,legal,experiencia-cliente'
    }
    $sandbox = Join-Path ([IO.Path]::GetTempPath()) ('office-opencode-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    try {
        Copy-Item -LiteralPath (Join-Path $kitRoot 'office') -Destination $sandbox -Recurse
        Copy-Item -LiteralPath $PSScriptRoot -Destination $sandbox -Recurse
        $agentDir = Join-Path $sandbox '.opencode/agents'
        New-Item -ItemType Directory -Path (Join-Path $agentDir 'custom') -Force | Out-Null
        $unknown = Join-Path $agentDir 'custom/keep.md'
        [IO.File]::WriteAllText($unknown, 'user-owned: análisis')
        $unknownFlat = Join-Path $agentDir 'custom-agent.md'
        [IO.File]::WriteAllText($unknownFlat, 'user-owned flat profile')
        $obsolete = @('directora', 'desarrollo', 'diseno', 'diseno-web', 'marketing', 'social-contenido', 'finanzas', 'operaciones', 'legal', 'producto', 'arquitectura', 'ux-web', 'frontend-web', 'backend', 'calidad', 'seguridad', 'plataforma-devops', 'datos-ia', 'documentacion', 'experiencia-cliente', 'direccion-arte', 'movimiento', 'imagenes')
        foreach ($id in $obsolete) { [IO.File]::WriteAllText((Join-Path $agentDir "$id.md"), 'old generated profile') }
        $configPath = Join-Path $sandbox 'opencode.jsonc'
        $configFixture = @'
{
  // User settings survive merging, including trailing commas and URL strings.
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "other",
  "theme": "custom",
  "mcp": {"local": {"url": "https://example.test//path", "enabled": false}},
  "experimental": {"subagent_depth": 1, "keep": {"enabled": true},},
}
'@
        [IO.File]::WriteAllText($configPath, $configFixture)
        $build = Join-Path $sandbox 'scripts/Build-Office.ps1'
        Assert-Throws { & $build -Platform OpenCode -Check } 'drift'
        Assert-True ([IO.File]::ReadAllText($configPath) -ceq $configFixture) 'Check changed configuration.'
        Assert-True ([IO.File]::ReadAllText((Join-Path $agentDir 'diseno.md')) -ceq 'old generated profile') 'Check removed obsolete output.'
        & $build -Platform OpenCode | Out-Null
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $sandbox '.codex')) -and -not (Test-Path -LiteralPath (Join-Path $sandbox 'AGENTS.md'))) 'OpenCode build wrote Codex output.'
        $files = @(Get-ChildItem -LiteralPath $agentDir -File -Filter '*.md' | Where-Object BaseName -CIn $registry.profiles.id)
        Assert-True ($files.Count -eq 31) 'Expected 31 flat OpenCode agents.'
        Assert-True ([IO.File]::ReadAllText($unknown) -ceq 'user-owned: análisis') 'Build pruned an unknown nested file.'
        Assert-True ([IO.File]::ReadAllText($unknownFlat) -ceq 'user-owned flat profile') 'Build pruned an unknown flat file.'
        foreach ($id in $obsolete | Where-Object { $_ -cnotin $registry.profiles.id }) {
            Assert-True (-not (Test-Path -LiteralPath (Join-Path $agentDir "$id.md"))) "Obsolete output remains: $id."
        }
        $primaryCount = 0
        foreach ($role in $registry.profiles) {
            $path = Join-Path $agentDir "$($role.id).md"
            $bytes = [IO.File]::ReadAllBytes($path)
            $strictUtf8 = [Text.UTF8Encoding]::new($false, $true)
            $text = $strictUtf8.GetString($bytes)
            Assert-True (-not ($bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191)) 'Output must be UTF-8 without BOM.'
            $agent = Read-OpenCodeAgent $text
            Assert-True ($agent.description -ceq $role.description) "Description did not round-trip for $($role.id)."
            $expectedMode = if ($role.id -eq 'directora') { 'primary' } else { 'subagent' }
            Assert-True ($agent.mode -eq $expectedMode) "Incorrect mode for $($role.id)."
            if ($agent.mode -eq 'primary') { $primaryCount++ }
            Assert-True ($agent.body.Contains('GENERATED') -and $agent.body.Contains('office/registry.json') -and $agent.body.Contains($role.prompt) -and $agent.body.Contains("office/permission-sets/$($role.permission_set).json")) "Canonical-source header missing for $($role.id)."
            Assert-True ($agent.body.Contains(((Get-OfficeRolePrompt $role $kitRoot) -replace "`r`n", "`n").TrimEnd())) "Canonical prompt differs for $($role.id)."
            $children = if ($routes.ContainsKey($role.id)) { @($routes[$role.id] -split ',') } else { @() }
            $subagentRules = @($agent.permissions | Where-Object action -CEQ 'subagent')
            Assert-True ($subagentRules.Count -eq (1 + $children.Count) -and $subagentRules[0].resource -eq '*' -and $subagentRules[0].effect -eq 'deny') "Delegation deny missing or allowlist expanded for $($role.id)."
            $allows = @($subagentRules | Where-Object effect -CEQ 'allow' | Select-Object -ExpandProperty resource)
            Assert-True ((($allows | Sort-Object) -join ',') -ceq (($children | Sort-Object) -join ',')) "Incorrect exact allowlist for $($role.id)."
            foreach ($target in @('general', 'explore', 'custom/keep') + @($registry.profiles.id)) {
                $want = if ($target -cin $children) { 'allow' } else { 'deny' }
                Assert-True ((Get-OpenCodeEffect $agent.permissions subagent $target) -eq $want) "Incorrect delegation to $target from $($role.id)."
            }
            foreach ($rule in $agent.permissions) {
                Assert-True ($rule.action -is [string] -and $rule.resource -is [string] -and $rule.effect -cin @('allow', 'deny', 'ask')) 'Invalid V2 permission rule.'
            }
            Assert-True ((Get-OpenCodeEffect $agent.permissions read 'src/main.ps1') -eq 'allow') 'Local reading must be allowed.'
            Assert-True ((Get-OpenCodeEffect $agent.permissions glob '*.ps1') -eq 'allow') 'Native glob must remain available.'
            # OpenCode authorizes grep against the search expression, not each
            # matched path. Approval must therefore apply to every expression
            # until the tool exposes per-file permission checks.
            $grepExpression = 'DATABASE_URL\s*='
            Assert-True ((Get-OpenCodeEffect $agent.permissions grep $grepExpression) -eq 'ask') 'Native grep must ask for the real expression resource.'
            # Inspection tools accept options that write files, execute programs or
            # read secrets; a shell prefix alone cannot prove read-only behavior.
            $unsafeInspection = @('git diff --output=src/main.ps1', 'rg --pre=./preprocessor.exe pattern README.md', 'Get-Content .env')
            $unconditionallyAllowed = @($unsafeInspection | Where-Object { (Get-OpenCodeEffect $agent.permissions shell $_) -eq 'allow' })
            Assert-True ($unconditionallyAllowed.Count -eq 0) "Inspection arguments bypass permissions for $($role.id): $($unconditionallyAllowed -join '; ')."
            $webEffect = if ('web_research' -cin $role.capabilities) { 'allow' } else { 'deny' }
            Assert-True ((Get-OpenCodeEffect $agent.permissions webfetch 'https://example.test') -eq $webEffect -and (Get-OpenCodeEffect $agent.permissions websearch 'references') -eq $webEffect) 'Web access must follow the role capability.'
            Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'git status --short') -eq 'ask') 'Shell inspection requires approval for its complete arguments.'
            $isReadonly = $role.permission_set -eq 'readonly'
            $externalEffect = if ($isReadonly) { 'deny' } else { 'ask' }
            Assert-True ((Get-OpenCodeEffect $agent.permissions external_directory 'C:/outside/*') -eq $externalEffect) 'Outside-workspace access bypassed policy.'
            Assert-True ((Get-OpenCodeEffect $agent.permissions read '.env') -eq 'ask') 'Credential reads must require authorization.'
            Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'git push origin main') -eq $externalEffect) 'Push must require external-write authorization.'
            Assert-True ((Get-OpenCodeEffect $agent.permissions github_create_issue '*') -eq $externalEffect) 'MCP writes must not inherit a broad allow.'
            $editEffect = if ($isReadonly) { 'deny' } else { 'allow' }
            Assert-True ((Get-OpenCodeEffect $agent.permissions edit 'docs/guide.md') -eq $editEffect) 'Incorrect workspace edit policy.'
            Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'Remove-Item -Recurse src') -ne 'allow') 'Destructive commands must not be allowed.'
            if ($isReadonly) {
                Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'node arbitrary.js') -eq 'deny') 'Readonly allowed general shell.'
            } elseif ($role.permission_set -eq 'implementer') {
                Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'npm run build') -eq 'allow') 'Implementer builds denied.'
                Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'npm test') -eq 'allow') 'Implementer tests denied.'
                Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'npm install package') -eq 'ask') 'Dependency installation must ask.'
            }
            if ($role.id -eq 'documentacion') { Assert-True ((Get-OpenCodeEffect $agent.permissions edit 'src/main.ps1') -eq 'deny') 'Documentation role may edit only documents.' }
            if ($role.id -eq 'qa') { Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'npm test') -eq 'ask') 'QA suites require task authorization.' }
            if ($role.permission_set -eq 'operator') {
                Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'kubectl get pods') -eq 'ask') 'Shell diagnostics require approval for their complete arguments.'
                Assert-True ((Get-OpenCodeEffect $agent.permissions shell 'kubectl apply -f prod.yaml') -eq 'ask') 'Infrastructure changes must require authorization.'
            }
        }
        Assert-True ($primaryCount -eq 1) 'Expected exactly one primary Director.'
        $config = [IO.File]::ReadAllText($configPath) | ConvertFrom-Json
        Assert-True (-not [IO.File]::ReadAllText($configPath).Contains("`r")) 'Configuration must use stable LF line endings.'
        Assert-True ($config.default_agent -eq 'directora' -and $config.experimental.subagent_depth -eq 2) 'Missing two-hop configuration.'
        Assert-True ($config.theme -eq 'custom' -and $config.experimental.keep.enabled -eq $true -and $config.mcp.local.url -ceq 'https://example.test//path' -and $config.mcp.local.enabled -eq $false) 'Build lost unrelated configuration.'
        $snapshot = @{}
        foreach ($path in @($files.FullName) + $configPath + $unknown + $unknownFlat) { $snapshot[$path] = [Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) }
        & $build -Platform OpenCode | Out-Null
        & $build -Platform OpenCode -Check | Out-Null
        foreach ($path in $snapshot.Keys) { Assert-True ([Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) -ceq $snapshot[$path]) "Generation is not byte-identical: $path." }
        $driftPath = Join-Path $agentDir 'backend.md'
        [IO.File]::AppendAllText($driftPath, 'manual drift')
        $driftBytes = [Convert]::ToBase64String([IO.File]::ReadAllBytes($driftPath))
        Assert-Throws { & $build -Platform OpenCode -Check } 'drift.*backend.md'
        Assert-True ([Convert]::ToBase64String([IO.File]::ReadAllBytes($driftPath)) -ceq $driftBytes) 'Check repaired drift instead of failing without writing.'
        # Direct renderer boundary exercises quoting, Unicode and multiline prompts.
        $role = Copy-Value $registry.profiles[0]
        $role.description = 'Descripción: "línea" # comentario'
        $role | Add-Member allowed_subagents @('coord-producto-experiencia')
        $permission = Get-Content -LiteralPath (Join-Path $kitRoot 'office/permission-sets/readonly.json') -Raw | ConvertFrom-Json
        $rendered = Read-OpenCodeAgent (ConvertTo-OpenCodeAgent $role "# Análisis`r`nTexto: \" $permission)
        Assert-True ($rendered.description -ceq $role.description -and $rendered.body.Contains("# Análisis`nTexto: \")) 'Renderer lost escaped or multiline content.'
    } finally {
        $resolved = [IO.Path]::GetFullPath($sandbox)
        $temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $resolved.StartsWith($temp, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe cleanup path.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    & (Join-Path $PSScriptRoot 'Build-Office.ps1') -Platform OpenCode -Check | Out-Null
    Write-Output 'PASS: 31 OpenCode agents; exact delegation; permission translation; UTF-8; idempotence; zero drift'
}

if ($Section -in @('Codex', 'All')) {
    $rendererPath = Join-Path $PSScriptRoot 'render/Render-CodexAgent.ps1'
    Assert-True (Test-Path -LiteralPath $rendererPath) 'Missing Codex renderer.'
    . $rendererPath
    # Read only the generated TOML subset: comments and JSON-escaped basic strings.
    function Read-CodexAgent([string] $Text) {
        $fields = @{}
        foreach ($line in $Text -split "`n") {
            if ($line -match '^#' -or $line -eq '') { continue }
            $match = [regex]::Match($line, '^(?<key>name|description|developer_instructions) = (?<value>".*")$')
            Assert-True ($match.Success -and -not $fields.ContainsKey($match.Groups['key'].Value)) 'Invalid or unexpected Codex TOML field.'
            $fields[$match.Groups['key'].Value] = $match.Groups['value'].Value | ConvertFrom-Json
        }
        Assert-True ($fields.Count -eq 3) 'Expected exactly three Codex fields, with inherited model and permissions.'
        [pscustomobject] $fields
    }
    $tomlParser = Get-Command python -ErrorAction SilentlyContinue
    Assert-True ($null -ne $tomlParser) 'Python with stdlib tomllib is required for real TOML compatibility checks.'
    function Read-CodexToml([string] $Path) {
        $python = 'import json, sys, tomllib; print(json.dumps(tomllib.load(open(sys.argv[1], "rb")), ensure_ascii=True))'
        $output = @(& $tomlParser.Source -c $python $Path 2>&1)
        $exitCode = $LASTEXITCODE
        Assert-True ($exitCode -eq 0) "Real TOML parser rejected '$Path': $($output -join "`n")"
        ($output -join "`n") | ConvertFrom-Json
    }
    $start = '<!-- oficina-unificada:inicio -->'
    $end = '<!-- oficina-unificada:fin -->'
    $block = "$start`nNuevo bloque`n$end"
    $prefix = "# Reglas privadas`r`nEspacios finales  `r`n"
    $suffix = "`r`n# Después`r`nConservar  "
    $existing = $prefix + "$start`r`nViejo bloque`r`n$end" + $suffix
    $updated = Set-ManagedInstructionBlock $existing $block
    Assert-True ($updated -ceq ($prefix + $block + $suffix)) 'Managed replacement lost prefix/suffix bytes.'
    Assert-True ((Set-ManagedInstructionBlock $updated $block) -ceq $updated) 'Managed replacement is not idempotent.'
    Assert-True ((Set-ManagedInstructionBlock '' $block) -ceq "$block`n") 'Empty AGENTS must contain exactly one block.'
    $appended = Set-ManagedInstructionBlock $prefix $block
    Assert-True ($appended.StartsWith($prefix, [StringComparison]::Ordinal) -and $appended.Contains($block)) 'Append trimmed existing instructions.'
    Assert-True ((Set-ManagedInstructionBlock $appended $block) -ceq $appended) 'Append duplicated the managed block.'
    foreach ($invalid in @($start, $end, "$end`n$start", "$block`n$block", "$start$start$end", "$start$end$end")) {
        Assert-Throws { Set-ManagedInstructionBlock $invalid $block } 'marker'
        Assert-Throws { Set-ManagedInstructionBlock '' $invalid } 'marker'
    }
    $registry = Get-OfficeRegistry $kitRoot
    Assert-OfficeRegistry $registry $kitRoot
    $roles = @($registry.profiles | Where-Object kind -CNE 'director')
    $sandbox = Join-Path ([IO.Path]::GetTempPath()) ('office-codex-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    try {
        foreach ($dir in @('office', 'scripts', 'templates')) { Copy-Item -LiteralPath (Join-Path $kitRoot $dir) -Destination $sandbox -Recurse }
        $build = Join-Path $sandbox 'scripts/Build-Office.ps1'
        $agentDir = Join-Path $sandbox '.codex/agents'
        New-Item -ItemType Directory -Path (Join-Path $agentDir 'custom') -Force | Out-Null
        $unknown = Join-Path $agentDir 'custom/keep.toml'
        $unknownFlat = Join-Path $agentDir 'custom-agent.toml'
        foreach ($path in @($unknown, $unknownFlat)) { [IO.File]::WriteAllText($path, 'user-owned: análisis') }
        $legacy = @('desarrollo', 'diseno', 'diseno-web', 'marketing', 'social-contenido', 'finanzas', 'operaciones', 'legal', 'producto', 'arquitectura', 'ux-web', 'frontend-web', 'backend', 'calidad', 'seguridad', 'plataforma-devops', 'datos-ia', 'documentacion', 'experiencia-cliente', 'direccion-arte', 'movimiento', 'imagenes')
        foreach ($id in $legacy) { [IO.File]::WriteAllText((Join-Path $agentDir "$id.toml"), 'old generated profile') }
        $agentsPath = Join-Path $sandbox 'AGENTS.md'
        [IO.File]::WriteAllText($agentsPath, $existing)
        $configPath = Join-Path $sandbox 'opencode.jsonc'
        [IO.File]::WriteAllText($configPath, '{"theme":"user-setting"}')
        Assert-Throws { & $build -Platform Codex -Check } 'drift'
        Assert-True ([IO.File]::ReadAllText($agentsPath) -ceq $existing -and [IO.File]::ReadAllText((Join-Path $agentDir 'diseno.toml')) -ceq 'old generated profile') 'Check changed instructions or obsolete output.'
        & $build -Platform Codex | Out-Null
        Assert-True ([IO.File]::ReadAllText($configPath) -ceq '{"theme":"user-setting"}' -and -not (Test-Path -LiteralPath (Join-Path $sandbox '.opencode'))) 'Codex build wrote OpenCode output.'
        $files = @(Get-ChildItem -LiteralPath $agentDir -File -Filter '*.toml' | Where-Object BaseName -CIn $roles.id)
        Assert-True ($files.Count -eq 30 -and -not (Test-Path -LiteralPath (Join-Path $agentDir 'directora.toml'))) 'Expected thirty non-Director Codex agents.'
        foreach ($id in $legacy | Where-Object { $_ -cnotin $roles.id }) {
            Assert-True (-not (Test-Path -LiteralPath (Join-Path $agentDir "$id.toml"))) "Obsolete Codex output remains: $id."
        }
        foreach ($path in @($unknown, $unknownFlat)) { Assert-True ([IO.File]::ReadAllText($path) -ceq 'user-owned: análisis') 'Build pruned unknown TOML.' }
        foreach ($role in $roles) {
            $bytes = [IO.File]::ReadAllBytes((Join-Path $agentDir "$($role.id).toml"))
            $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes)
            Assert-True (-not ($bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) -and -not $text.Contains("`r")) 'Codex output must be UTF-8 without BOM and use LF.'
            $agent = Read-CodexAgent $text
            $tomlAgent = Read-CodexToml (Join-Path $agentDir "$($role.id).toml")
            Assert-True ($agent.name -ceq $role.id -and $agent.description -ceq $role.description) "Codex identity did not round-trip: $($role.id)."
            Assert-True ($tomlAgent.name -ceq $role.id -and $tomlAgent.description -ceq $role.description) "Real TOML parser lost Codex identity: $($role.id)."
            Assert-True ($agent.developer_instructions -ceq ((Get-OfficeRolePrompt $role $kitRoot) -replace "`r`n", "`n")) "Canonical Codex prompt differs: $($role.id)."
            Assert-True ($text.StartsWith('# GENERATED:') -and $text.Contains('office/registry.json') -and $text.Contains($role.prompt)) "Canonical-source header missing: $($role.id)."
        }
        $guidance = [IO.File]::ReadAllText($agentsPath)
        Assert-True ($guidance.StartsWith($prefix, [StringComparison]::Ordinal) -and $guidance.EndsWith($suffix, [StringComparison]::Ordinal)) 'Build lost prefix/suffix instructions.'
        Assert-True ([regex]::Matches($guidance, [regex]::Escape($start)).Count -eq 1 -and [regex]::Matches($guidance, [regex]::Escape($end)).Count -eq 1) 'Director block missing or duplicated.'
        Assert-True ($guidance.Contains('office/registry.json') -and $guidance.Contains('office/roles/directora.md') -and $guidance.Contains('templates/AGENTS-oficina.md')) 'Director block lacks canonical-source header.'
        Assert-True ($guidance.Contains(((Get-OfficeRolePrompt ($registry.profiles | Where-Object id -CEQ 'directora') $kitRoot) -replace "`r`n", "`n").TrimEnd())) 'Director canonical prompt missing.'
        $snapshot = @{}
        foreach ($path in @($files.FullName) + $agentsPath + $unknown + $unknownFlat) { $snapshot[$path] = [Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) }
        & $build -Platform Codex | Out-Null
        & $build -Platform Codex -Check | Out-Null
        & $build -Platform Both | Out-Null
        & $build -Platform Both -Check | Out-Null
        Assert-True (@(Get-ChildItem -LiteralPath (Join-Path $sandbox '.opencode/agents') -File -Filter '*.md').Count -eq 31) 'Both did not generate OpenCode agents.'
        foreach ($path in $snapshot.Keys) { Assert-True ([Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) -ceq $snapshot[$path]) "Codex/Both generation is not byte-identical: $path." }
        $driftPath = Join-Path $agentDir 'backend.toml'
        [IO.File]::AppendAllText($driftPath, 'manual drift')
        Assert-Throws { & $build -Platform Codex -Check } 'drift.*backend.toml'
        Assert-True ([IO.File]::ReadAllText($driftPath).EndsWith('manual drift')) 'Check repaired Codex drift.'
        & $build -Platform Codex | Out-Null
        [IO.File]::WriteAllText((Join-Path $agentDir 'diseno.toml'), 'obsolete drift')
        Assert-Throws { & $build -Platform Codex -Check } 'drift.*diseno.toml'
        Assert-True (Test-Path -LiteralPath (Join-Path $agentDir 'diseno.toml')) 'Check removed obsolete drift.'
        & $build -Platform Codex | Out-Null
        [IO.File]::WriteAllText($agentsPath, $prefix)
        Assert-Throws { & $build -Platform Codex -Check } 'drift.*AGENTS.md'
        Assert-True ([IO.File]::ReadAllText($agentsPath) -ceq $prefix) 'Check repaired Director guidance.'
        [IO.File]::WriteAllText($agentsPath, $start)
        $before = [IO.File]::ReadAllText($driftPath)
        [IO.File]::WriteAllText($configPath, '{"theme":"before-failure"}')
        Assert-Throws { & $build -Platform Both } 'marker'
        Assert-True ([IO.File]::ReadAllText($driftPath) -ceq $before -and [IO.File]::ReadAllText($configPath) -ceq '{"theme":"before-failure"}' -and [IO.File]::ReadAllText($agentsPath) -ceq $start) 'Failed Both build partially wrote output.'
        $role = Copy-Value $roles[0]
        $role.description = 'Descripción: "línea" # comentario'
        $prompt = "# Análisis`r`nComillas: `"`"`"; ruta: C:\carpeta; tab:`tfin`nDEL:" + [char] 0x7f + "`n"
        $renderedToml = ConvertTo-CodexAgentToml $role $prompt
        $agent = Read-CodexAgent $renderedToml
        $compatibilityPath = Join-Path $sandbox 'codex-del-compatibility.toml'
        [IO.File]::WriteAllText($compatibilityPath, $renderedToml, [Text.UTF8Encoding]::new($false))
        $tomlAgent = Read-CodexToml $compatibilityPath
        Assert-True ($renderedToml.Contains('\u007f')) 'Codex renderer must escape U+007F for TOML compatibility.'
        Assert-True ($agent.description -ceq $role.description -and $agent.developer_instructions -ceq ($prompt -replace "`r`n", "`n")) 'Codex renderer lost quoted, multiline, Unicode or control content.'
        Assert-True ($tomlAgent.developer_instructions -ceq ($prompt -replace "`r`n", "`n")) 'Real TOML parser did not round-trip U+007F content.'
        Assert-Throws { ConvertTo-CodexAgentToml ($registry.profiles | Where-Object id -CEQ 'directora') '# Director' } 'Director'
    } finally {
        $resolved = [IO.Path]::GetFullPath($sandbox)
        $temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $resolved.StartsWith($temp, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe cleanup path.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    & (Join-Path $PSScriptRoot 'Build-Office.ps1') -Platform Codex -Check | Out-Null
    Write-Output 'PASS: 30 Codex subagents; Director block valid; zero drift'
}

if ($Section -in @('Roles', 'All')) {
    # Literal roster pins identity and ownership: a consistent rename or move is a regression.
    $expectedRoles = @'
directora||direccion|orquestación|release
coord-producto-experiencia|directora|producto-experiencia|producto y experiencia|product
producto|coord-producto-experiencia|producto-experiencia|alcance|product
diseno-web|coord-producto-experiencia|producto-experiencia|dirección de arte|design
ux-accesibilidad|coord-producto-experiencia|producto-experiencia|accesibilidad|design
seo-growth|coord-producto-experiencia|producto-experiencia|indexación|product
data-analytics|coord-producto-experiencia|producto-experiencia|métricas|product
coord-ingenieria-datos|directora|ingenieria-datos|ingeniería y datos|implementation
arquitectura|coord-ingenieria-datos|ingenieria-datos|contratos técnicos|implementation
frontend|coord-ingenieria-datos|ingenieria-datos|cliente web|implementation
backend|coord-ingenieria-datos|ingenieria-datos|servidor|implementation
mobile|coord-ingenieria-datos|ingenieria-datos|aplicaciones móviles|implementation
datos-ia|coord-ingenieria-datos|ingenieria-datos|pipelines|implementation
integraciones|coord-ingenieria-datos|ingenieria-datos|sistemas externos|implementation
coord-calidad-seguridad|directora|calidad-seguridad|calidad y seguridad|qa
qa|coord-calidad-seguridad|calidad-seguridad|pruebas|qa
seguridad|coord-calidad-seguridad|calidad-seguridad|seguridad técnica|security
auditoria|coord-calidad-seguridad|calidad-seguridad|controles|qa
rendimiento|coord-calidad-seguridad|calidad-seguridad|rendimiento|qa
coord-operaciones-entrega|directora|operaciones-entrega|operaciones y entrega|release
devops|coord-operaciones-entrega|operaciones-entrega|plataforma|release
sre-observabilidad|coord-operaciones-entrega|operaciones-entrega|fiabilidad|post_deploy
forensics|coord-operaciones-entrega|operaciones-entrega|incidentes|security
release|coord-operaciones-entrega|operaciones-entrega|entregas|release
documentacion|coord-operaciones-entrega|operaciones-entrega|documentación|documentation
coord-negocio-gobernanza|directora|negocio-gobernanza|negocio y gobernanza|product
marketing|coord-negocio-gobernanza|negocio-gobernanza|posicionamiento|product
social-contenido|coord-negocio-gobernanza|negocio-gobernanza|contenido editorial|product
finanzas|coord-negocio-gobernanza|negocio-gobernanza|presupuestos|product
legal|coord-negocio-gobernanza|negocio-gobernanza|privacidad legal|security
experiencia-cliente|coord-negocio-gobernanza|negocio-gobernanza|soporte|product
'@ | ConvertFrom-Csv -Delimiter '|' -Header id, parent, department, domain, gate
    $registry = Get-OfficeRegistry -Root $kitRoot
    Assert-True ((($registry.profiles.id | Sort-Object) -join ',') -ceq (($expectedRoles.id | Sort-Object) -join ',')) 'Canonical role IDs differ.'
    foreach ($expected in $expectedRoles) {
        $role = @($registry.profiles | Where-Object id -CEQ $expected.id)[0]
        Assert-True ([string] $role.parent -ceq $expected.parent -and $role.department -ceq $expected.department) "Canonical parent/department differs for $($expected.id)."
        $kind = if ($expected.id -eq 'directora') { 'director' } elseif ($expected.parent -eq 'directora') { 'coordinator' } else { 'specialist' }
        Assert-True ($role.kind -ceq $kind -and $role.prompt -ceq "office/roles/$($expected.id).md") "Canonical kind/prompt differs for $($expected.id)."
    }
    $missing = @($registry.profiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $kitRoot $_.prompt) -PathType Leaf) })
    Assert-True ($missing.Count -eq 0) "Missing role files: $($missing.prompt -join ', ')."
    Assert-OfficeRegistry $registry $kitRoot
    Assert-True ($null -ne (Get-Command Get-OfficeRolePrompt -ErrorAction SilentlyContinue)) 'Missing Get-OfficeRolePrompt.'
    foreach ($expected in $expectedRoles) {
        $role = @($registry.profiles | Where-Object id -CEQ $expected.id)[0]
        $prompt = Get-OfficeRolePrompt $role $kitRoot
        Assert-True ($prompt -is [string]) "Prompt must be a string for $($role.id)."
        $escalateTo = if ($expected.parent) { $expected.parent } else { 'humano' }
        Assert-True ($prompt -match ('(?m)^Departamento: ' + [regex]::Escape($expected.department) + '\r?$')) "Prompt department differs for $($role.id)."
        Assert-True ($prompt -match ('(?m)^Escalado a: ' + [regex]::Escape($escalateTo) + '\r?$')) "Prompt escalation route differs for $($role.id)."
        $sections = @{}
        foreach ($heading in @('Dominio propio', 'Límites', 'Salida esperada', 'Gate', 'Escalado', 'Evidencia')) {
            $match = [regex]::Match($prompt, '(?ms)^## ' + [regex]::Escape($heading) + '\r?\n(?<body>.+?)(?=^## |\z)')
            Assert-True ($match.Success -and $match.Groups['body'].Value.Trim().Length -ge 30) "Missing substantive '$heading' for $($role.id)."
            $sections[$heading] = $match.Groups['body'].Value
        }
        Assert-True ($sections['Dominio propio'] -match [regex]::Escape($expected.domain)) "Owned domain differs for $($role.id)."
        Assert-True ($sections['Límites'] -match '(?i)no ') "Forbidden adjacent domains missing for $($role.id)."
        Assert-True ($sections['Salida esperada'] -match 'handoff') "Expected handoff output missing for $($role.id)."
        foreach ($field in @('from', 'to', 'task_id', 'context_summary', 'scope', 'artifacts', 'evidence', 'gate_status', 'risks', 'next_action')) {
            Assert-True ($sections['Salida esperada'] -match ('\b' + $field + '\b')) "Missing handoff.$field for $($role.id)."
        }
        Assert-True ($sections['Gate'] -match ('\b' + $expected.gate + '\b') -and $sections['Gate'] -match 'pending.*pass.*fail.*waived') "Gate policy differs for $($role.id)."
        Assert-True ($sections['Escalado'] -match 'escalation' -and $sections['Escalado'] -match 'humano') "Human escalation missing for $($role.id)."
        Assert-True ($sections['Evidencia'] -match 'evidence' -and $sections['Evidencia'] -match 'comando|fuente|artefacto') "Evidence requirement missing for $($role.id)."
        $route = [regex]::Match($prompt, '(?m)^Delegación permitida: (?<ids>[^\r\n]+)\r?$')
        Assert-True $route.Success "Missing explicit routing for $($role.id)."
        $actualChildren = if ($route.Groups['ids'].Value -eq 'ninguna') { @() } else { @($route.Groups['ids'].Value -split ',\s*') }
        $expectedChildren = @($expectedRoles | Where-Object parent -CEQ $role.id | Select-Object -ExpandProperty id)
        Assert-True ((($actualChildren | Sort-Object) -join ',') -ceq (($expectedChildren | Sort-Object) -join ',')) "Forbidden delegation route for $($role.id)."
        foreach ($skill in $role.skills) {
            Assert-True ($prompt.Contains($skill)) "Missing method skill '$skill' for $($role.id)."
        }
    }
    # Exercise the actual loader boundary, including a caller-supplied root.
    $sandbox = Join-Path ([IO.Path]::GetTempPath()) ('office-role-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    try {
        Set-Content -LiteralPath (Join-Path $sandbox 'role.md') -Value "# Prueba de raíz`nDominio: análisis" -NoNewline -Encoding utf8
        Assert-True ((Get-OfficeRolePrompt ([pscustomobject]@{ prompt = 'role.md' }) $sandbox) -ceq "# Prueba de raíz`nDominio: análisis") 'Loader must return UTF-8 text from the supplied root.'
        Assert-Throws { Get-OfficeRolePrompt ([pscustomobject]@{ prompt = '../outside.md' }) $sandbox } 'outside'
        Assert-Throws { Get-OfficeRolePrompt ([pscustomobject]@{ prompt = (Join-Path $sandbox 'role.md') }) $sandbox } 'outside'
        Assert-Throws { Get-OfficeRolePrompt ([pscustomobject]@{ prompt = 'missing.md' }) $sandbox } 'Missing prompt'
        Assert-Throws { Get-OfficeRolePrompt ([pscustomobject]@{ prompt = ' ' }) $sandbox } 'Invalid prompt'
    } finally {
        $resolved = [IO.Path]::GetFullPath($sandbox)
        $temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $resolved.StartsWith($temp, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe cleanup path.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    Write-Output 'PASS: 31 prompts; routing graph valid'
}

if ($Section -in @('Registry', 'All')) {
    $registry = Get-OfficeRegistry -Root $kitRoot
    Assert-True (@($registry.profiles).Count -eq 31) 'Expected 31 profiles.'
    Assert-True (@($registry.profiles.id | Sort-Object -Unique).Count -eq 31) 'Expected unique IDs.'
    Assert-True (@($registry.profiles | Where-Object kind -eq director).Count -eq 1) 'Expected one Director.'
    Assert-True (@($registry.profiles | Where-Object kind -eq coordinator).Count -eq 5) 'Expected five coordinators.'
    Assert-True (@($registry.profiles | Where-Object kind -eq specialist).Count -eq 25) 'Expected 25 specialists.'
    $permissionFiles = @(Get-ChildItem -LiteralPath (Join-Path $kitRoot 'office/permission-sets') -Filter '*.json' -File)
    Assert-True ($permissionFiles.Count -eq 3) 'Expected three permission sets.'
    $readonly = Get-Content -LiteralPath (Join-Path $kitRoot 'office/permission-sets/readonly.json') -Raw | ConvertFrom-Json
    Assert-True ($readonly.permissions.edit -eq 'deny' -and $readonly.permissions.shell -eq 'deny' -and $readonly.permissions.external_write -eq 'deny') 'Readonly must deny editing, general shell and external writes.'
    # Validate real canonical prompts in an isolated root before mutating registry cases.
    $sandbox = Join-Path ([IO.Path]::GetTempPath()) ('office-core-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    try {
        Copy-Item -LiteralPath (Join-Path $kitRoot 'office') -Destination $sandbox -Recurse
        Assert-OfficeRegistry $registry $sandbox
        $bad = Copy-Value $registry; $bad.profiles[1].id = 'directora'
        Assert-Throws { Assert-OfficeRegistry $bad $sandbox } 'Duplicate profile ID'
        $bad = Copy-Value $registry; $bad.profiles[1].parent = 'producto'; $bad.profiles[2].parent = $bad.profiles[1].id
        Assert-Throws { Assert-OfficeRegistry $bad $sandbox } 'cycle'
        $bad = Copy-Value $registry; $bad.profiles[2].prompt = 'office/roles/missing.md'
        Assert-Throws { Assert-OfficeRegistry $bad $sandbox } 'Missing prompt'
        $bad = Copy-Value $registry; $bad.profiles[2].permission_set = 'godmode'
        Assert-Throws { Assert-OfficeRegistry $bad $sandbox } 'Unknown permission set'
        $bad = Copy-Value $registry; $bad.profiles[2].parent = 'missing'
        Assert-Throws { Assert-OfficeRegistry $bad $sandbox } 'Unknown parent'
        $bad = Copy-Value $registry; $bad.profiles[2].capabilities = @('lgtv')
        Assert-Throws { Assert-OfficeRegistry $bad $sandbox } 'Unknown capability'
        $bad = Copy-Value $registry; $bad.profiles[2].parent = $null
        Assert-Throws { Assert-OfficeRegistry $bad $sandbox } 'root'
        $bad = Copy-Value $registry; $bad.profiles[2].prompt = '../outside.md'
        Assert-Throws { Assert-OfficeRegistry $bad $sandbox } 'outside'
    } finally {
        $resolved = [IO.Path]::GetFullPath($sandbox)
        $temp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $resolved.StartsWith($temp, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe cleanup path.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}

if ($Section -in @('Registry', 'Contracts', 'All')) {
    $samples = @{
        task = '{"task_id":"T1","type":"feature","priority":"P1","objective":"Deliver","scope":["core"],"out_of_scope":[],"acceptance_criteria":["tests"],"constraints":[],"risk":"low","departments":["ingenieria-datos"],"artifacts":[],"status":"drafted"}'
        handoff = '{"from":"backend","to":"qa","task_id":"T1","context_summary":"Ready","scope":["core"],"artifacts":[],"evidence":["test run"],"gate_status":"pending","risks":[],"next_action":"Review"}'
        gate = '{"gate_id":"G1","task_id":"T1","kind":"qa","owner":"qa","required":true,"criteria":["tests"],"evidence":["test run"],"status":"pass"}'
        escalation = '{"escalation_id":"E1","task_id":"T1","trigger":"spend","question":"Approve?","options":["yes","no"],"recommendation":"no","status":"open","resolution":null}'
    }
    $expectedRequired = @{
        task = 'task_id,type,priority,objective,scope,out_of_scope,acceptance_criteria,constraints,risk,departments,artifacts,status'
        handoff = 'from,to,task_id,context_summary,scope,artifacts,evidence,gate_status,risks,next_action'
        gate = 'gate_id,task_id,kind,owner,required,criteria,evidence,status'
        escalation = 'escalation_id,task_id,trigger,question,options,recommendation,status,resolution'
    }
    $expectedEnums = @{
        task = @{ type = 'feature,bug,audit,deploy,incident,research,other'; priority = 'P0,P1,P2,P3'; risk = 'low,medium,high,critical'; status = 'drafted,approved,in_progress,verification,completed,blocked,cancelled' }
        handoff = @{ gate_status = 'pending,pass,fail,waived' }
        gate = @{ kind = 'product,design,implementation,qa,security,documentation,release,post_deploy'; status = 'pending,pass,fail,waived' }
        escalation = @{ trigger = 'business_ambiguity,legal_privacy,credentials,external_write,production,spend,destructive_action,instruction_conflict'; status = 'open,resolved' }
    }
    foreach ($name in @('task', 'handoff', 'gate', 'escalation')) {
        $schema = Get-OfficeContractSchema $name $kitRoot
        Assert-True (($schema.required -join ',') -eq $expectedRequired[$name]) "Required fields differ for $name."
        foreach ($field in $expectedEnums[$name].Keys) {
            Assert-True (($schema.properties.$field.enum -join ',') -eq $expectedEnums[$name][$field]) "Enum differs for $name.$field."
        }
        $value = $samples[$name] | ConvertFrom-Json
        Assert-OfficeContractInstance $value $name $schema
        foreach ($required in $schema.required) {
            $bad = Copy-Value $value; $bad.PSObject.Properties.Remove($required)
            Assert-Throws { Assert-OfficeContractInstance $bad $name $schema } "required.*$required"
        }
        foreach ($property in $schema.properties.PSObject.Properties) {
            if ($property.Value.PSObject.Properties.Name -contains 'enum') {
                foreach ($allowed in $property.Value.enum) {
                    $candidate = Copy-Value $value; $candidate.($property.Name) = $allowed
                    if ($name -eq 'gate' -and $allowed -eq 'waived') { $candidate | Add-Member waiver ([pscustomobject]@{ approved_by = 'human'; reason = 'Accepted risk'; evidence = @('Human approval') }) }
                    if ($name -eq 'escalation' -and $property.Name -eq 'status' -and $allowed -eq 'resolved') { $candidate.resolution = 'Approved by human' }
                    Assert-OfficeContractInstance $candidate $name $schema
                }
                $bad = Copy-Value $value; $bad.($property.Name) = 'invalid'
                Assert-Throws { Assert-OfficeContractInstance $bad $name $schema } "enum.*$($property.Name)"
            }
        }
    }
    $escalationSchema = Get-OfficeContractSchema escalation $kitRoot
    $escalation = $samples.escalation | ConvertFrom-Json
    Assert-OfficeContractInstance $escalation escalation $escalationSchema
    $escalation.status = 'resolved'; $escalation.resolution = $null
    Assert-Throws { Assert-OfficeContractInstance $escalation escalation $escalationSchema } 'type.*resolution'
    foreach ($invalidResolution in @('', '   ')) {
        $escalation.resolution = $invalidResolution
        Assert-Throws { Assert-OfficeContractInstance $escalation escalation $escalationSchema } 'nonempty.*resolution'
    }
    $escalation.resolution = 'Approved by human'
    Assert-OfficeContractInstance $escalation escalation $escalationSchema
    $taskSchema = Get-OfficeContractSchema task $kitRoot
    $transitions = @{ drafted = 'approved,blocked,cancelled'; approved = 'in_progress,blocked,cancelled'; in_progress = 'verification,blocked,cancelled'; verification = 'completed,blocked,cancelled'; completed = ''; blocked = 'previous_state,cancelled'; cancelled = '' }
    foreach ($state in $transitions.Keys) {
        Assert-True (($taskSchema.'x-transitions'.$state -join ',') -eq $transitions[$state]) "Task transition differs for $state."
    }
    Assert-True ($taskSchema.'x-blocked-resume'.requires -eq 'resolved_escalation') 'Blocked resume requires resolved escalation.'
    $gateSchema = Get-OfficeContractSchema gate $kitRoot
    $gate = $samples.gate | ConvertFrom-Json; $gate.status = 'waived'
    Assert-Throws { Assert-OfficeContractInstance $gate gate $gateSchema } 'required.*waiver'
    $gate | Add-Member waiver ([pscustomobject]@{ evidence = @('Human approval') })
    Assert-Throws { Assert-OfficeContractInstance $gate gate $gateSchema } 'required.*approved_by'
    $gate.waiver | Add-Member approved_by 'human'
    Assert-Throws { Assert-OfficeContractInstance $gate gate $gateSchema } 'required.*reason'
    $gate.waiver | Add-Member reason 'Accepted risk'; $gate.waiver.evidence = @()
    Assert-Throws { Assert-OfficeContractInstance $gate gate $gateSchema } 'minItems.*evidence'
    $gate = $samples.gate | ConvertFrom-Json; $gate.evidence = @()
    Assert-Throws { Assert-OfficeContractInstance $gate gate $gateSchema } 'minItems.*evidence'
    $handoffSchema = Get-OfficeContractSchema handoff $kitRoot
    $handoff = $samples.handoff | ConvertFrom-Json; $handoff.gate_status = 'pass'; $handoff.evidence = @()
    Assert-Throws { Assert-OfficeContractInstance $handoff handoff $handoffSchema } 'minItems.*evidence'
    $gate = $samples.gate | ConvertFrom-Json; $gate.required = 'true'
    Assert-Throws { Assert-OfficeContractInstance $gate gate $gateSchema } 'type.*required'
    $bad = $samples.task | ConvertFrom-Json; $bad.scope = 'not an array'
    Assert-Throws { Assert-OfficeContractInstance $bad task $taskSchema } 'type.*scope'
    $bad = $samples.task | ConvertFrom-Json; $bad.objective = ' '
    Assert-Throws { Assert-OfficeContractInstance $bad task $taskSchema } 'nonempty.*objective'
    $bad = $samples.task | ConvertFrom-Json; $bad.scope = @('core', $null)
    Assert-Throws { Assert-OfficeContractInstance $bad task $taskSchema } 'type.*scope'
    $bad = $samples.task | ConvertFrom-Json; $bad.objective = $null
    Assert-Throws { Assert-OfficeContractInstance $bad task $taskSchema } 'type.*objective'
    $bad = $samples.task | ConvertFrom-Json; $bad.type = @('feature')
    Assert-Throws { Assert-OfficeContractInstance $bad task $taskSchema } '(enum|type).*type'
    Assert-Throws { Assert-OfficeContractInstance ($samples.task | ConvertFrom-Json) task $gateSchema } 'Schema does not describe'
    Assert-Throws { Get-OfficeContractSchema '../outside' $kitRoot } 'Unknown contract'
    Write-Output 'PASS: 31 profiles; 4 contracts; 3 permission sets'
}
