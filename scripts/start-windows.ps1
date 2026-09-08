$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Resolve-Path (Join-Path $scriptDir "..")
$imageName = "pm-mvp:part2"
$containerName = "pm-mvp"

function Invoke-Docker {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Args
  )

  & docker @Args
  if ($LASTEXITCODE -ne 0) {
    throw "docker $($Args -join ' ') failed with exit code $LASTEXITCODE"
  }
}

Push-Location $rootDir
try {
  Invoke-Docker -Args @("info") | Out-Null

  Invoke-Docker -Args @("build", "-t", $imageName, ".")

  $existingContainer = & docker ps -a --filter "name=^/$containerName$" --format "{{.ID}}"
  if ($LASTEXITCODE -ne 0) {
    throw "docker ps failed with exit code $LASTEXITCODE"
  }

  if ($existingContainer) {
    Invoke-Docker -Args @("rm", "-f", $containerName) | Out-Null
  }

  Invoke-Docker -Args @("run", "-d", "--name", $containerName, "-p", "8000:8000", $imageName) | Out-Null
  Write-Host "Container '$containerName' started at http://127.0.0.1:8000"
}
finally {
  Pop-Location
}
