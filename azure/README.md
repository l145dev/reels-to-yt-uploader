# Azure Deployment for YouTube Scheduler

This directory contains the necessary scripts and configuration to deploy the YouTube Scheduler to an Azure VM using Docker.

## Overview

The deployment process involves:

1.  **Bundling**: Gathering all necessary code, configuration, and authentication files locally.
2.  **Upload**: Sending the bundle to the Azure VM via SSH/SCP.
3.  **Remote Execution**: Building the Docker image on the VM and running the container with persistent volumes.

## Prerequisites

### 1. Azure VM

- An Azure VM (e.g., Ubuntu) with Docker installed.
- **IP Address**: Currently configured as `20.199.136.72` in `server_to_cloud.ps1`. (replace `20.199.136.72` with your VM's IP address)
- **User**: `azureuser`. (replace `azureuser` with your VM's username)

### 2. Authentication Files

Ensure the following files are present in the project root (they are **ignored** by git for security):

- `client_secrets.json`: Google Cloud OAuth credentials (Desktop App).
- `token.json`: Generated after the first local run (stores the refresh token).
- `azure/{key}.pem`: SSH private key for the Azure VM. (replace `{key}` with your key's name)

### 3. State Management

- `schedule_state.json`: Tracks the last upload date. This file is preserved on the server during deployments to prevent re-uploading or schedule conflicts.

## Deployment Script

The main deployment logic is handled by `server_to_cloud.ps1`.

### Usage

Run the script from the **project root**:

```powershell
pwsh ./azure/server_to_cloud.ps1
```

### What the script does:

1.  **Cleans** any previous local temporary bundles (`dist_scheduler_temp`).
2.  **Copies** source code (`upload_vids.py`, `Dockerfile`, `requirements.txt`) and secrets to the temp folder.
3.  **Uploads** the temp folder to `~/scheduler_build` on the VM.
4.  **Connects** to the VM via SSH to:
    - Create the persistent data directory: `~/scheduler_data/videos`.
    - Backup/Initialize `schedule_state.json` in `~/scheduler_data/` if it doesn't exist.
    - Build the Docker image (`youtube-scheduler`).
    - Stop and remove any existing `scheduler` container.
    - Run the new container with volume mounts.

## Docker Configuration

The `Dockerfile` in this directory handles the environment setup (Python 3.11+, Dependencies).

**Volume Mounts:**

- `/app/videos` -> `~/scheduler_data/videos`: Defines where the downloaded videos are stored.
- `/app/schedule_state.json` -> `~/scheduler_data/schedule_state.json`: Persists the scheduling state.
- `/etc/timezone` & `/etc/localtime`: Syncs container time with host time (crucial for cron/scheduled jobs).

## Maintenance

### Check Logs

To check the logs of the running scheduler on the VM:

```bash
ssh -i azure/{key}.pem {VM_username}@{VM_PUBLIC_IP} "sudo docker logs -f scheduler"
```

### Manual Restart

If you need to manually restart the container without redeploying:

```bash
ssh -i azure/{key}.pem {VM_username}@{VM_PUBLIC_IP} "sudo docker restart scheduler"
```
