#!/bin/bash

# Oracle Cloud Development Server Deployment Script
# This script automates the complete setup of an Oracle Cloud development server

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/terraform"
SSH_CONFIG="$HOME/.ssh/config"
SSH_KEY_NAME="oci-dev-key"
SERVER_HOSTNAME="oracle-dev-server"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if OCI CLI is installed
    if ! command -v oci &> /dev/null; then
        error "OCI CLI is not installed. Please install it first: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm"
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        error "Terraform is not installed. Please install it first: https://learn.hashicorp.com/tutorials/terraform/install-cli"
    fi
    
    # Check if OCI CLI is configured
    if ! oci setup config &> /dev/null; then
        warning "OCI CLI might not be configured. Please ensure it's set up with 'oci setup config'"
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        error "jq is not installed. Please install it: sudo apt-get install jq (Ubuntu/Debian) or brew install jq (macOS)"
    fi
    
    log "Prerequisites check completed ✓"
}

# Get Oracle Cloud configuration
get_oci_config() {
    log "Retrieving Oracle Cloud configuration..."
    
    # Get the default config file location
    OCI_CONFIG_FILE="${HOME}/.oci/config"
    
    if [[ ! -f "$OCI_CONFIG_FILE" ]]; then
        error "OCI config file not found at $OCI_CONFIG_FILE. Please run 'oci setup config' first."
    fi
    
    # Extract configuration values
    export TF_VAR_tenancy_ocid=$(grep "tenancy" "$OCI_CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')
    export TF_VAR_user_ocid=$(grep "user" "$OCI_CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')
    export TF_VAR_fingerprint=$(grep "fingerprint" "$OCI_CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')
    export TF_VAR_region=$(grep "region" "$OCI_CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')
    export TF_VAR_private_key_path=$(grep "key_file" "$OCI_CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')
    
    # Get compartment ID
    export TF_VAR_compartment_id=$(oci iam compartment list --compartment-id-in-subtree true --query "data[0].id" --raw-output)
    
    # Get Ubuntu image ID for the region
    export TF_VAR_ubuntu_image_id=$(oci compute image list --compartment-id "$TF_VAR_compartment_id" --operating-system "Ubuntu" --operating-system-version "22.04" --shape "VM.Standard.E2.1.Micro" --sort-by "TIMECREATED" --order-by "DESC" --query "data[0].id" --raw-output)
    
    log "Oracle Cloud configuration retrieved ✓"
}

# Initialize Terraform
init_terraform() {
    log "Initializing Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    terraform init
    
    log "Terraform initialized ✓"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log "Deploying Oracle Cloud infrastructure..."
    
    cd "$TERRAFORM_DIR"
    
    # Plan and apply
    info "Running Terraform plan..."
    terraform plan -out=tfplan
    
    info "Applying Terraform configuration..."
    terraform apply -auto-approve tfplan
    
    log "Infrastructure deployed ✓"
}

# Get deployment outputs
get_deployment_outputs() {
    log "Extracting deployment outputs..."
    
    cd "$TERRAFORM_DIR"
    
    # Get public IP and SSH key path
    PUBLIC_IP=$(terraform output -raw public_ip)
    SSH_KEY_PATH=$(terraform output -raw ssh_key_path)
    INSTANCE_NAME=$(terraform output -raw instance_name)
    
    log "Deployment outputs extracted ✓"
    info "Public IP: $PUBLIC_IP"
    info "SSH Key: $SSH_KEY_PATH"
}

# Wait for SSH to be available
wait_for_ssh() {
    log "Waiting for SSH to become available..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@"$PUBLIC_IP" "echo 'SSH is ready'" &>/dev/null; then
            log "SSH is ready ✓"
            return 0
        fi
        
        info "Attempt $attempt/$max_attempts: SSH not ready, waiting 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    error "SSH did not become available after $max_attempts attempts"
}

# Update SSH config with security
update_ssh_config() {
    log "Updating SSH configuration with security..."
    
    # Backup existing SSH config
    if [[ -f "$SSH_CONFIG" ]]; then
        cp "$SSH_CONFIG" "$SSH_CONFIG.backup.$(date +%s)"
        info "SSH config backed up"
    fi
    
    # Get SSH host key before adding to config
    log "Retrieving SSH host key for security..."
    ssh-keyscan -H "$PUBLIC_IP" > "$SCRIPT_DIR/known_hosts.tmp" 2>/dev/null
    
    # Remove existing entry for this host if it exists
    if grep -q "Host $SERVER_HOSTNAME" "$SSH_CONFIG" 2>/dev/null; then
        sed -i "/Host $SERVER_HOSTNAME/,/^$/d" "$SSH_CONFIG"
        info "Removed existing SSH config entry for $SERVER_HOSTNAME"
    fi
    
    # Add new SSH config entry with enhanced security
    cat >> "$SSH_CONFIG" << EOF

# Oracle Cloud Development Server - Auto-generated
Host $SERVER_HOSTNAME
    HostName $PUBLIC_IP
    User ubuntu
    IdentityFile $SSH_KEY_PATH
    UserKnownHostsFile $SCRIPT_DIR/known_hosts.tmp
    StrictHostKeyChecking yes
    LogLevel INFO
    ServerAliveInterval 60
    ServerAliveCountMax 3
    IdentitiesOnly yes
    PasswordAuthentication no
    PubkeyAuthentication yes

EOF
    
    # Set proper permissions
    chmod 600 "$SCRIPT_DIR/known_hosts.tmp"
    chmod 600 "$SSH_CONFIG"
    
    log "SSH configuration updated with security ✓"
}

# Test SSH connection
test_ssh_connection() {
    log "Testing SSH connection..."
    
    if ssh "$SERVER_HOSTNAME" "echo 'SSH connection successful'"; then
        log "SSH connection test passed ✓"
    else
        error "SSH connection test failed"
    fi
}

# Setup additional development tools on remote server
setup_remote_dev_tools() {
    log "Setting up additional development tools on remote server..."
    
    # Copy setup script to remote server
    scp "$SCRIPT_DIR/remote-setup.sh" "$SERVER_HOSTNAME:/tmp/"
    
    # Execute setup script on remote server
    ssh "$SERVER_HOSTNAME" "chmod +x /tmp/remote-setup.sh && sudo /tmp/remote-setup.sh"
    
    log "Remote development tools setup completed ✓"
}

# Verify development environment is working
verify_development_environment() {
    log "Verifying development environment..."
    
    local failed_services=()
    
    # Test Docker
    if ! ssh "$SERVER_HOSTNAME" "docker --version" &>/dev/null; then
        failed_services+=("Docker")
    fi
    
    # Test Node.js
    if ! ssh "$SERVER_HOSTNAME" "node --version" &>/dev/null; then
        failed_services+=("Node.js")
    fi
    
    # Test Python
    if ! ssh "$SERVER_HOSTNAME" "python3 --version" &>/dev/null; then
        failed_services+=("Python")
    fi
    
    # Test Git
    if ! ssh "$SERVER_HOSTNAME" "git --version" &>/dev/null; then
        failed_services+=("Git")
    fi
    
    # Test Docker functionality
    if ! ssh "$SERVER_HOSTNAME" "sudo docker run --rm hello-world" &>/dev/null; then
        failed_services+=("Docker functionality")
    fi
    
    # Check if any services failed
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        error "Development environment verification failed for: ${failed_services[*]}"
    fi
    
    log "Development environment verification passed ✓"
}

# Create Windsurf action
create_windsurf_action() {
    log "Creating Windsurf action..."
    
    local windsurf_dir="${SCRIPT_DIR}/.windsurf/actions"
    mkdir -p "$windsurf_dir"
    
    cat > "$windsurf_dir/deploy-oracle-server.json" << EOF
{
  "name": "Deploy Oracle Cloud Development Server",
  "description": "Deploy a complete Oracle Cloud development server with all tools installed",
  "command": "${SCRIPT_DIR}/deploy-oracle-server.sh",
  "category": "Infrastructure",
  "icon": "🚀",
  "parameters": [],
  "workingDirectory": "${SCRIPT_DIR}",
  "environment": {
    "OCI_CLI_AUTH": "api_key"
  }
}
EOF
    
    log "Windsurf action created ✓"
}

# Print success message
print_success() {
    log "🎉 Oracle Cloud Development Server deployment completed successfully!"
    
    echo ""
    echo "📋 Connection Details:"
    echo "   Host: $SERVER_HOSTNAME"
    echo "   IP: $PUBLIC_IP"
    echo "   User: ubuntu"
    echo "   SSH Key: $SSH_KEY_PATH"
    echo ""
    echo "🔧 Connect with:"
    echo "   ssh $SERVER_HOSTNAME"
    echo ""
    echo "📁 Open in VS Code:"
    echo "   code --remote ssh-remote+$SERVER_HOSTNAME /home/ubuntu"
    echo ""
    echo "🌐 Server includes:"
    echo "   • Ubuntu 22.04 LTS"
    echo "   • Docker & Docker Compose"
    echo "   • Node.js 18.x"
    echo "   • Python 3"
    echo "   • Git"
    echo "   • Oh My Zsh"
    echo ""
    echo "⚡ Windsurf action created for one-click redeployment!"
}

# Main execution
main() {
    echo "🚀 Oracle Cloud Development Server Deployment"
    echo "=============================================="
    echo ""
    
    check_prerequisites
    get_oci_config
    init_terraform
    
    # Ask for confirmation before deployment
    echo ""
    warning "This will deploy resources to your Oracle Cloud account."
    warning "You may incur costs if you exceed the free tier limits."
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Deployment cancelled."
        exit 0
    fi
    
    deploy_infrastructure
    get_deployment_outputs
    wait_for_ssh
    update_ssh_config
    test_ssh_connection
    setup_remote_dev_tools
    verify_development_environment
    create_windsurf_action
    print_success
}

# Run main function
main "$@"
