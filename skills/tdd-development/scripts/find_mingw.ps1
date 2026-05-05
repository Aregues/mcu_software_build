param(
    [switch]$Quiet
)

function Find-MingwGcc {
    $paths = @()

    if ($env:PATH) {
        $paths += $env:PATH -split [System.IO.Path]::PathSeparator
    }

    $paths += @(
        'C:\msys64\mingw64\bin',
        'C:\msys64\ucrt64\bin',
        'C:\msys64\mingw32\bin',
        'C:\MinGW\bin'
    )

    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

    foreach ($dir in $paths) {
        if ([string]::IsNullOrWhiteSpace($dir)) {
            continue
        }

        $expanded = [Environment]::ExpandEnvironmentVariables($dir.Trim('"'))
        if (-not $seen.Add($expanded)) {
            continue
        }

        $candidate = Join-Path $expanded 'gcc.exe'
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $null
}

if ($MyInvocation.InvocationName -ne '.') {
    $gcc = Find-MingwGcc
    if ($gcc) {
        if ($Quiet) {
            Write-Output $gcc
        } else {
            Write-Output "Found MinGW gcc: $gcc"
        }
        exit 0
    }

    $message = 'MinGW gcc.exe not found in PATH or common locations: C:\msys64\mingw64\bin, C:\msys64\ucrt64\bin, C:\msys64\mingw32\bin, C:\MinGW\bin'
    if ($Quiet) {
        Write-Output $message
    } else {
        Write-Error $message
    }
    exit 1
}
