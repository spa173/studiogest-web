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

    $prose = Remove-OfficeMarkdownFencedCode $Text
    $prose = [regex]::Replace($prose, '(?i)\b(?:https?|ftp)://[^\s<>()]+', '')
    @([regex]::Matches(
        $prose,
        '(?<![A-Za-z0-9_.-])(?<path>(?:references|assets|evals|scripts)/[A-Za-z0-9._/-]+)'
    ) | ForEach-Object {
        $_.Groups['path'].Value.TrimEnd('.', ',', ':', ';', ')', ']')
    } | Sort-Object -Unique)
}

function Remove-OfficeMarkdownFencedCode {
    param([Parameter(Mandatory)][string] $Text)

    $result = [Text.StringBuilder]::new()
    $inFence = $false
    $fenceCharacter = $null
    foreach ($line in [regex]::Split($Text, '\r?\n')) {
        $marker = [regex]::Match($line, '^\s*(?<marker>`{3,}|~{3,})')
        if ($marker.Success) {
            $character = $marker.Groups['marker'].Value[0]
            if (-not $inFence) {
                $inFence = $true
                $fenceCharacter = $character
            } elseif ($character -eq $fenceCharacter) {
                $inFence = $false
                $fenceCharacter = $null
            }
            continue
        }
        if (-not $inFence) { $null = $result.AppendLine($line) }
    }
    $result.ToString()
}

function Get-OfficeSkillMarkdownDocuments {
    param([Parameter(Mandatory)][string] $SkillPath)

    $documents = @((Join-Path $SkillPath 'SKILL.md'))
    foreach ($relative in @('references', 'evals')) {
        $directory = Join-Path $SkillPath $relative
        if (Test-Path -LiteralPath $directory -PathType Container) {
            $documents += @(Get-ChildItem -LiteralPath $directory -Recurse -File -Filter '*.md' | Select-Object -ExpandProperty FullName)
        }
    }
    @($documents | Sort-Object -Unique)
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
    $positiveEnglish = $document.Description -match "(?i)(?<!not )(?<!never )(?<!don't )\buse when\b"
    $positiveSpanish = $document.Description -match '(?i)\b(?:úsala|usala|utilízala|utilizala)\s+cuando\b'
    if (-not ($positiveEnglish -or $positiveSpanish)) {
        throw "Skill '$folder' lacks a positive activation trigger."
    }

    $root = [IO.Path]::GetFullPath($SkillPath).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    foreach ($markdownPath in Get-OfficeSkillMarkdownDocuments $SkillPath) {
        $markdown = $strictUtf8.GetString([IO.File]::ReadAllBytes($markdownPath))
        $relativeDocument = [IO.Path]::GetRelativePath($SkillPath, $markdownPath)
        foreach ($reference in Get-OfficeSkillReferences $markdown) {
            $candidate = [IO.Path]::GetFullPath((Join-Path $SkillPath $reference))
            if (-not $candidate.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Reference outside skill '$folder' in '$relativeDocument': '$reference'."
            }
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                throw "Referenced path '$reference' in '$relativeDocument' does not resolve to a file."
            }
            if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
                throw "Missing reference '$reference' in '$relativeDocument' for skill '$folder'."
            }
        }
    }
}

function Assert-OfficeSkillConsumerContract {
    param(
        [Parameter(Mandatory)][string] $Path,
        [Parameter(Mandatory)][string[]] $AvailableSkills
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing skill consumer contract '$Path'." }
    try {
        $contract = $strictUtf8.GetString([IO.File]::ReadAllBytes($Path)) | ConvertFrom-Json
    } catch {
        throw "Invalid skill consumer contract '$Path': $($_.Exception.Message)"
    }
    if ($contract.version -ne 1) { throw 'Skill consumer contract must use version 1.' }
    if ($contract.scenarios -isnot [array] -or $contract.scenarios.Count -lt 2) {
        throw 'Skill consumer contract must contain at least two scenarios.'
    }

    $ids = @()
    foreach ($scenario in $contract.scenarios) {
        foreach ($field in @('id', 'kind', 'prompt', 'expected')) {
            if ($scenario.PSObject.Properties.Name -cnotcontains $field) { throw "Consumer scenario is missing '$field'." }
        }
        if ($scenario.id -isnot [string] -or $scenario.id -cnotmatch '^[a-z][a-z0-9-]*$') { throw 'Consumer scenario has an invalid id.' }
        if ($scenario.kind -cnotin @('activation', 'authority')) { throw "Consumer scenario '$($scenario.id)' has an invalid kind." }
        if ($scenario.prompt -isnot [string] -or [string]::IsNullOrWhiteSpace($scenario.prompt)) { throw "Consumer scenario '$($scenario.id)' has an empty prompt." }
        if ($scenario.expected.activate -isnot [array] -or $scenario.expected.must_not_activate -isnot [array] -or $scenario.expected.authority -isnot [pscustomobject]) {
            throw "Consumer scenario '$($scenario.id)' has an invalid expected contract."
        }

        $activated = @($scenario.expected.activate)
        $excluded = @($scenario.expected.must_not_activate)
        $overlap = @($activated | Where-Object { $_ -cin $excluded })
        if ($overlap.Count -gt 0) { throw "Consumer scenario '$($scenario.id)' lists '$($overlap[0])' in both activate and must_not_activate." }
        foreach ($skill in @($activated + $excluded)) {
            if ($skill -isnot [string] -or $skill -cnotin $AvailableSkills) { throw "Consumer scenario '$($scenario.id)' references unknown skill '$skill'." }
        }
        foreach ($authority in $scenario.expected.authority.PSObject.Properties) {
            if ($authority.Value -cne 'not-applicable' -and $authority.Value -cnotin $AvailableSkills) {
                throw "Consumer scenario '$($scenario.id)' assigns unknown authority '$($authority.Value)'."
            }
        }
        $ids += $scenario.id
    }
    if (@($ids | Sort-Object -Unique).Count -ne $ids.Count) { throw 'Skill consumer contract contains duplicate scenario ids.' }

    $backend = @($contract.scenarios | Where-Object id -CEQ 'backend-only-anti-trigger')
    if ($backend.Count -ne 1 -or 'taste-skill' -cnotin $backend[0].expected.must_not_activate) {
        throw 'Skill consumer contract must define the backend-only taste-skill anti-trigger.'
    }
    $visual = @($contract.scenarios | Where-Object id -CEQ 'frontend-visual-authority-handoff')
    if ($visual.Count -ne 1 -or $visual[0].expected.authority.visual -cne 'taste-skill' -or $visual[0].expected.authority.client -cne 'frontend-developer') {
        throw 'Skill consumer contract must assign visual and client authority explicitly.'
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
    $consumerContractPath = Join-Path $PSScriptRoot 'fixtures/Office.Skill.ConsumerScenarios.json'
    $null = Assert-OfficeSkillConsumerContract -Path $consumerContractPath -AvailableSkills $importedNames

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
    Assert-True ($taste.Description -match '(?i)no usar para backend') 'taste-skill structural activation metadata must declare the backend-only exclusion.'
    Assert-True (
        $tasteEvals -match '(?i)anti-test' -and
        $tasteEvals -match '/api/orders' -and
        $tasteEvals -match '(?i)no debe activarse'
    ) 'taste-skill structural eval contract must include the backend-only anti-trigger scenario.'

    $frontendPath = Join-Path $skillsRoot 'frontend-developer'
    $frontend = Read-OfficeSkillDocument (Join-Path $frontendPath 'SKILL.md')
    Assert-True (
        $frontend.Description -match '(?i)no define (tipografía|tipografia)' -and
        $frontend.Description -match '(?i)responsabilidad.*taste-skill' -and
        $frontend.Body -match '(?i)única fuente de verdad estética' -and
        $frontend.Body -match '(?i)no redefinas valores visuales'
    ) 'frontend-developer structural authority contract must explicitly assign visual decisions to taste-skill.'

    $auditRunner = Join-Path $PSScriptRoot 'Invoke-TasteAudit.ps1'
    Assert-True (Test-Path -LiteralPath $auditRunner -PathType Leaf) 'Missing supported Taste audit runner.'

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

        $negativeOnly = Join-Path $sandbox 'negative-only'
        New-Item -ItemType Directory -Path $negativeOnly | Out-Null
        [IO.File]::WriteAllText(
            (Join-Path $negativeOnly 'SKILL.md'),
            "---`nname: negative-only`ndescription: Do not use when the task is backend only.`n---`n`n# Negative only`n",
            [Text.UTF8Encoding]::new($false)
        )
        Assert-Throws { Assert-OfficeSkill $negativeOnly } 'positive activation trigger'

        $directoryReference = Join-Path $sandbox 'directory-reference'
        New-Item -ItemType Directory -Path (Join-Path $directoryReference 'references/not-a-file.md') -Force | Out-Null
        [IO.File]::WriteAllText(
            (Join-Path $directoryReference 'SKILL.md'),
            "---`nname: directory-reference`ndescription: Use when validating a controlled directory reference.`n---`n`nRead ``references/not-a-file.md``.`n",
            [Text.UTF8Encoding]::new($false)
        )
        Assert-Throws { Assert-OfficeSkill $directoryReference } 'does not resolve to a file'

        $supportingReference = Join-Path $sandbox 'supporting-reference'
        New-Item -ItemType Directory -Path (Join-Path $supportingReference 'references') -Force | Out-Null
        [IO.File]::WriteAllText(
            (Join-Path $supportingReference 'SKILL.md'),
            "---`nname: supporting-reference`ndescription: Use when validating a supporting Markdown reference.`n---`n`nRead ``references/guide.md``.`n",
            [Text.UTF8Encoding]::new($false)
        )
        [IO.File]::WriteAllText(
            (Join-Path $supportingReference 'references/guide.md'),
            "# Guide`n`nUse [the local asset](assets/missing.css).`n",
            [Text.UTF8Encoding]::new($false)
        )
        Assert-Throws { Assert-OfficeSkill $supportingReference } "Missing reference 'assets/missing.css'.*references[/\\]guide.md"

        $nonReferences = @'
# Guide

External example: https://example.test/assets/not-local.css

```text
assets/example-only.css
```
'@
        [IO.File]::WriteAllText(
            (Join-Path $supportingReference 'references/guide.md'),
            $nonReferences,
            [Text.UTF8Encoding]::new($false)
        )
        $null = Assert-OfficeSkill $supportingReference

        $invalidContract = Join-Path $sandbox 'invalid-consumer-contract.json'
        [IO.File]::WriteAllText(
            $invalidContract,
            '{"version":1,"scenarios":[{"id":"contradictory","kind":"activation","prompt":"Backend task","expected":{"activate":["taste-skill"],"must_not_activate":["taste-skill"],"authority":{"visual":"taste-skill"}}},{"id":"second-scenario","kind":"authority","prompt":"Frontend task","expected":{"activate":["frontend-developer"],"must_not_activate":[],"authority":{"client":"frontend-developer"}}}]}',
            [Text.UTF8Encoding]::new($false)
        )
        Assert-Throws {
            Assert-OfficeSkillConsumerContract -Path $invalidContract -AvailableSkills $importedNames
        } 'both activate and must_not_activate'

        $nativePreference = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
        try {
            $cleanOutput = @(& pwsh -NoProfile -File $auditRunner -Path (Join-Path $tastePath 'assets') -Profile 3 2>&1)
            $cleanExit = $LASTEXITCODE
            Assert-True ($cleanExit -eq 0 -and ($cleanOutput -join "`n") -match '0 errores') 'Taste runner must audit the clean asset directory successfully under the host console encoding.'

            $badOutput = @(& pwsh -NoProfile -File $auditRunner -Path (Join-Path $tastePath 'evals/fixtures') -Profile 1 2>&1)
            $badExit = $LASTEXITCODE
            Assert-True ($badExit -eq 1 -and ($badOutput -join "`n") -match '11 errores') 'Taste runner must preserve the auditor failure and findings for the bad fixture.'

            $missingAuditPath = Join-Path $sandbox 'missing-audit-input'
            $missingOutput = @(& pwsh -NoProfile -File $auditRunner -Path $missingAuditPath -Profile 3 2>&1)
            $missingExit = $LASTEXITCODE
            Assert-True ($missingExit -eq 2 -and ($missingOutput -join "`n") -match 'does not exist') 'Taste runner must reject a missing audit input before Python runs.'

            $emptyAuditPath = Join-Path $sandbox 'empty-audit-input'
            New-Item -ItemType Directory -Path $emptyAuditPath | Out-Null
            [IO.File]::WriteAllText((Join-Path $emptyAuditPath 'README.txt'), 'No auditable files.', [Text.UTF8Encoding]::new($false))
            $emptyOutput = @(& pwsh -NoProfile -File $auditRunner -Path $emptyAuditPath -Profile 3 2>&1)
            $emptyExit = $LASTEXITCODE
            Assert-True ($emptyExit -eq 2 -and ($emptyOutput -join "`n") -match 'no auditable files') 'Taste runner must reject a directory without auditable files before Python runs.'
        } finally {
            $PSNativeCommandUseErrorActionPreference = $nativePreference
        }
    } finally {
        $resolved = [IO.Path]::GetFullPath($sandbox)
        $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
        if (-not $resolved.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe test cleanup path.' }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }

    Write-Output 'PASS: imported skills; recursive references, structural consumer contracts, and Taste audit runner validated'
}
