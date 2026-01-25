# deploy-scheduler.ps1
# Usage: pwsh ./deploy-scheduler.ps1

# Configuration
$vmIp = "20.199.136.72"
$keyPath = "azure/chessbot-backend_key.pem" # run from project root
$remoteUser = "azureuser"
$tempDir = "dist_scheduler_temp"

Write-Host "Starting Scheduler Deployment to Azure ($vmIp)..." -ForegroundColor Cyan

# 1. Clean up & Create Temp Directory
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# 2. Bundle ONLY Code & Configs (No Videos)
Write-Host "Bundling necessary files..." -ForegroundColor Yellow

# Copy Core Files
Copy-Item "azure/Dockerfile"          -Destination "$tempDir/Dockerfile"
Copy-Item "upload_vids.py"      -Destination "$tempDir/upload_vids.py"
Copy-Item "requirements.txt"    -Destination "$tempDir/requirements.txt"

# Copy Auth & Initial State
# We copy state here, but the server logic decides whether to use it (to prevent overwriting progress)
Copy-Item "client_secrets.json" -Destination "$tempDir/client_secrets.json"
Copy-Item "token.json"          -Destination "$tempDir/token.json"
Copy-Item "schedule_state.json" -Destination "$tempDir/schedule_state.json"

# 3. Upload to Azure
Write-Host "☁️ Uploading payload..." -ForegroundColor Yellow

# Clean the BUILD folder (Code), but leave DATA folder alone
ssh -i $keyPath -o StrictHostKeyChecking=no ${remoteUser}@${vmIp} "rm -rf ~/scheduler_build"
# Upload new bundle
scp -i $keyPath -r $tempDir "${remoteUser}@${vmIp}:~/scheduler_build"

# 4. Remote Execution (Build & Run)
Write-Host "Building and Configuring on VM..." -ForegroundColor Yellow

$commands = @(
    # A. Setup Persistent Data Folder (If not exists)
    "mkdir -p ~/scheduler_data/videos",

    # B. Smart State Handling
    # If state file doesn't exist on server, copy the one we just uploaded.
    # If it DOES exist, we ignore the upload to prevent overwriting the bot's progress.
    "if [ ! -f ~/scheduler_data/schedule_state.json ]; then cp ~/scheduler_build/schedule_state.json ~/scheduler_data/schedule_state.json; fi",

    # C. Build Docker Image
    "cd ~/scheduler_build",
    "sudo docker build -t youtube-scheduler .",

    # D. Stop Old Container
    "sudo docker rm -f scheduler || true",

    # E. Run New Container
    # Note the Volume Mounts: We map the PERSISTENT data folder, not the build folder.
    "sudo docker run -d \
        --name scheduler \
        --restart unless-stopped \
        -v /etc/timezone:/etc/timezone:ro \
        -v /etc/localtime:/etc/localtime:ro \
        -v ~/scheduler_data/videos:/app/videos \
        -v ~/scheduler_data/schedule_state.json:/app/schedule_state.json \
        youtube-scheduler"
)

ssh -i $keyPath ${remoteUser}@${vmIp} ($commands -join " && ")

# 5. Cleanup Local Temp
Remove-Item -Recurse -Force $tempDir
Write-Host "✅ Scheduler Deployed! Running at 11 PM CEST." -ForegroundColor Green