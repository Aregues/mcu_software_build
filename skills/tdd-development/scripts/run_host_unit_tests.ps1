param(
    [string]$ProjectRoot = (Get-Location).Path,
    [string[]]$Source = @(),
    [string[]]$Include = @(),
    [string]$BuildDir = '',
    [switch]$KeepBuild
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'find_mingw.ps1')

function Write-TestError {
    param([string]$Message)

    [Console]::Error.WriteLine($Message)
}

function Resolve-ProjectPath {
    param([string]$Root)

    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        throw "Project root does not exist: $Root"
    }

    return (Resolve-Path -LiteralPath $Root).Path
}

function Test-HasMain {
    param([string]$Path)

    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    return $content -match '\bint\s+main\s*\('
}

$root = Resolve-ProjectPath $ProjectRoot
$gcc = Find-MingwGcc

if (-not $gcc) {
    Write-TestError 'ERROR: MinGW gcc.exe not found. Install MinGW or add gcc.exe to PATH; host unit tests were not run.'
    exit 2
}

$testDir = Join-Path $root 'test'
if (-not (Test-Path -LiteralPath $testDir -PathType Container)) {
    Write-TestError "ERROR: No project-root test directory found: $testDir"
    exit 3
}

$allTestSources = Get-ChildItem -LiteralPath $testDir -Recurse -File -Filter '*.c' | Sort-Object FullName
if (-not $allTestSources) {
    Write-TestError "ERROR: No C test sources found under: $testDir"
    exit 3
}

$entrySources = @()
foreach ($file in $allTestSources) {
    $base = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    if ($file.Name -like 'test_*.c' -or $base -like '*_test' -or $file.Name -like '*.test.c' -or (Test-HasMain $file.FullName)) {
        $entrySources += $file
    }
}

if (-not $entrySources) {
    Write-TestError 'ERROR: No test entry files found. Expected test/test_*.c, test/*_test.c, test/*.test.c, or a C file containing int main(.'
    exit 3
}

if ([string]::IsNullOrWhiteSpace($BuildDir)) {
    $BuildDir = Join-Path ([System.IO.Path]::GetTempPath()) ("mcu-go-host-tests-{0}" -f ([guid]::NewGuid().ToString('N')))
}

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

$includeDirs = @($testDir, $root) + $Include
$extraSources = @()
foreach ($src in $Source) {
    $resolved = if ([System.IO.Path]::IsPathRooted($src)) { $src } else { Join-Path $root $src }
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        Write-TestError "ERROR: Extra source not found: $src"
        exit 3
    }
    $extraSources += (Resolve-Path -LiteralPath $resolved).Path
}

$supportSources = @($allTestSources | Where-Object { $entrySources.FullName -notcontains $_.FullName } | ForEach-Object { $_.FullName })
$failures = 0

foreach ($entry in $entrySources) {
    $exe = Join-Path $BuildDir ([System.IO.Path]::GetFileNameWithoutExtension($entry.Name) + '.exe')
    $compileArgs = @('-std=c11', '-Wall', '-Wextra', '-DHOST_UNIT_TEST=1')

    foreach ($inc in $includeDirs) {
        $incPath = if ([System.IO.Path]::IsPathRooted($inc)) { $inc } else { Join-Path $root $inc }
        $compileArgs += @('-I', $incPath)
    }

    $compileArgs += @('-o', $exe, $entry.FullName)
    $compileArgs += $supportSources
    $compileArgs += $extraSources

    Write-Output "Compiling $($entry.FullName)"
    & $gcc @compileArgs
    if ($LASTEXITCODE -ne 0) {
        Write-TestError "ERROR: Compile failed for $($entry.FullName)"
        $failures++
        continue
    }

    Write-Output "Running $exe"
    & $exe
    if ($LASTEXITCODE -ne 0) {
        Write-TestError "ERROR: Test failed: $($entry.FullName)"
        $failures++
    }
}

if (-not $KeepBuild) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
}

if ($failures -ne 0) {
    Write-TestError "ERROR: $failures host unit test(s) failed."
    exit 5
}

Write-Output "Host unit tests passed: $($entrySources.Count)"
exit 0
