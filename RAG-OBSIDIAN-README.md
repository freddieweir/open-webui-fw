# Obsidian RAG Integration for Open WebUI

This branch adds [Retrieval-Augmented Generation (RAG)](https://www.pinecone.io/learn/retrieval-augmented-generation/) capabilities to Open WebUI, allowing you to use your [Obsidian](https://obsidian.md/) notes as a knowledge source for AI conversations.

## Features

- Integrates [Marqo](https://www.marqo.ai/) as a vector database for Open WebUI
- Processes and indexes your Obsidian vault
- Handles Obsidian-specific markdown features:
  - Frontmatter
  - Wiki-style links
  - Images
  - Tags
- Enables AI to reference and use your personal notes during conversations
- Preserves metadata and context from your notes

## Requirements

- Docker (for running Marqo)
- Python 3.8+
- An existing Obsidian vault with notes
- Open WebUI installation

## Quick Setup

A setup script is provided to simplify the integration:

```bash
./scripts/setup_obsidian_rag.sh -v /path/to/your/obsidian/vault
```

### Command Line Options

```
-v, --vault-path PATH      Path to your Obsidian vault (required)
-m, --marqo-url URL        URL for Marqo server (default: http://localhost:8882)
-c, --collection-name NAME Collection name (default: obsidian-vault)
-r, --recreate             Recreate collection if it exists
-h, --help                 Show help message
```

## Manual Setup

If you prefer to set up components manually, follow these steps:

1. **Start Marqo Server**:
   ```bash
   docker-compose -f docker-compose.marqo.yaml up -d
   ```

2. **Configure Open WebUI to use Marqo**:
   Add these lines to your `.env` file:
   ```
   VECTOR_DB=marqo
   MARQO_URL=http://localhost:8882
   ```

3. **Process and index your Obsidian vault**:
   ```bash
   python -m scripts.load_obsidian_to_marqo --vault-path /path/to/your/obsidian/vault
   ```

4. **Start Open WebUI**:
   ```bash
   ./start_webui.sh
   ```

5. **Create a collection** in Open WebUI using the Marqo database.

## Auto-Tag and Clean Up Your Obsidian Notes

This integration can also help organize your notes. To auto-tag and clean up Obsidian files:

1. Chat with an AI in Open WebUI, selecting your Obsidian collection
2. Ask the AI to analyze and suggest improvements for your notes
3. Request auto-tagging or documentation cleanup

Example prompts:
- "Review my notes and suggest consistent tagging"
- "Help me organize the structure of my vault"
- "Clean up and format inconsistent notes"

## How It Works

1. The Obsidian vault processor:
   - Scans your Obsidian vault for markdown files
   - Extracts frontmatter, tags, and content
   - Processes Obsidian-specific markdown features
   - Chunks content into manageable pieces

2. Marqo:
   - Creates embeddings (vector representations) of your notes
   - Stores these vectors in a searchable database
   - Provides semantic search capabilities

3. Open WebUI's RAG:
   - When you ask a question, relevant notes are retrieved
   - The AI combines its knowledge with information from your notes
   - Responses are generated with context from your personal knowledge base

## Troubleshooting

- **Marqo server not starting**: Ensure Docker has enough memory allocated (at least 8GB)
- **Notes not appearing in search**: Check that the collection was created correctly
- **Error processing Obsidian vault**: Ensure your vault path is correct and accessible

## Advanced Configuration

For advanced users, you can further customize the setup:

- Modify the chunking parameters for different text splitting strategies
- Use a different embedding model by configuring Marqo
- Adjust the RAG retrieval parameters in Open WebUI

## Contributing

Contributions are welcome! If you'd like to improve this integration:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This integration is covered under the same license as Open WebUI. 