param(
    [switch]$major,
    [switch]$minor,
    [switch]$patch,
    [string]$message = "Auto update"
)

# Ensure we are in a git repo
if (-not (Test-Path ".git")) {
    Write-Host "❌ This folder is not a Git repository." -ForegroundColor Red
    exit 1
}

# -------------------------
# Pre-deploy checks
# -------------------------
Write-Host "🔍 Running pre-deploy checks..."

# Run tests
Write-Host "🧪 Running pytest..."
$pytest = pytest --maxfail=1 --disable-warnings
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests failed! Deployment aborted." -ForegroundColor Red
    exit 1
}

# Lint
Write-Host "⚡ Running flake8..."
$flake8 = flake8 .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Lint failed! Deployment aborted." -ForegroundColor Red
    exit 1
}

# Black formatting check
Write-Host "🎨 Checking formatting with black..."
$black = black . --check
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Formatting issues detected! Deployment aborted." -ForegroundColor Red
    exit 1
}

# Mypy type check
Write-Host "📐 Running mypy..."
$mypy = mypy .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Type checking failed! Deployment aborted." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All pre-deploy checks passed!"

# -------------------------
# Versioning
# -------------------------
if (-not (Test-Path ".app_version")) {
    "0.1.0" | Out-File ".app_version"
    Write-Host "Created .app_version with default version 0.1.0"
}

$version = Get-Content ".app_version"
$parts = $version.Split(".")

$majorV = [int]$parts[0]
$minorV = [int]$parts[1]
$patchV = [int]$parts[2]

if ($major) { $majorV++; $minorV=0; $patchV=0 }
elseif ($minor) { $minorV++; $patchV=0 }
else { $patchV++ }

$newVersion = "$majorV.$minorV.$patchV"
$newVersion | Out-File ".app_version"
Write-Host "📌 Updated version: $version → $newVersion"

# -------------------------
# Git commit and push
# -------------------------
git add -A
$commitMsg = "build($newVersion): $message"
git commit -m $commitMsg
Write-Host "✔ Commit created: $commitMsg"

git tag "v$newVersion"
Write-Host "🏷 Created tag v$newVersion"

$line = "$(Get-Date -Format yyyy-MM-dd) - v$newVersion - $message"
Add-Content "CHANGELOG.md" $line
Write-Host "📝 Appended to CHANGELOG.md"

git push
git push --tags
Write-Host "🚀 Deployment complete for version $newVersion"
