param([ValidateSet('Registry', 'Contracts', 'Roles', 'All')][string] $Section = 'All')
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
                    Assert-OfficeContractInstance $candidate $name $schema
                }
                $bad = Copy-Value $value; $bad.($property.Name) = 'invalid'
                Assert-Throws { Assert-OfficeContractInstance $bad $name $schema } "enum.*$($property.Name)"
            }
        }
    }
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
