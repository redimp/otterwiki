# Proxmox LXC Setup for OtterWiki

This directory contains scripts and documentation for deploying OtterWiki in Proxmox LXC containers.

## Overview

The `setup-otterwiki-lxc.sh` script automates the creation and configuration of an LXC container in Proxmox VE for running OtterWiki. It handles everything from container creation to service configuration, providing a ready-to-use OtterWiki installation.

## Features

- **Ubuntu 24.04 LTS**: Uses the latest Ubuntu LTS template
- **Official Installation**: Follows [OtterWiki official installation guidelines](https://otterwiki.com/Installation#from-source-as-wsgi-application-with-uwsgi)
- **Source Installation**: Clones from official GitHub repository for latest features
- **Automated Setup**: Complete installation and configuration of OtterWiki
- **Flexible Configuration**: Customizable resources, networking, and authentication
- **Production Ready**: Includes uWSGI with systemd for reliable service management
- **Host DNS Integration**: Automatically uses host DNS settings as default

## Requirements

- Proxmox VE 7.0 or later
- Root access to Proxmox host
- Available container ID number
- Network bridge configured (default: vmbr0)
- Storage pool available (default: local-lvm)

## Quick Start

### Execute Directly from GitHub

Run the script directly from the repository without cloning:

```bash
# Basic usage with DHCP
curl -fsSL https://raw.githubusercontent.com/redimp/otterwiki/main/proxmox/setup-otterwiki-lxc.sh | bash

# With static IP and SSH key
curl -fsSL https://raw.githubusercontent.com/redimp/otterwiki/main/proxmox/setup-otterwiki-lxc.sh | bash -s -- -i 100 -a 192.168.1.100/24 -g 192.168.1.1 -k ~/.ssh/id_rsa.pub
```

### Local Usage

After cloning or downloading the script locally:

#### Basic Usage

Create a container with DHCP networking:

```bash
./setup-otterwiki-lxc.sh
```

#### Advanced Usage

Create a container with static IP and SSH key authentication:

```bash
./setup-otterwiki-lxc.sh \
  -i 100 \
  -n "otterwiki-prod" \
  -a 192.168.1.100/24 \
  -g 192.168.1.1 \
  -k ~/.ssh/id_rsa.pub \
  -r https://github.com/user/my-wiki.git \
  -m 4096 \
  -c 4
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i, --id` | Container ID (required) | - |
| `-n, --name` | Container hostname | otterwiki |
| `-t, --template` | Ubuntu template | ubuntu-24.04-standard_24.04-2_amd64.tar.zst |
| `-s, --storage` | Storage pool | auto-detect |
| `-m, --memory` | Memory in MB | 2048 |
| `-c, --cores` | CPU cores | 2 |
| `-d, --disk` | Disk size | 20G |
| `-b, --bridge` | Network bridge | vmbr0 |
| `-a, --ip` | Static IP (CIDR format) | DHCP |
| `-g, --gateway` | Gateway IP | - |
| `-ns, --nameserver` | DNS server | Host DNS |
| `-k, --ssh-key` | SSH public key file | - |
| `-p, --password` | Root password | Interactive prompt |
| `-r, --repo-url` | Git repository URL to clone | - |
| `-h, --help` | Show help message | - |

## What the Script Does

1. **Validation**: Checks Proxmox environment and container ID availability
2. **Template Management**: Downloads Ubuntu 24.04 template if not present
3. **Container Creation**: Creates LXC container with specified configuration
4. **System Setup**: Updates packages and installs dependencies
5. **OtterWiki Installation**: Clones from source and sets up Python environment
6. **Service Configuration**: Configures uWSGI with systemd service
7. **Data Setup**: Initializes git repository and configuration files

## Post-Installation

### Accessing OtterWiki

After successful installation:

- **Web Interface**: `http://[container-ip]:8080`
- **Container Shell**: `pct enter [container-id]`
- **First User**: The first registered user becomes the admin

### Container Management

```bash
# Start container
pct start <container-id>

# Stop container
pct stop <container-id>

# Enter container
pct enter <container-id>

# View container status
pct status <container-id>

# Delete container
pct destroy <container-id>
```

### Service Management (inside container)

```bash
# Check service status
systemctl status otterwiki

# Restart service
systemctl restart otterwiki

# Stop service
systemctl stop otterwiki

# View logs
journalctl -u otterwiki -f
```

## Configuration Files

Key configuration files in the container:

- **OtterWiki Config**: `/opt/otterwiki/settings.cfg`
- **Systemd Service**: `/etc/systemd/system/otterwiki.service`
- **Virtual Environment**: `/opt/otterwiki/venv/`

## Data Persistence

- **Wiki Data**: `/opt/otterwiki/app-data/repository` (git repository)
- **Database**: `/opt/otterwiki/app-data/db.sqlite`
- **Configuration**: `/opt/otterwiki/settings.cfg`

## Networking Examples

### Static IP Configuration

```bash
# Single static IP
./setup-otterwiki-lxc.sh -i 100 -a 192.168.1.100/24 -g 192.168.1.1

# Custom DNS server
./setup-otterwiki-lxc.sh -i 100 -a 192.168.1.100/24 -g 192.168.1.1 -ns 1.1.1.1
```

### Different Network Bridge

```bash
# Use custom bridge
./setup-otterwiki-lxc.sh -i 100 -b vmbr1
```

## Troubleshooting

### Common Issues

1. **Storage Error** (`no such logical volume`): 
   - The script now auto-detects available storage
   - To manually specify: `./setup-otterwiki-lxc.sh -i 100 -s local`
   - Check available storage: `pvesm status -content rootdir`

2. **Template Download Fails**: Check internet connectivity and Proxmox subscription

3. **Container ID Exists**: Use a different ID or remove existing container

4. **Network Issues**: Verify bridge configuration and IP ranges

5. **SSH Key Not Found**: Ensure path to SSH key file is correct

### Log Locations

- **Container Creation**: Script output shows detailed progress
- **Service Logs**: Available via `journalctl -u otterwiki`
- **System Logs**: `/var/log/` in container

### Getting Help

For issues with:
- **Script**: Check script output and container logs
- **OtterWiki**: Consult [OtterWiki documentation](https://otterwiki.com/)
- **Proxmox**: Check Proxmox VE documentation

## Security Considerations

- Secret key is auto-generated during installation in `/opt/otterwiki/settings.cfg`
- Configure proper firewall rules
- Use SSH key authentication when possible
- Regularly update container packages
- Monitor container resource usage

## Optional: Git Repository Synchronization

If you've cloned an existing wiki repository using the `-r` option, you may want to set up automatic synchronization with the remote repository.

### Setting Up Periodic Sync (Optional)

To automatically sync changes with the remote repository, you can set up a cron job inside the container:

1. **Enter the container**:
   ```bash
   pct enter <container-id>
   ```

2. **Switch to the www-data user**:
   ```bash
   sudo -u www-data -s
   ```

3. **Navigate to the repository**:
   ```bash
   cd /opt/otterwiki/app-data/repository
   ```

4. **Create a sync script**:
   ```bash
   cat > /opt/otterwiki/sync-repo.sh << 'EOF'
   #!/bin/bash
   cd /opt/otterwiki/app-data/repository
   
   # Pull latest changes from remote
   git fetch origin
   git merge origin/main 2>/dev/null || git merge origin/master 2>/dev/null
   
   # Push any local changes
   git push origin 2>/dev/null || true
   
   echo "$(date): Repository sync completed" >> /var/log/otterwiki-sync.log
   EOF
   
   chmod +x /opt/otterwiki/sync-repo.sh
   chown www-data:www-data /opt/otterwiki/sync-repo.sh
   ```

5. **Set up the cron job** (as www-data user):
   ```bash
   crontab -e
   ```
   
   Add this line to sync every 30 minutes:
   ```
   */30 * * * * /opt/otterwiki/sync-repo.sh
   ```

### Important Notes

- **Backup First**: Always backup your data before setting up automatic sync
- **Conflict Resolution**: The script handles simple merges but may fail on conflicts
- **Authentication**: Ensure the container has appropriate git credentials configured
- **Monitoring**: Check `/var/log/otterwiki-sync.log` for sync status
- **Testing**: Test the sync script manually before enabling the cron job

### Alternative: Manual Sync

For manual synchronization, you can run these commands inside the container:

```bash
# Enter container and switch to www-data
pct enter <container-id>
sudo -u www-data -s
cd /opt/otterwiki/app-data/repository

# Pull changes
git pull origin main  # or master

# Push changes
git push origin main  # or master
```

## Customization

The script can be modified to:
- Install additional packages
- Configure different web servers
- Adjust service configurations
- Set up SSL certificates
- Configure backup scripts

## License

This script is part of the OtterWiki project and follows the same licensing terms.