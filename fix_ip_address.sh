#!/bin/bash

# fix_ip_address.sh - Automatically update IP settings and SSL certificates for Open WebUI

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== Open WebUI IP Address Fixer ====${NC}"
echo -e "${YELLOW}This script will update all IP-related configurations when your IP address changes${NC}"
echo

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}This script needs to be run as root or with sudo${NC}"
    exit 1
fi

# Get the current IP address (trying various methods to be more robust)
get_ip_address() {
    # Try ifconfig first
    if command -v ifconfig &> /dev/null; then
        IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
    # Fall back to ip command
    elif command -v ip &> /dev/null; then
        IP_ADDRESS=$(ip addr | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | cut -d/ -f1)
    else
        echo -e "${RED}Neither ifconfig nor ip command found. Cannot determine IP address.${NC}"
        exit 1
    fi

    if [ -z "$IP_ADDRESS" ]; then
        echo -e "${RED}No suitable IP address found. Please check your network connection.${NC}"
        exit 1
    fi

    echo "$IP_ADDRESS"
}

IP_ADDRESS=$(get_ip_address)
echo -e "${GREEN}Current IP address: ${IP_ADDRESS}${NC}"

# Create a file to store the last used IP address if it doesn't exist
IP_HISTORY_FILE=".ip_address_history"
if [ ! -f "$IP_HISTORY_FILE" ]; then
    echo "Creating new IP history file..."
    echo "" > "$IP_HISTORY_FILE"
fi

# Get the previous IP address
PREV_IP=$(cat "$IP_HISTORY_FILE")

# Check if IP has changed
if [ "$IP_ADDRESS" = "$PREV_IP" ] && [ ! -z "$PREV_IP" ]; then
    echo -e "${GREEN}IP address hasn't changed (still $IP_ADDRESS). No updates needed.${NC}"
    echo -e "${YELLOW}If you want to force update anyway, use the --force flag.${NC}"
    
    # Check if --force flag is provided
    if [[ "$1" != "--force" ]]; then
        echo
        echo -e "${BLUE}==== Connection Information ====${NC}"
        echo -e "${GREEN}Open WebUI is accessible at:${NC}"
        echo -e "  • ${YELLOW}https://webui.local${NC} (from this computer)"
        echo -e "  • ${YELLOW}https://$IP_ADDRESS${NC} (from other devices on your network)"
        exit 0
    else
        echo -e "${YELLOW}Force flag detected. Proceeding with update anyway...${NC}"
    fi
else
    echo -e "${YELLOW}IP address has changed or is being set for the first time.${NC}"
    # Save the new IP address
    echo "$IP_ADDRESS" > "$IP_HISTORY_FILE"
fi

# 1. Update hosts file and nginx configuration using the existing script
echo -e "${YELLOW}Running update_webui_host.sh to update hosts file and nginx config...${NC}"
./update_webui_host.sh

# 2. Regenerate SSL certificate with the new IP
echo -e "${YELLOW}Regenerating SSL certificate for the new IP address...${NC}"

SSL_DIR="./ssl_cert"
CERT_FILE="${SSL_DIR}/certificate.crt"
KEY_FILE="${SSL_DIR}/private.key"

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

# Generate a new self-signed certificate with the current IP address as SAN
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/CN=webui.local" \
    -addext "subjectAltName=DNS:webui.local,DNS:localhost,IP:127.0.0.1,IP:$IP_ADDRESS"

# Check if certificate generation was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}SSL certificate successfully regenerated with the new IP address${NC}"
    
    # Set proper permissions
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"
    
    # 3. Restart the nginx container to apply the certificate changes
    echo -e "${YELLOW}Restarting nginx container to apply SSL certificate changes...${NC}"
    docker compose restart nginx
else
    echo -e "${RED}Failed to regenerate SSL certificate. Please check the openssl command output.${NC}"
    exit 1
fi

# 4. Display connection information
echo
echo -e "${BLUE}==== Connection Information ====${NC}"
echo -e "${GREEN}Open WebUI is now accessible at:${NC}"
echo -e "  • ${YELLOW}https://webui.local${NC} (from this computer)"
echo -e "  • ${YELLOW}https://$IP_ADDRESS${NC} (from other devices on your network)"
echo
echo -e "${BLUE}Note:${NC} You may need to accept the security warning in your browser due to the self-signed certificate."
echo -e "${GREEN}All IP address-related configurations have been successfully updated!${NC}" 