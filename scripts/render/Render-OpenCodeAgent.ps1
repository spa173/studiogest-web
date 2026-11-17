# OpenCode v2 uses ordered action/resource/effect rules; the last match wins.
function ConvertTo-OpenCodeAgent {
    param(
        [Parameter(Mandatory)][pscustomobject] $Role,
        [Parameter(Mandatory)][string] $Prompt,
        [Parameter(Mandatory)][pscustomobject] $PermissionSet
    )
    if ($PermissionSet.id -cne $Role.permission_set) { throw "Permission set differs for '$($Role.id)'." }
    $policy = $PermissionSet.permissions
    $rules = [Collections.Generic.List[object]]::new()
    # Unknown connector tools remain denied/ask until a verified tool binding exists.
    $rules.Add([ordered]@{ action = '*'; resource = '*'; effect = $policy.external_write })
    foreach ($action in @('read', 'glob', 'skill', 'question')) {
        $rules.Add([ordered]@{ action = $action; resource = '*'; effect = 'allow' })
    }
    # OpenCode's grep permission resource is the search expression, not each
    # candidate path, so native grep cannot inherit unrestricted search access.
    $rules.Add([ordered]@{ action = 'grep'; resource = '*'; effect = 'ask' })
    $webEffect = if ('web_research' -cin $Role.capabilities) { 'allow' } else { 'deny' }
    foreach ($action in @('webfetch', 'websearch')) {
        $rules.Add([ordered]@{ action = $action; resource = '*'; effect = $webEffect })
    }
    $editEffect = if ($policy.edit -eq 'workspace' -or $policy.prepare_config -eq 'workspace') { 'allow' } else { 'deny' }
    $rules.Add([ordered]@{ action = 'edit'; resource = '*'; effect = $(if ($Role.id -eq 'documentacion') { 'deny' } else { $editEffect }) })
    if ($Role.id -eq 'documentacion' -and $editEffect -eq 'allow') {
        foreach ($pattern in @('*.md', '*.txt', '*.rst', '*.adoc')) {
            $rules.Add([ordered]@{ action = 'edit'; resource = $pattern; effect = 'allow' })
        }
    }
    $rules.Add([ordered]@{ action = 'external_directory'; resource = '*'; effect = $policy.external_write })
    foreach ($pattern in @('*.env', '*.env.*', '*credentials*', '*.pem', '*.key')) {
        $rules.Add([ordered]@{ action = 'read'; resource = $pattern; effect = 'ask' })
        if ($editEffect -eq 'allow' -and $Role.id -ne 'documentacion') {
            $rules.Add([ordered]@{ action = 'edit'; resource = $pattern; effect = 'ask' })
        }
    }
    $shellEffect = if ($policy.shell -eq 'deny') { 'deny' } else { 'ask' }
    $rules.Add([ordered]@{ action = 'shell'; resource = '*'; effect = $shellEffect })
    $inspection = if ($null -ne $policy.inspection_commands) { @($policy.inspection_commands) } else {
        @('git status', 'git diff', 'git log', 'git show', 'rg', 'Get-ChildItem', 'Get-Content', 'Select-String')
    }
    # A command prefix does not constrain its options: diff can write output,
    # rg can run preprocessors, and shell reads bypass native credential rules.
    # Require approval for the full shell command; native read/glob/grep stay usable.
    foreach ($command in $inspection) {
        $rules.Add([ordered]@{ action = 'shell'; resource = "$command *"; effect = 'ask' })
    }
    $testCommands = @('npm test', 'npm run test', 'pnpm test', 'yarn test', 'pytest', 'dotnet test', 'cargo test', 'go test')
    if ($policy.test -eq 'allow' -or $policy.test_execution -eq 'task_authorization') {
        $testEffect = if ($policy.test -eq 'allow') { 'allow' } else { 'ask' }
        foreach ($command in $testCommands) {
            $rules.Add([ordered]@{ action = 'shell'; resource = "$command *"; effect = $testEffect })
        }
    }
    if ($policy.build -eq 'allow') {
        foreach ($command in @('npm run build', 'pnpm build', 'yarn build', 'dotnet build', 'cargo build', 'go build')) {
            $rules.Add([ordered]@{ action = 'shell'; resource = "$command *"; effect = 'allow' })
        }
    }
    if ($policy.diagnostics -eq 'allow') {
        foreach ($command in @('Get-Process', 'Get-Service', 'docker ps', 'docker logs', 'kubectl get', 'kubectl describe')) {
            $rules.Add([ordered]@{ action = 'shell'; resource = "$command *"; effect = 'ask' })
        }
    }
    $rules.Add([ordered]@{ action = 'subagent'; resource = '*'; effect = 'deny' })
    foreach ($id in @($Role.allowed_subagents)) {
        if ($id -cnotmatch '^[a-z][a-z0-9-]*$') { throw "Invalid subagent ID '$id'." }
        $rules.Add([ordered]@{ action = 'subagent'; resource = $id; effect = 'allow' })
    }
    $mode = if ($Role.kind -eq 'director') { 'primary' } else { 'subagent' }
    $description = ConvertTo-Json -InputObject $Role.description -Compress
    # JSON flow collections are valid YAML, avoiding an additional YAML dependency.
    $permissions = ConvertTo-Json -InputObject @($rules.ToArray()) -Depth 10 -Compress
    $normalizedPrompt = ($Prompt -replace "`r`n", "`n").TrimEnd("`r", "`n")
    @(
        '---'
        "description: $description"
        "mode: $mode"
        "permissions: $permissions"
        '---'
        ''
        "<!-- GENERATED: DO NOT EDIT. Sources: office/registry.json; $($Role.prompt); office/permission-sets/$($PermissionSet.id).json. Run scripts/Build-Office.ps1 -Platform OpenCode. -->"
        ''
        $normalizedPrompt
        ''
    ) -join "`n"
}
