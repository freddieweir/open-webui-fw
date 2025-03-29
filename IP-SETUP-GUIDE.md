# Open WebUI IP Address Configuration Guide

This guide explains how to manage IP address configuration for Open WebUI, especially when your local IP address changes frequently.

## Understanding the Issue

Open WebUI uses a local domain (`webui.local`) to access the interface securely over HTTPS. This domain needs to be mapped to your local IP address in your system's hosts file. When your IP address changes (e.g., when changing networks or locations), this mapping needs to be updated.

## Automated Scripts

We've created several scripts to help manage this process:

### 1. `update_webui_host.sh`

This script automatically detects your current IP address and updates the necessary configurations:

- Updates your system's hosts file to map `webui.local` to your current IP
- Updates the nginx configuration with your current IP
- Restarts the nginx container to apply the changes

Run this script whenever your IP address changes:

```bash
sudo ./update_webui_host.sh
```

### 2. `start_webui.sh`

This script provides a complete startup process:

- Updates your IP address configuration using `update_webui_host.sh`
- Stops any running containers
- Starts all containers fresh

Use this script to start Open WebUI with the correct configuration:

```bash
sudo ./start_webui.sh
```

### 3. `get_webui_ip.sh`

This script displays your current IP address for accessing Open WebUI from other devices on your network.

Run this script to get the IP address:

```bash
./get_webui_ip.sh
```

## Accessing Open WebUI

### From the Same Computer

After running the setup scripts, you can access Open WebUI at:

```
https://webui.local
```

### From Other Devices

To access Open WebUI from other devices on your network:

1. Run `./get_webui_ip.sh` to get your current IP address
2. On the other device, access Open WebUI using:

```
https://[IP_ADDRESS]
```

Replace `[IP_ADDRESS]` with the IP address displayed by the script.

## Troubleshooting

If you encounter connection issues:

1. Verify your IP address hasn't changed
2. Run `./update_webui_host.sh` to update the configuration
3. Check if the containers are running with `docker compose ps`
4. Check nginx logs with `docker logs open-webui-fw-nginx-1`
5. Check Open WebUI logs with `docker logs open-webui`

## Security Notes

- The SSL certificate used is self-signed, so browsers will show a security warning
- Accept the security risk in your browser to proceed to the interface
- This setup is intended for local development/usage and not for production environments 