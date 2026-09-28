# Import a local, untracked .env file into the CURRENT PowerShell process.
# Never print values or commit .env. Only simple NAME=value lines are supported.
param([string]$Path = (Join-Path (Split-Path $PSScriptRoot -Parent) '.env'))

if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "Environment file not found. Create .env from .env.example first."
}

foreach ($line in (Get-Content -LiteralPath $Path)) {
    $line = $line.Trim()
    if (-not $line -or $line.StartsWith('#')) { continue }
    $separator = $line.IndexOf('=')
    if ($separator -lt 1) { throw "Invalid .env line. Expected NAME=value." }
    $name = $line.Substring(0, $separator).Trim()
    if ($name -cnotmatch '^[A-Z][A-Z0-9_]*$') { throw "Invalid environment variable name." }
    $value = $line.Substring($separator + 1).Trim()
    if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or
        ($value.StartsWith("'") -and $value.EndsWith("'")))) {
        $value = $value.Substring(1, $value.Length - 2)
    }
    Set-Item -Path "Env:$name" -Value $value
}