# Local Documents RAG Quick Start Guide

This guide will help you quickly set up and use RAG (Retrieval-Augmented Generation) with your local documents in Open WebUI.

## Setup for Your Documents Directory

Your documents directory is located at:
```
/Users/fweir/Syncthing-LocalOnly/Local Documents
```

## Supported Document Types

The following document types are supported:
- PDF (.pdf)
- Word documents (.docx, .doc)
- Text files (.txt)
- Markdown files (.md)
- HTML files (.html, .htm)
- CSV files (.csv)
- JSON files (.json)
- Rich Text Format (.rtf)

## Steps to Set Up

1. **Start services with the docker-compose file**:
   ```bash
   cd /Users/fweir/git/Forked/open-webui-fw
   docker-compose up -d
   ```

2. **Load your documents into marqo**:
   ```bash
   ./load_documents.sh
   ```
   
   This will process all supported files in your documents directory and add them to the marqo vector database.

3. **Access Open WebUI** in your web browser.

4. **Configure a Collection**:
   - Navigate to Knowledge → Collections
   - Click "New Collection"
   - Enter a name (e.g., "Local Documents")
   - Select "marqo" as the vector database
   - Enter "local-documents" as the collection name
   - Click "Create"

5. **Start a new chat with context**:
   - Create a new chat
   - Click on the context button (folder icon)
   - Select your documents collection
   - Start chatting with your documents as context

## Using Different Document Paths

If you want to use a different documents directory, specify it with the `-p` or `--path` option:

```bash
./load_documents.sh -p "/path/to/your/documents"
```

## Document Processing

When processing documents, the system will:
1. Extract text from various file formats
2. Split content into manageable chunks
3. Convert these chunks into vector embeddings
4. Store them in the marqo database for semantic search

## Useful Prompts for Working with Your Documents

- "Summarize the document about [topic]"
- "What information do I have about [subject]?"
- "Find and explain the key points from my documents about [topic]"
- "Compare information between different documents about [concept]"
- "Extract the main arguments from the document about [subject]"
- "What are the steps mentioned in the document about [process]?"

## Updating Your Document Collection

When you add new documents or make changes to existing ones, simply run the script again:

```bash
./load_documents.sh
```

Choose "y" when asked if you want to recreate the collection to refresh all documents.

## Troubleshooting

- **Missing document text**: Some document formats (especially complex PDFs) may not extract properly. Consider converting them to simpler formats.
- **Document processing errors**: Make sure the required dependencies are installed when prompted.
- **Large documents**: Very large documents may take time to process. Be patient during loading.
- **Search results not relevant**: Try rephrasing your query or specify more details to get better context.

## Advanced Configuration

For advanced users, you can customize document processing parameters in `scripts/load_documents_to_marqo.py`, such as:
- Chunk size and overlap
- File extensions to process
- Excluded directories 