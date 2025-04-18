#!/bin/bash

# Get the local IP address
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

if [ -z "$IP_ADDRESS" ]; then
  echo "Error: Could not determine local IP address."
  exit 1
fi

echo "Using IP address: $IP_ADDRESS"

# Update /etc/hosts entries
if grep -q "webui.local" /etc/hosts; then
  sudo sed -i '' "s/.*webui\.local/$IP_ADDRESS webui.local/" /etc/hosts
else
  echo "$IP_ADDRESS webui.local" | sudo tee -a /etc/hosts > /dev/null
fi

if grep -q "vtuber.local" /etc/hosts; then
  sudo sed -i '' "s/.*vtuber\.local/$IP_ADDRESS vtuber.local/" /etc/hosts
else
  echo "$IP_ADDRESS vtuber.local" | sudo tee -a /etc/hosts > /dev/null
fi

echo "Host entries updated. You can now access:"
echo "  • https://webui.local (Open WebUI)"
echo "  • https://vtuber.local (Open-LLM-VTuber)"
