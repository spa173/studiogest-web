$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $kitRoot 'codex\roles'
$targetDir = Join-Path $kitRoot '.codex\agents'
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

foreach ($role in Get-ChildItem -LiteralPath $sourceDir -Filter '*.md' -File) {
    $instructions = [System.IO.File]::ReadAllText($role.FullName, [System.Text.Encoding]::UTF8)
    $firstLine = ($instructions -split "`r?`n", 2)[0]
    $description = $firstLine -replace '^#\s*', ''
    $name = $role.BaseName
    $toml = @(
        "name = $(ConvertTo-Json -InputObject $name -Compress)"
        "description = $(ConvertTo-Json -InputObject $description -Compress)"
        "developer_instructions = $(ConvertTo-Json -InputObject $instructions -Compress)"
    ) -join "`n"
    [System.IO.File]::WriteAllText(
        (Join-Path $targetDir ($name + '.toml')),
        $toml + "`n",
        [System.Text.UTF8Encoding]::new($false)
    )
}

Write-Output "Perfiles Codex generados en: $targetDir"
