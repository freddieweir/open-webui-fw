#!/bin/bash

# Setup Obsidian RAG with Open WebUI and Marqo
# This script runs marqo, loads Obsidian notes, and configures Open WebUI to use marqo

set -e  # Exit on any error

# Default values
VAULT_PATH=""
MARQO_URL="http://localhost:8882"
COLLECTION_NAME="obsidian-vault"
RECREATE=false
HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -v|--vault-path)
      VAULT_PATH="$2"
      shift
      shift
      ;;
    -m|--marqo-url)
      MARQO_URL="$2"
      shift
      shift
      ;;
    -c|--collection-name)
      COLLECTION_NAME="$2"
      shift
      shift
      ;;
    -r|--recreate)
      RECREATE=true
      shift
      ;;
    -h|--help)
      HELP=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Show help if requested
if [ "$HELP" = true ] || [ -z "$VAULT_PATH" ]; then
  echo "Setup Obsidian RAG with Open WebUI and Marqo"
  echo ""
  echo "Usage: $0 -v VAULT_PATH [options]"
  echo ""
  echo "Required arguments:"
  echo "  -v, --vault-path PATH      Path to your Obsidian vault"
  echo ""
  echo "Optional arguments:"
  echo "  -m, --marqo-url URL        URL for Marqo server (default: http://localhost:8882)"
  echo "  -c, --collection-name NAME Collection name (default: obsidian-vault)"
  echo "  -r, --recreate             Recreate collection if it exists"
  echo "  -h, --help                 Show this help message"
  exit 0
fi

# Ensure vault path exists
if [ ! -d "$VAULT_PATH" ]; then
  echo "Error: Vault path $VAULT_PATH does not exist or is not a directory"
  exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
  echo "Error: Docker is not installed. Please install Docker first."
  exit 1
fi

# Start Marqo container if not already running
if ! docker ps | grep -q "marqo"; then
  echo "Starting Marqo container..."
  cd "$ROOT_DIR"
  docker-compose -f docker-compose.marqo.yaml up -d
  
  # Wait for Marqo to start
  echo "Waiting for Marqo to start..."
  sleep 10
  
  # Check if Marqo is running
  if ! curl -s "$MARQO_URL" &> /dev/null; then
    echo "Waiting more time for Marqo to initialize..."
    sleep 20
  fi
fi

# Check if Marqo is accessible
if ! curl -s "$MARQO_URL" &> /dev/null; then
  echo "Error: Cannot connect to Marqo at $MARQO_URL"
  echo "Please make sure Marqo is running and accessible."
  exit 1
fi

echo "Marqo is running at $MARQO_URL"

# Process Obsidian vault and load to Marqo
echo "Processing Obsidian vault at $VAULT_PATH and loading to Marqo..."
cd "$ROOT_DIR"

# Build the arguments for the Python script
ARGS="--vault-path \"$VAULT_PATH\" --marqo-url \"$MARQO_URL\" --collection-name \"$COLLECTION_NAME\""
if [ "$RECREATE" = true ]; then
  ARGS="$ARGS --recreate-collection"
fi

# Run the Python script
python -m scripts.load_obsidian_to_marqo $ARGS

# Configure Open WebUI to use Marqo as vector database
echo "Configuring Open WebUI to use Marqo as vector database..."

# Create or update .env file
ENV_FILE="$ROOT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  # Check if VECTOR_DB is already set
  if grep -q "^VECTOR_DB=" "$ENV_FILE"; then
    # Update the existing value
    sed -i.bak "s/^VECTOR_DB=.*/VECTOR_DB=marqo/" "$ENV_FILE"
  else
    # Add the value
    echo "VECTOR_DB=marqo" >> "$ENV_FILE"
  fi
  
  # Check if MARQO_URL is already set
  if grep -q "^MARQO_URL=" "$ENV_FILE"; then
    # Update the existing value
    sed -i.bak "s|^MARQO_URL=.*|MARQO_URL=$MARQO_URL|" "$ENV_FILE"
  else
    # Add the value
    echo "MARQO_URL=$MARQO_URL" >> "$ENV_FILE"
  fi
else
  # Create a new .env file
  cp "$ROOT_DIR/.env.example" "$ENV_FILE" 2>/dev/null || touch "$ENV_FILE"
  echo "VECTOR_DB=marqo" >> "$ENV_FILE"
  echo "MARQO_URL=$MARQO_URL" >> "$ENV_FILE"
fi

echo "Setup complete!"
echo ""
echo "To use your Obsidian vault with Open WebUI:"
echo "1. Start Open WebUI: ./start_webui.sh"
echo "2. Go to Web UI and navigate to Knowledge -> Collections"
echo "3. Create a new collection using the marqo database with collection name: $COLLECTION_NAME"
echo "4. Chat with your Obsidian notes by selecting the collection and starting a new chat"
echo ""
echo "Your Obsidian vault is now available for RAG in Open WebUI!" 