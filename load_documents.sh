#!/bin/bash

# Script to load documents into marqo in the integrated docker-compose setup
# Usage: ./load_documents.sh

set -e  # Exit on any error

# Default to the specified directory
DOCS_PATH="/Users/fweir/Syncthing-LocalOnly/Local Documents"

# Parse any command line options
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -p|--path)
      DOCS_PATH="$2"
      shift
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  -p, --path PATH    Path to documents directory (default: /Users/fweir/Syncthing-LocalOnly/Local Documents)"
      echo "  -h, --help         Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Using documents directory: $DOCS_PATH"

# Ensure documents path exists
if [ ! -d "$DOCS_PATH" ]; then
  echo "Error: Documents path '$DOCS_PATH' does not exist or is not a directory"
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

# Process documents and load to marqo
echo "Processing documents at $DOCS_PATH and loading to marqo..."

# Run the Python script inside a container with mounted volumes
echo "This may take some time depending on the number and size of your documents..."

# Check if the user wants to recreate the collection
read -p "Do you want to recreate the collection if it exists? (y/N): " RECREATE
RECREATE_ARG=""
if [[ "$RECREATE" =~ ^[Yy]$ ]]; then
  RECREATE_ARG="--recreate-collection"
fi

# Check if the required dependencies are installed in the container
read -p "Install document processing dependencies? (Y/n): " INSTALL_DEPS
INSTALL_DEPS_CMD=""
if [[ ! "$INSTALL_DEPS" =~ ^[Nn]$ ]]; then
  echo "Installing required dependencies for document processing..."
  INSTALL_DEPS_CMD="pip install PyPDF2 python-docx langchain_text_splitters && "
fi

# Run the script using docker-compose exec, mounting the documents directory as a volume
docker run --rm \
  --network open-webui-fw_default \
  -v "$DOCS_PATH:/documents" \
  -v "$(pwd)/scripts:/scripts" \
  --entrypoint bash \
  ghcr.io/open-webui/open-webui:latest \
  -c "${INSTALL_DEPS_CMD}python -m scripts.load_documents_to_marqo --docs-path /documents --marqo-url http://marqo:8882 --collection-name local-documents $RECREATE_ARG"

echo "Setup complete!"
echo ""
echo "Your documents have been loaded into marqo and are ready to use with Open WebUI."
echo "To use your documents in conversations:"
echo "1. Go to Open WebUI in your browser"
echo "2. Navigate to Knowledge -> Collections"
echo "3. Create a new collection using 'marqo' as the vector database and 'local-documents' as the collection name"
echo "4. Start a new chat and select your documents collection for context"
echo "" 