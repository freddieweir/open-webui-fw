# Obsidian RAG Quick Start Guide

This guide will help you quickly get up and running with RAG (Retrieval-Augmented Generation) using your Obsidian vault in Open WebUI.

## Specific Setup for Your Vault

Your Obsidian vault is located at:
```
/Users/fweir/Syncthing-LocalOnly/Local Obsidian/Cortana's Database
```

## Steps to Set Up

1. **Start services with your updated docker-compose file**:
   ```bash
   cd /Users/fweir/git/Forked/open-webui-fw
   docker-compose up -d
   ```

2. **Load your Obsidian vault into marqo**:
   ```bash
   ./load_obsidian_vault.sh "/Users/fweir/Syncthing-LocalOnly/Local Obsidian/Cortana's Database"
   ```
   
   Note: If the path contains spaces, make sure to enclose it in quotes as shown above.

3. **Access Open WebUI** in your web browser.

4. **Configure a Collection**:
   - Navigate to Knowledge → Collections
   - Click "New Collection"
   - Enter a name (e.g., "Cortana's Database")
   - Select "marqo" as the vector database
   - Enter "obsidian-vault" as the collection name
   - Click "Create"

5. **Start a new chat with context**:
   - Create a new chat
   - Click on the context button (folder icon)
   - Select your Obsidian collection
   - Start chatting with your personal knowledge base

## Useful Prompts for Working with Your Notes

- "Summarize my notes about [topic]"
- "What information do I have about [subject]?"
- "Help me organize my thoughts on [topic] based on my existing notes"
- "Find connections between [concept1] and [concept2] in my notes"
- "What are the key points I've documented about [topic]?"
- "Extract actionable items from my notes about [project]"

## Updating Your Knowledge Base

When you add new notes to your Obsidian vault or make significant changes, you can reload the data:

```bash
./load_obsidian_vault.sh "/Users/fweir/Syncthing-LocalOnly/Local Obsidian/Cortana's Database"
```

Choose "y" when asked if you want to recreate the collection.

## Troubleshooting

- **If the collection isn't available**: Make sure both the marqo and open-webui containers are running with `docker ps`
- **If searches return no results**: Check that the collection was created properly and that your Obsidian vault was properly processed
- **If container networking issues occur**: Restart all containers with `docker-compose down` followed by `docker-compose up -d`

## Advanced Configuration

The marqo configuration can be adjusted in `docker-compose.yaml` if needed. For more advanced configurations, refer to the full RAG-OBSIDIAN-README.md documentation. 