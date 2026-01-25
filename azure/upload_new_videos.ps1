# Load .env file
$envPath = "azure/.env"
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        $line = $_.Trim()
        if ($line -notmatch "^#" -and $line -match "=") {
            $name, $value = $line -split "=", 2
            $value = $value.Trim('"').Trim("'") # Remove quotes
            Set-Variable -Name $name -Value $value
        }
    }
} else {
    Write-Error "Error: 'azure/.env' file not found. Please create it with VM_PUBLIC_IP, KEY_NAME, and VM_USERNAME."
    exit 1
}

$vmIp = $VM_PUBLIC_IP
$keyPath = "azure/${KEY_NAME}.pem"
$remoteUser = $VM_USERNAME

# Command to just upload new videos without restarting anything
scp -i $keyPath ./new_videos/* $remoteUser@$vmIp:~/scheduler_data/videos/

# Delete all from new_videos folder
Remove-Item -Path "./new_videos/*" -Recurse -Force
