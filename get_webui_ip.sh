#!/bin/bash

# This script displays the IP address for accessing Open WebUI from other devices

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Detecting IP address for Open WebUI...${NC}"

# Get the IP address from the 192.168.4.x subnet (preferred)
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | grep "192.168.4." | head -1 | awk '{print $2}')

if [ -z "$IP_ADDRESS" ]; then
  echo -e "${YELLOW}No IP address in the 192.168.4.x subnet found.${NC}"
  echo -e "${YELLOW}Looking for any suitable local network IP address...${NC}"
  
  # Try to find a suitable local IP address (excluding loopback)
  # Look for common home/office network ranges in this order: 192.168.x.x, 10.x.x.x, 172.16-31.x.x
  IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | grep -E "192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\." | head -1 | awk '{print $2}')
  
  if [ -z "$IP_ADDRESS" ]; then
    # Fall back to any non-loopback IP
    IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
    
    if [ -z "$IP_ADDRESS" ]; then
      echo -e "${RED}No suitable IP address found. Please check your network connection.${NC}"
      exit 1
    fi
  fi
fi

# Check if nginx is running
if docker ps | grep -q open-webui-fw-nginx; then
  CONTAINER_RUNNING=true
else
  CONTAINER_RUNNING=false
fi

echo -e "\n${GREEN}${BOLD}===== OPEN WEBUI ACCESS INFORMATION =====${NC}\n"

echo -e "${BOLD}Local computer access URL:${NC}"
echo -e "  ${BLUE}https://webui.local${NC}"

echo -e "\n${BOLD}Other devices on your network can access Open WebUI at:${NC}"
echo -e "  ${BLUE}https://${IP_ADDRESS}${NC}"

if [ "$CONTAINER_RUNNING" = false ]; then
  echo -e "\n${YELLOW}NOTE: The Open WebUI container is not currently running.${NC}"
  echo -e "${YELLOW}Run './start_webui.sh' to start the service.${NC}"
fi

echo -e "\n${GREEN}${BOLD}=======================================${NC}" 