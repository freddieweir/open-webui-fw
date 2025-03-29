# AI Agent Setup Guide: Open WebUI with HTTPS

This guide is designed to help AI assistants set up Open WebUI with HTTPS support on a local network. This configuration is particularly useful for enabling voice and other features that require secure connections.

## Overview

This setup uses:
- A standard Nginx container as a reverse proxy
- Self-signed SSL certificates for HTTPS
- Docker Compose for orchestration
- WebSocket support for real-time features like voice chat

## Prerequisites

- Docker and Docker Compose installed
- Basic understanding of networking concepts
- Root/sudo access on the host machine
- The IP address of the host machine on the local network
- Port 80 and 443 available on the host

## Step 1: Create the Project Structure

```bash
# Create directories for SSL certificates and Nginx configuration
mkdir -p ssl_cert
mkdir -p data/nginx/custom
```

## Step 2: Generate Self-Signed SSL Certificate

Replace `IP_ADDRESS` with the actual IP address of the host machine (e.g., 192.168.1.100).

```bash
# Generate a self-signed certificate for the IP address
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl_cert/private.key -out ssl_cert/certificate.crt \
  -subj "/CN=IP_ADDRESS" -addext "subjectAltName = IP:IP_ADDRESS"
```

## Step 3: Create Nginx Configuration

Create a file at `data/nginx/custom/open-webui.conf` with the following content:

```nginx
server {
    listen 80;
    server_name IP_ADDRESS;
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    http2 on;
    server_name IP_ADDRESS;
    
    ssl_certificate /etc/ssl/custom/certificate.crt;
    ssl_certificate_key /etc/ssl/custom/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://open-webui:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Replace all instances of `IP_ADDRESS` with the actual IP address of the host machine.

## Step 4: Create Docker Compose Configuration

Create or modify `docker-compose.yaml` with the following configuration:

```yaml
services:
  # Uncomment if you want to run Ollama in the same Docker Compose
  # ollama:
  #   volumes:
  #     - ollama:/root/.ollama
  #   container_name: ollama
  #   pull_policy: always
  #   tty: true
  #   restart: unless-stopped
  #   image: ollama/ollama:${OLLAMA_DOCKER_TAG-latest}

  nginx:
    image: 'nginx:alpine'
    restart: unless-stopped
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./data/nginx/custom:/etc/nginx/conf.d
      - ./ssl_cert:/etc/ssl/custom
    depends_on:
      - open-webui
    extra_hosts:
      - host.docker.internal:host-gateway

  open-webui:
    build:
      context: .
      args:
        OLLAMA_BASE_URL: '/ollama'
      dockerfile: Dockerfile
    image: ghcr.io/open-webui/open-webui:${WEBUI_DOCKER_TAG-main}
    container_name: open-webui
    volumes:
      - open-webui:/app/backend/data
    # Expose port internally instead of publishing it
    expose:
      - 8080
    environment:
      # Point to the Ollama instance - adjust as needed
      - 'OLLAMA_BASE_URL=http://host.docker.internal:11434'
      - 'WEBUI_SECRET_KEY='
    extra_hosts:
      - host.docker.internal:host-gateway
    restart: unless-stopped

volumes:
  # Uncomment if using Ollama in the same Docker Compose
  # ollama: {}
  open-webui: {}
```

## Step 5: Start the Services

```bash
docker-compose up -d
```

## Step 6: Set Up Local Hostname (Optional)

To use a hostname like `webui.local` instead of an IP address, add an entry to the hosts file on each client device:

- **macOS/Linux**: Edit `/etc/hosts`
- **Windows**: Edit `C:\Windows\System32\drivers\etc\hosts`

Add the following line:
```
IP_ADDRESS webui.local
```

Replace `IP_ADDRESS` with the actual IP address of the server.

## Step 7: Access Open WebUI

Access the Open WebUI at:
```
https://IP_ADDRESS
```

Or, if you set up the local hostname:
```
https://webui.local
```

The browser will show a security warning because of the self-signed certificate. This is expected. Click "Advanced" and proceed to the site.

## Troubleshooting

### Certificate Errors
If you get certificate errors in the browser:
- Ensure the certificate was generated correctly for the right IP/hostname
- Verify the Nginx configuration points to the correct certificate files
- Try accessing using the same name/IP used in the certificate

### Connection Issues
If you can't connect to the server:
- Check that ports 80 and 443 are open and not used by other services
- Ensure the Docker containers are running with `docker-compose ps`
- Check logs with `docker-compose logs nginx` and `docker-compose logs open-webui`
- Verify the server IP address is correct and accessible from the client

### WebSocket/Voice Issues
If voice features aren't working:
- Ensure the WebSocket configuration in Nginx is correct
- Check browser console for any errors related to WebSockets
- Verify you're accessing via HTTPS (browsers restrict audio/video APIs on non-secure connections)

## Security Notes

This setup uses a self-signed certificate, which is fine for local network use but isn't trusted by browsers by default. For a more secure setup in a production environment, consider:

- Using a proper certificate authority
- Implementing additional security measures like firewall rules
- Setting a strong WEBUI_SECRET_KEY environment variable

## Maintaining and Updating

To update Open WebUI to a newer version:

```bash
docker-compose pull
docker-compose up -d
```

## For Mobile Devices

For iOS or Android devices:
- Use the IP address directly (easiest method)
- For iOS devices, you may need to manually accept the certificate warning
- Android devices may require you to add a security exception in the browser settings

---

This configuration was created by an AI assistant. If you encounter any issues, please provide the error messages for more specific troubleshooting. 