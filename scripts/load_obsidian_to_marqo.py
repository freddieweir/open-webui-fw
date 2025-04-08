#!/usr/bin/env python3
"""
Script to process Obsidian notes and load them into Marqo for RAG in Open WebUI.
This script scans an Obsidian vault, processes markdown files, and adds them to Marqo.
"""

import os
import re
import json
import argparse
import logging
from typing import Dict, List, Optional, Set, Tuple
import marqo
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("obsidian-to-marqo")

# Regular expressions for processing Obsidian markdown
WIKILINK_PATTERN = r'\[\[(.*?)(?:\|(.*?))?\]\]'  # Match [[link]] or [[link|title]]
TAG_PATTERN = r'#([a-zA-Z0-9_\-/]+)'  # Match #tag
FRONTMATTER_PATTERN = r'^---\n(.*?)\n---'  # Match YAML frontmatter
IMAGE_PATTERN = r'!\[\[(.*?)\]\]'  # Match ![[image.png]]
CODE_BLOCK_PATTERN = r'```(?:\w+)?\n(.*?)```'  # Match code blocks

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process Obsidian notes and load them into Marqo for RAG."
    )
    parser.add_argument(
        "--vault-path",
        type=str,
        required=True,
        help="Path to the Obsidian vault",
    )
    parser.add_argument(
        "--marqo-url",
        type=str,
        default="http://localhost:8882",
        help="URL for the Marqo server",
    )
    parser.add_argument(
        "--marqo-api-key",
        type=str,
        default=None,
        help="API key for the Marqo server (if required)",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="obsidian-vault",
        help="Name of the Marqo collection to use",
    )
    parser.add_argument(
        "--exclude-dirs",
        type=str,
        nargs="+",
        default=[".obsidian", ".trash", ".git"],
        help="Directories to exclude from processing",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Size of text chunks for processing",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Overlap between consecutive chunks",
    )
    parser.add_argument(
        "--recreate-collection",
        action="store_true",
        help="Recreate the Marqo collection if it exists",
    )
    return parser.parse_args()

def extract_frontmatter(content: str) -> Tuple[Dict, str]:
    """Extract YAML frontmatter from an Obsidian note."""
    frontmatter = {}
    
    # Search for frontmatter
    matches = re.search(FRONTMATTER_PATTERN, content, re.DOTALL)
    if matches:
        yaml_text = matches.group(1)
        # Basic YAML parsing (for simplicity)
        for line in yaml_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()
                
        # Remove frontmatter from content
        content = re.sub(FRONTMATTER_PATTERN, '', content, flags=re.DOTALL).strip()
    
    return frontmatter, content

def extract_tags(content: str) -> Tuple[List[str], str]:
    """Extract tags from an Obsidian note."""
    tags = []
    
    # Extract tags
    for match in re.finditer(TAG_PATTERN, content):
        tags.append(match.group(1))
    
    # Remove tags from content for cleaner text
    # content = re.sub(TAG_PATTERN, '', content)
    
    return tags, content

def process_wikilinks(content: str, vault_path: str) -> str:
    """Process Obsidian wikilinks [[link]] or [[link|title]] and replace with titles or links."""
    def replace_wikilink(match):
        link = match.group(1)
        title = match.group(2) if match.group(2) else link
        
        # If link refers to a file that exists, we might want to expand it later
        # For now, just replace with the display text
        return title
    
    return re.sub(WIKILINK_PATTERN, replace_wikilink, content)

def process_images(content: str) -> str:
    """Process Obsidian images ![[image.png]] and replace with text indicators."""
    def replace_image(match):
        image_name = match.group(1)
        return f"[Image: {image_name}]"
    
    return re.sub(IMAGE_PATTERN, replace_image, content)

def process_code_blocks(content: str) -> str:
    """Process code blocks and ensure they're properly formatted."""
    return content  # For now, leave code blocks as they are

def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If we're not at the end of the text, try to find a good break point
        if end < len(text):
            # Try to find a paragraph break
            paragraph_break = text.rfind('\n\n', start, end)
            if paragraph_break != -1 and paragraph_break > start + chunk_size // 2:
                end = paragraph_break
            else:
                # Try to find a sentence break
                sentence_break = text.rfind('. ', start, end)
                if sentence_break != -1 and sentence_break > start + chunk_size // 2:
                    end = sentence_break + 1  # Include the period
                else:
                    # Just break at a space if possible
                    space_break = text.rfind(' ', start, end)
                    if space_break != -1 and space_break > start + chunk_size // 2:
                        end = space_break
        
        chunks.append(text[start:end].strip())
        start = end - chunk_overlap if end < len(text) else len(text)
    
    return chunks

def process_file(
    file_path: Path, 
    vault_path: str, 
    chunk_size: int, 
    chunk_overlap: int
) -> List[Dict]:
    """Process a single Obsidian markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get relative path from vault root
        rel_path = str(file_path.relative_to(vault_path))
        file_id = rel_path.replace('/', '_').replace('\\', '_')
        
        # Extract and process components
        frontmatter, content = extract_frontmatter(content)
        tags, content = extract_tags(content)
        content = process_wikilinks(content, vault_path)
        content = process_images(content)
        content = process_code_blocks(content)
        
        # Chunk the content
        chunks = chunk_text(content, chunk_size, chunk_overlap)
        
        # Create documents for each chunk
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "_id": f"{file_id}_chunk_{i}",
                "text": chunk,
                "file_path": rel_path,
                "file_name": file_path.name,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            
            # Add frontmatter as metadata
            for key, value in frontmatter.items():
                doc[f"frontmatter_{key}"] = value
            
            # Add tags
            if tags:
                doc["tags"] = tags
            
            documents.append(doc)
        
        return documents
    
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return []

def process_vault(
    vault_path: str, 
    exclude_dirs: List[str], 
    chunk_size: int, 
    chunk_overlap: int
) -> List[Dict]:
    """Process an entire Obsidian vault."""
    vault_path = Path(vault_path).expanduser().resolve()
    
    if not vault_path.exists() or not vault_path.is_dir():
        raise ValueError(f"Vault path '{vault_path}' does not exist or is not a directory")
    
    logger.info(f"Processing vault at {vault_path}")
    
    all_documents = []
    
    # Walk through the vault
    for root, dirs, files in os.walk(vault_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Process markdown files
        for file in files:
            if file.endswith('.md'):
                file_path = Path(root) / file
                logger.debug(f"Processing file: {file_path}")
                
                documents = process_file(file_path, vault_path, chunk_size, chunk_overlap)
                all_documents.extend(documents)
    
    logger.info(f"Processed {len(all_documents)} chunks from vault")
    return all_documents

def main():
    """Main entry point."""
    args = parse_args()
    
    # Process the vault
    documents = process_vault(
        args.vault_path, 
        args.exclude_dirs, 
        args.chunk_size, 
        args.chunk_overlap
    )
    
    if not documents:
        logger.warning("No documents processed from vault")
        return
    
    # Connect to Marqo
    logger.info(f"Connecting to Marqo at {args.marqo_url}")
    client = marqo.Client(url=args.marqo_url, api_key=args.marqo_api_key)
    
    # Check if collection exists
    try:
        client.index(args.collection_name).get_stats()
        collection_exists = True
    except Exception:
        collection_exists = False
    
    # Create or recreate collection
    if not collection_exists or args.recreate_collection:
        if collection_exists:
            logger.info(f"Recreating collection {args.collection_name}")
            client.index(args.collection_name).delete()
        
        logger.info(f"Creating collection {args.collection_name}")
        client.create_index(args.collection_name)
    
    # Add documents to collection
    logger.info(f"Adding {len(documents)} documents to collection {args.collection_name}")
    
    # Process in batches to avoid overwhelming the server
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        client.index(args.collection_name).add_documents(
            batch, 
            tensor_fields=["text"],
            client_batch_size=batch_size
        )
        logger.info(f"Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
    
    logger.info(f"Successfully added {len(documents)} documents to collection {args.collection_name}")
    
    # Print a test query to verify
    logger.info("Testing search functionality...")
    results = client.index(args.collection_name).search(
        q="test query",
        limit=1
    )
    logger.info(f"Search test complete. Found {len(results.get('hits', []))} results.")

if __name__ == "__main__":
    main() 