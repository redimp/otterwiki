#!/bin/bash

set -euo pipefail

SCRIPT_NAME=$(basename "$0")
CONTAINER_ID=""
CONTAINER_NAME="otterwiki"
TEMPLATE="ubuntu-24.04-standard_24.04-2_amd64.tar.zst"
STORAGE="$(pvesm status -content rootdir | awk 'NR>1 && $3=="active" {print $1; exit}' || echo 'local-lvm')"
MEMORY=2048
CORES=2
DISK_SIZE="16" # in GB
NETWORK="vmbr0"
IP_ADDRESS="dhcp"
GATEWAY=""
DNS=""
SSH_KEY=""
ROOT_PASSWORD=""
GIT_REPO_URL=""
VERBOSE="false"

usage() {
    cat << EOF
Usage: $SCRIPT_NAME -i CONTAINER_ID [OPTIONS]

Creates an LXC container in Proxmox for OtterWiki

Optional:
  -i, --id CONTAINER_ID        Container ID (e.g., 100)
  -n, --name NAME              Container name (default: $CONTAINER_NAME)
  -t, --template TEMPLATE      CT template (default: $TEMPLATE)
  -s, --storage STORAGE        Storage location (default: auto-detect)
  -m, --memory MEMORY          Memory in MB (default: $MEMORY)
  -c, --cores CORES            CPU cores (default: $CORES)
  -d, --disk DISK_SIZE         Disk size (default: $DISK_SIZE)
  -b, --bridge NETWORK         Network bridge (default: $NETWORK)
  -a, --ip IP_ADDRESS          Static IP address (default: $IP_ADDRESS) CIDR format, e.g., 192.168.1.100/24
  -g, --gateway GATEWAY        Gateway IP address
  -ns, --nameserver NS         DNS nameserver(s) (default: host DNS)
  -k, --ssh-key SSH_KEY        Path to SSH public key file
  -p, --password PASSWORD      Root password (will prompt if not provided)
  -r, --repo-url URL           Git repository URL to clone (optional)
  -v, --verbose                Enable verbose output
  -h, --help                   Show this help message

Example:
  $SCRIPT_NAME -i 100 -a 192.168.1.100/24 -g 192.168.1.1 -k ~/.ssh/id_rsa.pub
EOF
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
    exit 1
}

debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] DBG: $*"
    fi
}

check_proxmox() {
    if ! command -v pct &> /dev/null; then
        error "This script must be run on a Proxmox host with pct command available"
    fi
}

check_template() {
    local template_path="/var/lib/vz/template/cache/$TEMPLATE"
    if [[ ! -f "$template_path" ]]; then
        log "Template $TEMPLATE not found, downloading..."
        pveam update
        pveam download local "$TEMPLATE" || error "Failed to download template $TEMPLATE"
    fi
}

check_storage() {
    log "Checking storage availability..."
    
    if ! pvesm status -content rootdir | grep -q "$STORAGE"; then
        log "Storage '$STORAGE' not found or not suitable for containers"
        log "Available storage options:"
        pvesm status -content rootdir | awk 'NR>1 && $3=="active" {print "  " $1}' || true
        
        # Try to auto-detect a suitable storage
        local auto_storage
        auto_storage=$(pvesm status -content rootdir | awk 'NR>1 && $3=="active" {print $1; exit}')
        if [[ -n "$auto_storage" ]]; then
            log "Auto-selecting storage: $auto_storage"
            STORAGE="$auto_storage"
        else
            error "No suitable storage found for container rootfs"
        fi
    fi
    
    log "Using storage: $STORAGE"
}

validate_container_id() {
    if [[ ! "$CONTAINER_ID" =~ ^[0-9]+$ ]]; then
        error "Container ID must be a number"
    fi
    
    if pct status "$CONTAINER_ID" &>/dev/null; then
        error "Container with ID $CONTAINER_ID already exists"
    fi
}

create_container() {
    local create_cmd=(
        pct create "$CONTAINER_ID"
        "/var/lib/vz/template/cache/$TEMPLATE"
        --hostname "$CONTAINER_NAME"
        --memory "$MEMORY"
        --cores "$CORES"
        --rootfs "$STORAGE:$DISK_SIZE"
        --features "nesting=1"
        --unprivileged 1
        --onboot 1
        --net0
    )
    
    if [[ -n "$GATEWAY" ]]; then
        create_cmd[${#create_cmd[@]}]="name=eth0,bridge=$NETWORK,firewall=1,ip=$IP_ADDRESS,gw=$GATEWAY"
    else
        create_cmd[${#create_cmd[@]}]="name=eth0,bridge=$NETWORK,firewall=1,ip=$IP_ADDRESS"
    fi

    if [[ -n "$DNS" ]]; then
        create_cmd[${#create_cmd[@]}]="--nameserver "$DNS""
    fi
    
    if [[ -n "$SSH_KEY" ]]; then
        if [[ -f "$SSH_KEY" ]]; then
            create_cmd+=(--ssh-public-keys "$SSH_KEY")
        else
            error "SSH key file not found: $SSH_KEY"
        fi
    fi
    
    if [[ -n "$ROOT_PASSWORD" ]]; then
        create_cmd+=(--password "$ROOT_PASSWORD")
    fi
    
    log "Creating container $CONTAINER_ID..."
    debug "Command: ${create_cmd[*]}"
    "${create_cmd[@]}" || error "Failed to create container"
}

setup_container() {
    log "Starting container $CONTAINER_ID..."
    pct start "$CONTAINER_ID" || error "Failed to start container"
    
    log "Waiting for container to be ready..."
    sleep 10
    
    log "Updating system packages..."
    pct exec "$CONTAINER_ID" -- bash -c "apt-get update && apt-get upgrade -y" || error "Failed to update packages"
    
    log "Installing essential packages..."
    pct exec "$CONTAINER_ID" -- bash -c "apt-get install -y curl wget git net-tools netcat-traditional python3 python3-pip python3-venv uwsgi uwsgi-plugin-python3 build-essential python3-dev libjpeg-dev zlib1g-dev libxml2-dev libxslt-dev" || error "Failed to install packages"
    
    log "Cloning OtterWiki repository..."
    pct exec "$CONTAINER_ID" -- bash -c "cd /opt && git clone https://github.com/redimp/otterwiki.git" || error "Failed to clone OtterWiki repository"
    
    log "Setting up Python virtual environment..."
    pct exec "$CONTAINER_ID" -- bash -c "cd /opt/otterwiki && python3 -m venv venv" || error "Failed to create virtual environment"
    pct exec "$CONTAINER_ID" -- bash -c "cd /opt/otterwiki && ./venv/bin/pip install -U pip uwsgi" || error "Failed to upgrade pip and install uwsgi"
    pct exec "$CONTAINER_ID" -- bash -c "cd /opt/otterwiki && ./venv/bin/pip install ." || error "Failed to install OtterWiki"
    
    log "Creating app-data directory structure..."
    pct exec "$CONTAINER_ID" -- bash -c "cd /opt/otterwiki && mkdir -p app-data/repository" || error "Failed to create app-data directory"
    
    log "Initializing data repository..."
    pct exec "$CONTAINER_ID" -- bash -c "cd /opt/otterwiki/app-data/repository && git init -b main" || error "Failed to initialize repository"
    
    log "Creating OtterWiki configuration..."
    pct exec "$CONTAINER_ID" -- bash -c "cd /opt/otterwiki && python3 -c \"
import secrets
with open('settings.cfg', 'w') as f:
    f.write('''REPOSITORY = '/opt/otterwiki/app-data/repository'
SQLALCHEMY_DATABASE_URI = 'sqlite:////opt/otterwiki/app-data/db.sqlite'
SECRET_KEY = '{}' 
OTTERWIKI_NAME = 'OtterWiki'
OTTERWIKI_MAIL_DEFAULT_SENDER = 'otterwiki@localhost'
OTTERWIKI_WELCOME_PAGE = 'Home'
'''.format(secrets.token_hex()))
\""
    
    if [[ -n "$GIT_REPO_URL" ]]; then
        log "Cloning wiki content repository from $GIT_REPO_URL..."
        pct exec "$CONTAINER_ID" -- bash -c "cd /opt/otterwiki/app-data && rm -rf repository && git clone '$GIT_REPO_URL' repository" || error "Failed to clone repository"
    fi
    
    log "Setting ownership..."
    pct exec "$CONTAINER_ID" -- chown -R www-data:www-data /opt/otterwiki
    
    log "Creating systemd service for OtterWiki..."
    pct exec "$CONTAINER_ID" -- tee /etc/systemd/system/otterwiki.service > /dev/null << 'EOF'
[Unit]
Description=uWSGI server for OtterWiki
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/otterwiki
Environment=OTTERWIKI_SETTINGS=/opt/otterwiki/settings.cfg
ExecStart=/opt/otterwiki/venv/bin/uwsgi --http 0.0.0.0:8080 --master --enable-threads --die-on-term -w otterwiki.server:app
Restart=always
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF
    
    log "Enabling and starting OtterWiki service..."
    pct exec "$CONTAINER_ID" -- systemctl daemon-reload
    pct exec "$CONTAINER_ID" -- systemctl enable otterwiki.service
    pct exec "$CONTAINER_ID" -- systemctl start otterwiki.service
    
    log "Container setup completed successfully!"
    log "Container ID: $CONTAINER_ID"
    log "Container Name: $CONTAINER_NAME"
    
    if [[ -n "$IP_ADDRESS" ]]; then
        log "IP Address: $IP_ADDRESS"
    else
        local container_ip
        container_ip=$(pct exec "$CONTAINER_ID" -- ip route get 1 | awk '{print $7}' | head -1)
        log "IP Address: $container_ip (DHCP)"
    fi
    
    log ""
    log "To access the container:"
    log "  pct enter $CONTAINER_ID"
    log ""
    log "Access OtterWiki at:"
    if [[ -n "$IP_ADDRESS" ]]; then
        log "  http://${IP_ADDRESS%/*}:8080"
    else
        log "  http://[container-ip]:8080"
    fi
    log ""
    log "Service management:"
    log "  systemctl status otterwiki"
    log "  systemctl restart otterwiki"
    log "  systemctl stop otterwiki"
    log ""
    log "First registered user will become the admin."
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--id)
            CONTAINER_ID="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -t|--template)
            TEMPLATE="$2"
            shift 2
            ;;
        -s|--storage)
            STORAGE="$2"
            shift 2
            ;;
        -m|--memory)
            MEMORY="$2"
            shift 2
            ;;
        -c|--cores)
            CORES="$2"
            shift 2
            ;;
        -d|--disk)
            DISK_SIZE="$2"
            shift 2
            ;;
        -b|--bridge)
            NETWORK="$2"
            shift 2
            ;;
        -a|--ip)
            IP_ADDRESS="$2"
            shift 2
            ;;
        -g|--gateway)
            GATEWAY="$2"
            shift 2
            ;;
        -ns|--nameserver)
            DNS="$2"
            shift 2
            ;;
        -k|--ssh-key)
            SSH_KEY="$2"
            shift 2
            ;;
        -p|--password)
            ROOT_PASSWORD="$2"
            shift 2
            ;;
        -r|--repo-url)
            GIT_REPO_URL="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

if [[ -z "$CONTAINER_ID" ]]; then
    echo -n "Enter the container ID: "
    read CONTAINER_ID
fi

if [[ -z "$CONTAINER_ID" ]]; then
    error "Container ID is required!"
fi

if [[ -z "$ROOT_PASSWORD" && -z "$SSH_KEY" ]]; then
    echo -n "Enter root password for the container: "
    read -s ROOT_PASSWORD
    echo
fi

log "Starting LXC container creation process..."
check_proxmox
validate_container_id
check_storage
check_template
create_container
setup_container

log "LXC container creation completed successfully!"