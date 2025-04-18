#!/bin/bash

# fix_ip_address_siri.sh - Minimal version for Siri Shortcuts
# Updates IP settings and SSL certificates for Open WebUI

# Simple function to get IP address
get_ip_address() {
    if command -v ifconfig &> /dev/null; then
        IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
    elif command -v ip &> /dev/null; then
        IP_ADDRESS=$(ip addr | grep 'inet ' | grep -v '127.0.0.1' | head -1 | awk '{print $2}' | cut -d/ -f1)
    else
        echo "ERROR: Cannot determine IP address"
        exit 1
    fi

    if [ -z "$IP_ADDRESS" ]; then
        echo "ERROR: No IP address found"
        exit 1
    fi

    echo "$IP_ADDRESS"
}

# Get current IP
IP_ADDRESS=$(get_ip_address)

# Check for IP change
IP_HISTORY_FILE=".ip_address_history"
if [ ! -f "$IP_HISTORY_FILE" ]; then
    echo "" > "$IP_HISTORY_FILE"
fi

PREV_IP=$(cat "$IP_HISTORY_FILE")

# Handle IP change check
if [ "$IP_ADDRESS" = "$PREV_IP" ] && [ ! -z "$PREV_IP" ] && [[ "$1" != "--force" ]]; then
    echo "Status: No Change"
    echo "IP: $IP_ADDRESS"
    echo "WebUI: https://atlantis.local/webui or https://$IP_ADDRESS/webui"
    echo "VTuber: https://atlantis.local/vtuber or https://$IP_ADDRESS/vtuber"
    exit 0
else
    # Save new IP
    echo "$IP_ADDRESS" > "$IP_HISTORY_FILE"
    
    # Status message
    if [ "$IP_ADDRESS" != "$PREV_IP" ] || [ -z "$PREV_IP" ]; then
        echo "Status: IP Updated"
        echo "Previous IP: $PREV_IP"
        echo "New IP: $IP_ADDRESS"
    else
        echo "Status: Force Update"
        echo "IP: $IP_ADDRESS"
    fi

    # Update hosts and nginx
    ./update_webui_host.sh > /dev/null 2>&1
    
    # Update SSL cert
    SSL_DIR="./ssl_cert"
    CERT_FILE="${SSL_DIR}/certificate.crt"
    KEY_FILE="${SSL_DIR}/private.key"
    
    mkdir -p "$SSL_DIR"
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/CN=atlantis.local" \
        -addext "subjectAltName=DNS:atlantis.local,DNS:localhost,IP:127.0.0.1,IP:$IP_ADDRESS" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        chmod 644 "$CERT_FILE"
        chmod 600 "$KEY_FILE"
        docker compose restart nginx > /dev/null 2>&1
        echo "SSL: Updated"
    else
        echo "SSL: Failed to update"
    fi
    
    # Final access info
    echo "WebUI: https://atlantis.local/webui or https://$IP_ADDRESS/webui"
    echo "VTuber: https://atlantis.local/vtuber or https://$IP_ADDRESS/vtuber"
fi 