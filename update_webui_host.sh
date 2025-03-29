#!/bin/bash

# This script updates the hosts file with the correct IP address for webui.local

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Updating webui.local in your hosts file...${NC}"

# Get the IP address from the 192.168.4.x subnet
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | grep "192.168.4." | head -1 | awk '{print $2}')

if [ -z "$IP_ADDRESS" ]; then
  echo -e "${RED}Could not find an IP address in the 192.168.4.x subnet.${NC}"
  echo -e "${YELLOW}Looking for any available local IP address...${NC}"
  
  # Try to get any local IP address (excluding loopback)
  IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
  
  if [ -z "$IP_ADDRESS" ]; then
    echo -e "${RED}No suitable IP address found. Please check your network connection.${NC}"
    exit 1
  fi
fi

echo -e "${GREEN}Found IP address: ${IP_ADDRESS}${NC}"

# Check if webui.local is already in the hosts file
if grep -q "webui.local" /etc/hosts; then
  echo -e "${YELLOW}Updating existing webui.local entry in hosts file...${NC}"
  
  # Need sudo to modify hosts file
  sudo sed -i '' "s/.*webui\.local/$IP_ADDRESS webui.local/" /etc/hosts
else
  echo -e "${YELLOW}Adding new webui.local entry to hosts file...${NC}"
  
  # Need sudo to modify hosts file
  echo "$IP_ADDRESS webui.local" | sudo tee -a /etc/hosts > /dev/null
fi

# Restart nginx container
echo -e "${YELLOW}Restarting nginx container...${NC}"
docker compose restart nginx

echo -e "${GREEN}Done! webui.local has been updated to point to ${IP_ADDRESS}${NC}"
echo -e "${YELLOW}You can now access Open WebUI at https://webui.local${NC}"

# Update the nginx configuration if needed
NGINX_CONF="./data/nginx/custom/open-webui.conf"
if [ -f "$NGINX_CONF" ]; then
  if ! grep -q "$IP_ADDRESS" "$NGINX_CONF"; then
    echo -e "${YELLOW}Updating nginx configuration with new IP address...${NC}"
    sed -i '' "s/server_name localhost webui\.local [0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}/server_name localhost webui.local $IP_ADDRESS/" "$NGINX_CONF"
    echo -e "${YELLOW}Restarting nginx container to apply changes...${NC}"
    docker compose restart nginx
  fi
fi

echo -e "${GREEN}All done! Your Open WebUI should now be accessible.${NC}" 