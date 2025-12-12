#!/bin/bash

# Oracle Cloud A1.Flex Deployment Retry Script
# Continuously attempts deployment until capacity becomes available

set -e

# Configuration
MAX_ATTEMPTS=1440  # Try for 24 hours (1 attempt per minute)
BASE_DELAY=60      # Start with 1 minute delay
MAX_DELAY=1800     # Max delay of 30 minutes
LOG_FILE="a1-flex-deploy.log"
SUCCESS_FILE="deployment-success.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Success notification
notify_success() {
    local ip="$1"
    log "${GREEN}🎉 SUCCESS! A1.Flex instance deployed successfully!${NC}"
    log "${GREEN}📍 Public IP: $ip${NC}"
    log "${GREEN}🔑 SSH Key: ~/.ssh/oci-dev-key${NC}"
    log "${GREEN}🚀 Connect with: ssh -i ~/.ssh/oci-dev-key ubuntu@$ip${NC}"
    
    # Create success file
    cat > "$SUCCESS_FILE" << EOF
Oracle Cloud A1.Flex Deployment Successful! 🎉

Instance Details:
- Public IP: $ip
- SSH Key: ~/.ssh/oci-dev-key
- Connect: ssh -i ~/.ssh/oci-dev-key ubuntu@$ip
- Specs: 4 OCPUs, 24GB RAM, 200GB Storage

Deployment completed at: $(date)
EOF
    
    # Send desktop notification if available
    if command -v notify-send &> /dev/null; then
        notify-send "Oracle Cloud A1.Flex Deployed" "IP: $ip | Ready to connect!"
    fi
    
    exit 0
}

# Calculate exponential backoff delay
calculate_delay() {
    local attempt="$1"
    local delay=$((BASE_DELAY * (2 ** (attempt / 10))))
    
    # Cap at MAX_DELAY
    if [ "$delay" -gt "$MAX_DELAY" ]; then
        delay="$MAX_DELAY"
    fi
    
    # Add random jitter (±20%)
    local jitter=$((delay / 5))
    local random_jitter=$((RANDOM % (jitter * 2) - jitter))
    delay=$((delay + random_jitter))
    
    echo "$delay"
}

# Check if it's off-peak hours (better chance of capacity)
is_off_peak() {
    local hour=$(date +%H)
    # Off-peak: 10 PM - 6 AM Sydney time (12-20 UTC)
    [ "$hour" -ge 12 ] || [ "$hour" -le 20 ]
}

# Deploy function
deploy_a1_flex() {
    local attempt="$1"
    
    log "${BLUE}🔄 Attempt $attempt/$MAX_ATTEMPTS: Deploying A1.Flex instance...${NC}"
    
    # Clean up any existing state
    cd terraform
    rm -rf .terraform* terraform.tfstate* 2>/dev/null || true
    
    # Initialize and apply
    if terraform init -upgrade >/dev/null 2>&1 && \
       terraform apply -auto-approve >/dev/null 2>&1; then
        
        # Get the public IP
        local public_ip=$(terraform output -raw public_ip 2>/dev/null || echo "")
        
        if [ -n "$public_ip" ]; then
            cd ..
            notify_success "$public_ip"
        else
            cd ..
            log "${YELLOW}⚠️  Deployment succeeded but couldn't retrieve IP${NC}"
            return 1
        fi
    else
        cd ..
        return 1
    fi
}

# Main retry loop
main() {
    log "${BLUE}🚀 Starting Oracle Cloud A1.Flex deployment retry script${NC}"
    log "${BLUE}📍 Target: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM, 200GB Storage)${NC}"
    log "${BLUE}🌍 Region: ap-sydney-1${NC}"
    log "${BLUE}⏰ Max attempts: $MAX_ATTEMPTS (~24 hours)${NC}"
    
    # Clean up any previous success file
    rm -f "$SUCCESS_FILE"
    
    for attempt in $(seq 1 $MAX_ATTEMPTS); do
        # Check if we should prioritize off-peak hours
        if is_off_peak; then
            log "${YELLOW}🌙 Off-peak hours detected - better chance of capacity!${NC}"
        else
            log "${YELLOW}☀️ Peak hours - capacity may be limited, trying anyway...${NC}"
        fi
        
        # Attempt deployment
        if deploy_a1_flex "$attempt"; then
            exit 0
        fi
        
        # Calculate delay for next attempt
        if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
            local delay=$(calculate_delay "$attempt")
            local delay_minutes=$((delay / 60))
            
            log "${YELLOW}⏳ Waiting ${delay_minutes} minutes before next attempt...${NC}"
            log "${YELLOW}💡 Tip: A1.Flex capacity is scarce - this is normal!${NC}"
            
            sleep "$delay"
        fi
    done
    
    log "${RED}❌ Failed to deploy A1.Flex after $MAX_ATTEMPTS attempts${NC}"
    log "${RED}💡 Suggestions:${NC}"
    log "${RED}   1. Try again tomorrow (capacity refreshes daily)${NC}"
    log "${RED}   2. Consider manual deployment via OCI Console${NC}"
    log "${RED}   3. Contact Oracle support for capacity inquiry${NC}"
    
    exit 1
}

# Handle interruption gracefully
trap 'log "${YELLOW}⚠️  Script interrupted by user${NC}"; exit 130' INT TERM

# Run main function
main "$@"
