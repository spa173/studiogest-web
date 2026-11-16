param([ValidateSet('Registry', 'Contracts', 'All')][string] $Section = 'All')
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
    # A real temporary filesystem supplies prompts until the roles task lands.
    $sandbox = Join-Path ([IO.Path]::GetTempPath()) ('office-core-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    try {
        Copy-Item -LiteralPath (Join-Path $kitRoot 'office') -Destination $sandbox -Recurse
        foreach ($profile in $registry.profiles) {
            $path = Join-Path $sandbox $profile.prompt
            New-Item -ItemType Directory -Path (Split-Path $path) -Force | Out-Null
            Set-Content -LiteralPath $path -Value '# Test role fixture'
        }
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
