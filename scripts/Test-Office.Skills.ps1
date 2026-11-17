[CmdletBinding()]
param(
    [ValidateSet('Imported', 'All')]
    [string] $Section = 'All'
)

$ErrorActionPreference = 'Stop'
$kitRoot = Split-Path -Parent $PSScriptRoot
$strictUtf8 = [Text.UTF8Encoding]::new($false, $true)

function Assert-True {
    param($Condition, [string] $Message)
    if (-not $Condition) { throw $Message }
}

function Assert-Throws {
    param([scriptblock] $Action, [string] $Pattern)
    $caught = $null
    try { & $Action } catch { $caught = $_.Exception.Message }
    Assert-True ($null -ne $caught -and $caught -match $Pattern) "Expected error '$Pattern'; got '$caught'."
}

function Read-OfficeSkillDocument {
    param([Parameter(Mandatory)][string] $Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing skill document '$Path'." }
    $bytes = [IO.File]::ReadAllBytes($Path)
    $text = $strictUtf8.GetString($bytes)
    $frontmatter = [regex]::Match($text, '\A---\r?\n(?<header>.*?)\r?\n---\r?\n(?<body>.*)\z', 'Singleline')
    if (-not $frontmatter.Success) { throw "Invalid frontmatter in '$Path'." }
    $header = $frontmatter.Groups['header'].Value
    $name = [regex]::Match($header, '(?m)^name:\s*(?<value>[^\r\n]+)\s*$')
    $description = [regex]::Match($header, '(?m)^description:\s*(?<value>[^\r\n]+)\s*$')
    if (-not $name.Success) { throw "Missing skill name in '$Path'." }
    if (-not $description.Success -or [string]::IsNullOrWhiteSpace($description.Groups['value'].Value)) {
        throw "Missing activation description in '$Path'."
    }
    [pscustomobject]@{
        Name = $name.Groups['value'].Value.Trim()
        Description = $description.Groups['value'].Value.Trim()
        Body = $frontmatter.Groups['body'].Value
        Text = $text
    }
}

function Get-OfficeSkillReferences {
    param([Parameter(Mandatory)][string] $Text)

    @([regex]::Matches(
        $Text,
        '(?<![A-Za-z0-9_.-])(?<path>(?:references|assets|evals|scripts)/[A-Za-z0-9._/-]+)'
    ) | ForEach-Object {
        $_.Groups['path'].Value.TrimEnd('.', ',', ':', ';', ')', ']')
    } | Sort-Object -Unique)
}

function Get-OfficeSkillManifest {
    param([Parameter(Mandatory)][string] $SkillsRoot)

    if (-not (Test-Path -LiteralPath $SkillsRoot -PathType Container)) { return @() }
    @(Get-ChildItem -LiteralPath $SkillsRoot -Directory | Sort-Object Name | ForEach-Object {
        $document = Read-OfficeSkillDocument (Join-Path $_.FullName 'SKILL.md')
        [pscustomobject]@{
            Name = $document.Name
            Folder = $_.Name
            Description = $document.Description
            Path = $_.FullName
        }
    })
}

function Assert-OfficeSkill {
    param([Parameter(Mandatory)][string] $SkillPath)

    if (-not (Test-Path -LiteralPath $SkillPath -PathType Container)) { throw "Missing skill folder '$SkillPath'." }
    $folder = Split-Path -Leaf $SkillPath
    $document = Read-OfficeSkillDocument (Join-Path $SkillPath 'SKILL.md')
    if ($document.Name -cne $folder) { throw "Skill name '$($document.Name)' does not match folder '$folder'." }
    if ($document.Name -cnotmatch '^[a-z][a-z0-9-]*$') { throw "Invalid skill name '$($document.Name)'." }
    if ($document.Description -notmatch '(?i)(\buse when\b|\bcuando\b)') {
        throw "Skill '$folder' lacks an activation-oriented description."
    }

    foreach ($reference in Get-OfficeSkillReferences $document.Text) {
        $candidate = [IO.Path]::GetFullPath((Join-Path $SkillPath $reference))
        $root = [IO.Path]::GetFullPath($SkillPath).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $candidate.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Reference outside skill '$folder': '$reference'."
        }
        if (-not (Test-Path -LiteralPath $candidate)) { throw "Missing reference '$reference' for skill '$folder'." }
    }
}

if ($Section -in @('Imported', 'All')) {
    $skillsRoot = Join-Path $kitRoot 'skills'
    Assert-True (Test-Path -LiteralPath $skillsRoot -PathType Container) 'Missing imported skills root.'

    $manifest = @(Get-OfficeSkillManifest $skillsRoot)
    $importedNames = @($manifest.Name)
    foreach ($name in @('taste-skill', 'frontend-developer')) {
        Assert-True ($name -cin $importedNames) "Missing imported skill '$name'."
        $null = Assert-OfficeSkill (Join-Path $skillsRoot $name)
    }

    $tastePath = Join-Path $skillsRoot 'taste-skill'
    foreach ($relative in @(
        'scripts/audit_taste.py',
        'evals/evals.md',
        'evals/fixtures/malo.css',
        'evals/fixtures/malo.html'
    )) {
        Assert-True (Test-Path -LiteralPath (Join-Path $tastePath $relative) -PathType Leaf) "Taste fixture is incomplete: '$relative'."
    }
    $taste = Read-OfficeSkillDocument (Join-Path $tastePath 'SKILL.md')
    $tasteEvals = $strictUtf8.GetString([IO.File]::ReadAllBytes((Join-Path $tastePath 'evals/evals.md')))
    Assert-True ($taste.Description -match '(?i)no usar para backend') 'taste-skill must exclude backend-only work in its activation description.'
    Assert-True (
        $tasteEvals -match '(?i)anti-test' -and
        $tasteEvals -match '/api/orders' -and
        $tasteEvals -match '(?i)no debe activarse'
    ) 'taste-skill must include the backend-only anti-trigger fixture.'

    $frontendPath = Join-Path $skillsRoot 'frontend-developer'
    $frontend = Read-OfficeSkillDocument (Join-Path $frontendPath 'SKILL.md')
    Assert-True (
        $frontend.Description -match '(?i)no define (tipografía|tipografia)' -and
        $frontend.Description -match '(?i)responsabilidad.*taste-skill' -and
        $frontend.Body -match '(?i)única fuente de verdad estética' -and
        $frontend.Body -match '(?i)no redefinas valores visuales'
    ) 'frontend-developer must explicitly cede visual authority to taste-skill.'

    $sandbox = Join-Path ([IO.Path]::GetTempPath()) ('office-skill-tests-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $sandbox | Out-Null
    try {
        $invalid = Join-Path $sandbox 'folder-name'
        New-Item -ItemType Directory -Path $invalid | Out-Null
        [IO.File]::WriteAllText(
            (Join-Path $invalid 'SKILL.md'),
            "---`nname: different-name`ndescription: Use when validating a controlled fixture.`n---`n`nSee ``references/missing.md``.`n",
            [Text.UTF8Encoding]::new($false)
        )
        Assert-Throws { Assert-OfficeSkill $invalid } 'does not match folder'
        [IO.File]::WriteAllText(
            (Join-Path $invalid 'SKILL.md'),
            "---`nname: folder-name`ndescription: Use when validating a controlled fixture.`n---`n`nSee ``references/missing.md``.`n",
            [Text.UTF8Encoding]::new($false)
        )
        Assert-Throws { Assert-OfficeSkill $invalid } "Missing reference 'references/missing.md'"
    } finally {
        $resolved = [IO.Path]::GetFullPath($sandbox)
        $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $resolved.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe test cleanup path.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }

    Write-Output 'PASS: imported design and frontend skills; references and authority boundaries validated'
}
