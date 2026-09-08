$ErrorActionPreference = "Stop"

$containerName = "pm-mvp"
$existingContainer = docker ps -a --filter "name=^/$containerName$" --format "{{.ID}}"

if ($existingContainer) {
  docker rm -f $containerName | Out-Null
  Write-Host "Container '$containerName' stopped and removed."
}
else {
  Write-Host "Container '$containerName' was not found."
}
