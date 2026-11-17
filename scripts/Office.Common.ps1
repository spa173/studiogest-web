# Shared canonical registry and contract validation. No external modules required.
function Set-ManagedInstructionBlock {
    param([AllowEmptyString()][string] $Existing, [string] $Block)
    $start = '<!-- oficina-unificada:inicio -->'
    $end = '<!-- oficina-unificada:fin -->'
    $blockText = ($Block -replace "`r`n?", "`n").Trim("`n")
    foreach ($text in @($Existing, $blockText)) {
        $starts = [regex]::Matches($text, [regex]::Escape($start)).Count
        $ends = [regex]::Matches($text, [regex]::Escape($end)).Count
        if ($starts -ne $ends -or $starts -gt 1 -or ($starts -eq 1 -and $text.IndexOf($end, [StringComparison]::Ordinal) -lt $text.IndexOf($start, [StringComparison]::Ordinal))) {
            throw 'Invalid managed instruction markers: expected one ordered pair or no markers.'
        }
    }
    if (-not $blockText.StartsWith($start, [StringComparison]::Ordinal) -or -not $blockText.EndsWith($end, [StringComparison]::Ordinal)) {
        throw 'Invalid block markers: the block must be bounded by the managed markers.'
    }
    $startIndex = $Existing.IndexOf($start, [StringComparison]::Ordinal)
    if ($startIndex -ge 0) {
        $endIndex = $Existing.IndexOf($end, $startIndex, [StringComparison]::Ordinal) + $end.Length
        return $Existing.Substring(0, $startIndex) + $blockText + $Existing.Substring($endIndex)
    }
    $separator = if ($Existing.Length -eq 0 -or $Existing.EndsWith("`n`n")) { '' } elseif ($Existing.EndsWith("`n")) { "`n" } else { "`n`n" }
    $Existing + $separator + $blockText + "`n"
}

function Get-OfficeRegistry {
    param([string] $Root = (Split-Path -Parent $PSScriptRoot))
    Get-Content -LiteralPath (Join-Path $Root 'office/registry.json') -Raw | ConvertFrom-Json
}

function Get-OfficeRolePrompt {
    param([Parameter(Mandatory)][pscustomobject] $Role, [Parameter(Mandatory)][string] $Root)
    if ($Role.prompt -isnot [string] -or [string]::IsNullOrWhiteSpace($Role.prompt)) { throw 'Invalid prompt path.' }
    if ([IO.Path]::IsPathRooted($Role.prompt)) { throw "Prompt outside root: '$($Role.prompt)'." }
    $rootPath = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    $promptPath = [IO.Path]::GetFullPath((Join-Path $Root $Role.prompt))
    if (-not $promptPath.StartsWith($rootPath, [StringComparison]::OrdinalIgnoreCase)) { throw "Prompt outside root: '$($Role.prompt)'." }
    if (-not (Test-Path -LiteralPath $promptPath -PathType Leaf)) { throw "Missing prompt '$($Role.prompt)'." }
    [IO.File]::ReadAllText($promptPath, [Text.Encoding]::UTF8)
}

function Assert-OfficeRegistry {
    param([Parameter(Mandatory)][pscustomobject] $Registry, [Parameter(Mandatory)][string] $Root)
    $profiles = @($Registry.profiles)
    if ($profiles.Count -ne 31) { throw "Expected 31 profiles; found $($profiles.Count)." }
    $byId = @{}
    $permissionSets = @('readonly', 'implementer', 'operator')
    foreach ($name in $permissionSets) {
        $permission = Get-Content -LiteralPath (Join-Path $Root "office/permission-sets/$name.json") -Raw | ConvertFrom-Json
        if ($permission.id -cne $name) { throw "Invalid permission set ID: $name." }
    }
    $catalog = Get-Content -LiteralPath (Join-Path $Root 'office/capabilities.json') -Raw | ConvertFrom-Json
    $capabilityIds = @($catalog.capabilities.id)
    if (@($capabilityIds | Sort-Object -Unique).Count -ne $capabilityIds.Count) { throw 'Duplicate capability ID.' }
    $rootPath = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    foreach ($profile in $profiles) {
        foreach ($field in @('id', 'kind', 'department', 'parent', 'description', 'prompt', 'permission_set', 'skills', 'capabilities')) {
            if ($profile.PSObject.Properties.Name -cnotcontains $field) { throw "Missing profile field '$field'." }
        }
        if ($profile.id -cnotmatch '^[a-z][a-z0-9-]*$') { throw "Invalid profile ID: '$($profile.id)'." }
        if ($byId.ContainsKey($profile.id)) { throw "Duplicate profile ID: '$($profile.id)'." }
        $byId[$profile.id] = $profile
        if ($profile.kind -cnotin @('director', 'coordinator', 'specialist')) { throw "Unknown profile kind: '$($profile.kind)'." }
        if ($profile.permission_set -cnotin $permissionSets) { throw "Unknown permission set '$($profile.permission_set)' for '$($profile.id)'." }
        foreach ($field in @('department', 'description', 'prompt')) {
            if ($profile.$field -isnot [string] -or [string]::IsNullOrWhiteSpace($profile.$field)) { throw "Invalid profile field '$field' for '$($profile.id)'." }
        }
        foreach ($field in @('skills', 'capabilities')) {
            if ($profile.$field -isnot [array]) { throw "Expected array '$field' for '$($profile.id)'." }
            foreach ($value in $profile.$field) {
                if ($value -isnot [string] -or [string]::IsNullOrWhiteSpace($value)) { throw "Invalid $field reference for '$($profile.id)'." }
            }
        }
        foreach ($capability in $profile.capabilities) {
            if ($capability -cnotin $capabilityIds) { throw "Unknown capability '$capability' for '$($profile.id)'." }
        }
        if ([IO.Path]::IsPathRooted($profile.prompt)) { throw "Prompt outside root for '$($profile.id)'." }
        $promptPath = [IO.Path]::GetFullPath((Join-Path $Root $profile.prompt))
        if (-not $promptPath.StartsWith($rootPath, [StringComparison]::OrdinalIgnoreCase)) { throw "Prompt outside root for '$($profile.id)'." }
        if (-not (Test-Path -LiteralPath $promptPath -PathType Leaf)) { throw "Missing prompt '$($profile.prompt)' for '$($profile.id)'." }
    }
    foreach ($profile in $profiles) {
        if ($null -ne $profile.parent -and -not $byId.ContainsKey([string] $profile.parent)) { throw "Unknown parent '$($profile.parent)' for '$($profile.id)'." }
        $seen = @{}
        $current = $profile
        while ($null -ne $current) {
            if ($seen.ContainsKey($current.id)) { throw "Hierarchy cycle at '$($current.id)'." }
            $seen[$current.id] = $true
            if ($null -eq $current.parent) { break }
            if (-not $byId.ContainsKey([string] $current.parent)) { throw "Unknown parent '$($current.parent)'." }
            $current = $byId[$current.parent]
        }
    }
    $roots = @($profiles | Where-Object { $null -eq $_.parent })
    if ($roots.Count -ne 1 -or $roots[0].id -cne 'directora' -or $roots[0].kind -cne 'director') { throw 'Only directora may be the root Director.' }
    foreach ($entry in @(@('director', 1), @('coordinator', 5), @('specialist', 25))) {
        if (@($profiles | Where-Object kind -CEQ $entry[0]).Count -ne $entry[1]) { throw "Invalid count for kind '$($entry[0])'." }
    }
    foreach ($profile in $profiles) {
        if ($profile.kind -eq 'director') { continue }
        $parent = $byId[$profile.parent]
        if (($profile.kind -eq 'coordinator' -and $parent.kind -ne 'director') -or
            ($profile.kind -eq 'specialist' -and $parent.kind -ne 'coordinator')) { throw "Invalid parent kind for '$($profile.id)'." }
        if ($profile.kind -eq 'specialist' -and $profile.department -cne $parent.department) { throw "Department differs from parent for '$($profile.id)'." }
    }
}

function Get-OfficeContractSchema {
    param([Parameter(Mandatory)][string] $Name, [string] $Root = (Split-Path -Parent $PSScriptRoot))
    if ($Name -cnotin @('task', 'handoff', 'gate', 'escalation')) { throw "Unknown contract '$Name'." }
    Get-Content -LiteralPath (Join-Path $Root "office/contracts/$Name.schema.json") -Raw | ConvertFrom-Json
}

# Deliberately implements only the JSON Schema vocabulary used by the four
# bundled contracts: type, required, properties, enum, const, minLength,
# pattern, items, minItems, allOf and if/then. It is not a general schema engine.
function Assert-OfficeSchemaValue {
    param([AllowNull()] $Value, [pscustomobject] $Schema, [string] $Path)
    $keywords = @($Schema.PSObject.Properties.Name)
    if ($keywords -contains 'type') {
        $matchesType = $false
        foreach ($typeName in @($Schema.type)) {
            $matchesType = $matchesType -or $(switch ($typeName) {
                'null' { $null -eq $Value }
                'object' { $Value -is [pscustomobject] }
                'array' { $Value -is [array] }
                'string' { $Value -is [string] }
                'boolean' { $Value -is [bool] }
                default { throw "Unsupported schema type '$typeName' at $Path." }
            })
        }
        if (-not $matchesType) { throw "Invalid type at $Path; expected $($Schema.type -join '|')." }
    }
    if ($keywords -contains 'enum' -and $Value -cnotin $Schema.enum) { throw "Invalid enum at $Path." }
    if ($keywords -contains 'const' -and $Value -cne $Schema.const) { throw "Invalid const at $Path." }
    if ($Value -is [string] -and $keywords -contains 'minLength' -and $Value.Trim().Length -lt $Schema.minLength) { throw "Expected nonempty string at $Path." }
    if ($Value -is [string] -and $keywords -contains 'pattern' -and -not [regex]::IsMatch($Value, $Schema.pattern)) { throw "Invalid pattern at $Path." }
    if ($Value -is [array]) {
        if ($keywords -contains 'minItems' -and $Value.Count -lt $Schema.minItems) { throw "Invalid minItems at $Path." }
        if ($keywords -contains 'items') {
            for ($index = 0; $index -lt $Value.Count; $index++) { Assert-OfficeSchemaValue -Value $Value[$index] -Schema $Schema.items -Path "$Path[$index]" }
        }
    }
    if ($Value -is [pscustomobject]) {
        foreach ($required in $Schema.required) {
            if ($Value.PSObject.Properties.Name -cnotcontains $required) { throw "Missing required field $Path.$required." }
        }
        if ($keywords -contains 'properties') {
            foreach ($property in $Schema.properties.PSObject.Properties) {
                if ($Value.PSObject.Properties.Name -ccontains $property.Name) {
                    Assert-OfficeSchemaValue -Value $Value.($property.Name) -Schema $property.Value -Path "$Path.$($property.Name)"
                }
            }
        }
    }
    foreach ($clause in $Schema.allOf) { Assert-OfficeSchemaValue -Value $Value -Schema $clause -Path $Path }
    if ($keywords -contains 'if') {
        $conditionMatches = $true
        try { Assert-OfficeSchemaValue -Value $Value -Schema $Schema.if -Path $Path } catch { $conditionMatches = $false }
        if ($conditionMatches -and $keywords -contains 'then') { Assert-OfficeSchemaValue -Value $Value -Schema $Schema.then -Path $Path }
    }
}

function Assert-OfficeContractInstance {
    param([Parameter(Mandatory)][pscustomobject] $Value, [Parameter(Mandatory)][string] $Type, [Parameter(Mandatory)][pscustomobject] $Schema)
    if ($Type -cnotin @('task', 'handoff', 'gate', 'escalation')) { throw "Unknown contract '$Type'." }
    if ($Schema.title -cne $Type) { throw "Schema does not describe contract '$Type'." }
    Assert-OfficeSchemaValue -Value $Value -Schema $Schema -Path $Type
}
