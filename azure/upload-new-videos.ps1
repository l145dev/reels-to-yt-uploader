$vmIp = "20.199.136.72"
$keyPath = "azure/chessbot-backend_key.pem"
$remoteUser = "azureuser"

# Command to just upload new videos without restarting anything
scp -i $keyPath ./new_videos/* $remoteUser@$vmIp:~/scheduler_data/videos/

# Delete all from new_videos folder
Remove-Item -Path "./new_videos/*" -Recurse -Force
