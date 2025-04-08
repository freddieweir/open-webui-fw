#!/bin/bash

# Script to load Obsidian vault into marqo in the integrated docker-compose setup
# Usage: ./load_obsidian_vault.sh "/path/to/obsidian/vault"

set -e  # Exit on any error

# Get the Obsidian vault path from command line argument
if [ -z "$1" ]; then
  echo "Error: Please provide the path to your Obsidian vault"
  echo "Usage: $0 \"/path/to/obsidian/vault\""
  exit 1
fi

VAULT_PATH="$1"
echo "Using Obsidian vault at: $VAULT_PATH"

# Ensure vault path exists
if [ ! -d "$VAULT_PATH" ]; then
  echo "Error: Vault path '$VAULT_PATH' does not exist or is not a directory"
  exit 1
fi

# Check if docker-compose is running
if ! docker ps | grep -q "open-webui"; then
  echo "Starting docker-compose services..."
  docker-compose up -d
  
  # Wait for marqo to start
  echo "Waiting for marqo to initialize (this may take a minute)..."
  sleep 20
fi

# Ensure marqo is running
if ! docker ps | grep -q "marqo"; then
  echo "Error: marqo container is not running. Please start the services with docker-compose up -d"
  exit 1
fi

echo "marqo service is running"

# Process Obsidian vault and load to marqo
echo "Processing Obsidian vault at $VAULT_PATH and loading to marqo..."

# Run the Python script inside the open-webui container
echo "This may take some time depending on the size of your vault..."

# First, prepare the script with correct arguments
SCRIPT_ARGS="--vault-path /obsidian --marqo-url http://marqo:8882 --collection-name obsidian-vault"

# Check if the user wants to recreate the collection
read -p "Do you want to recreate the collection if it exists? (y/N): " RECREATE
if [[ "$RECREATE" =~ ^[Yy]$ ]]; then
  SCRIPT_ARGS="$SCRIPT_ARGS --recreate-collection"
fi

# Run the script using docker-compose exec, mounting the Obsidian vault as a volume
docker run --rm \
  --network open-webui-fw_default \
  -v "$VAULT_PATH:/obsidian" \
  -v "$(pwd)/scripts:/scripts" \
  --entrypoint python \
  ghcr.io/open-webui/open-webui:latest \
  -m scripts.load_obsidian_to_marqo $SCRIPT_ARGS

echo "Setup complete!"
echo ""
echo "Your Obsidian vault has been loaded into marqo and is ready to use with Open WebUI."
echo "To use your Obsidian notes in conversations:"
echo "1. Go to Open WebUI in your browser"
echo "2. Navigate to Knowledge -> Collections"
echo "3. Create a new collection using 'marqo' as the vector database and 'obsidian-vault' as the collection name"
echo "4. Start a new chat and select your Obsidian collection for context"
echo "" 