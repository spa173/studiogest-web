# Codex basic TOML strings accept the JSON escapes emitted by ConvertTo-Json.
function ConvertTo-CodexAgentToml {
    param(
        [Parameter(Mandatory)][pscustomobject] $Role,
        [Parameter(Mandatory)][string] $Prompt
    )
    if ($Role.kind -ceq 'director') { throw 'Director guidance belongs in the managed AGENTS.md block.' }
    $fields = [ordered]@{
        name = $Role.id
        description = $Role.description
        developer_instructions = ($Prompt -replace "`r`n?", "`n")
    }
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add("# GENERATED: DO NOT EDIT. Sources: office/registry.json; $($Role.prompt). Run scripts/Build-Office.ps1 -Platform Codex.")
    foreach ($key in $fields.Keys) {
        if ($fields[$key] -isnot [string] -or [string]::IsNullOrWhiteSpace($fields[$key])) { throw "Invalid Codex field '$key'." }
        $escaped = (ConvertTo-Json -InputObject $fields[$key] -Compress).Replace([string] [char] 0x7f, '\u007f')
        if (($escaped | ConvertFrom-Json) -cne $fields[$key]) { throw "Codex field '$key' did not round-trip." }
        $lines.Add("$key = $escaped")
    }
    ($lines -join "`n") + "`n"
}
