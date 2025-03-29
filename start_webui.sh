#!/bin/bash

# This script updates the IP address in the hosts file and starts the Open WebUI services

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Open WebUI...${NC}"

# First, update the hosts file
echo -e "${YELLOW}Updating hosts file with current IP address...${NC}"
./update_webui_host.sh

# Then start the Docker containers
echo -e "${YELLOW}Starting Docker containers...${NC}"
docker compose down
docker compose up -d

echo -e "${GREEN}Open WebUI is now running!${NC}"
echo -e "${YELLOW}You can access it at https://webui.local${NC}" 