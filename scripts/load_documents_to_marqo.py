#!/usr/bin/env python3
"""
Script to process documents and load them into Marqo for RAG in Open WebUI.
This script scans a directory, processes various document types, and adds them to Marqo.
"""

import os
import re
import argparse
import logging
from typing import Dict, List, Optional, Tuple
import marqo
from pathlib import Path
import hashlib
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("documents-to-marqo")

# Try to import document processing libraries, with fallbacks
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter_available = True
except ImportError:
    logger.warning("langchain_text_splitters not available, falling back to basic chunking")
    text_splitter_available = False

try:
    import PyPDF2
    pdf_reader_available = True
except ImportError:
    logger.warning("PyPDF2 not available, PDF processing will be limited")
    pdf_reader_available = False

try:
    import docx
    docx_reader_available = True
except ImportError:
    logger.warning("python-docx not available, DOCX processing will be limited")
    docx_reader_available = False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process documents and load them into Marqo for RAG."
    )
    parser.add_argument(
        "--docs-path",
        type=str,
        required=True,
        help="Path to the documents directory",
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
        default="local-documents",
        help="Name of the Marqo collection to use",
    )
    parser.add_argument(
        "--exclude-dirs",
        type=str,
        nargs="+",
        default=[".git", "__pycache__", "node_modules"],
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
        "--file-extensions",
        type=str,
        nargs="+",
        default=[".txt", ".md", ".pdf", ".docx", ".doc", ".rtf", ".html", ".htm", ".csv", ".json"],
        help="File extensions to process",
    )
    parser.add_argument(
        "--recreate-collection",
        action="store_true",
        help="Recreate the Marqo collection if it exists",
    )
    return parser.parse_args()

def calculate_file_hash(file_path: Path) -> str:
    """Calculate a hash for a file to use as unique ID."""
    BLOCKSIZE = 65536
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as file:
        buf = file.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()

def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    if not pdf_reader_available:
        logger.warning(f"PDF processing not available. Skipping {file_path}")
        return ""
    
    try:
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: Path) -> str:
    """Extract text from a DOCX file."""
    if not docx_reader_available:
        logger.warning(f"DOCX processing not available. Skipping {file_path}")
        return ""
    
    try:
        text = ""
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {e}")
        return ""

def extract_text_from_file(file_path: Path) -> str:
    """Extract text from a file based on its extension."""
    extension = file_path.suffix.lower()
    
    try:
        if extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return extract_text_from_docx(file_path)
        elif extension in ['.txt', '.md', '.html', '.htm', '.csv', '.json', '.rtf']:
            # Try to read as text file with various encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            logger.warning(f"Could not decode {file_path} with any encoding")
            return ""
        else:
            logger.warning(f"Unsupported file type: {extension}")
            return ""
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split text into overlapping chunks."""
    if text_splitter_available:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        return splitter.split_text(text)
    
    # Fallback to basic chunking if LangChain splitter is not available
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
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
    docs_path: str, 
    chunk_size: int, 
    chunk_overlap: int
) -> List[Dict]:
    """Process a single document file."""
    try:
        # Get relative path from root directory
        rel_path = str(file_path.relative_to(Path(docs_path)))
        file_id = calculate_file_hash(file_path)
        
        # Extract text based on file type
        text = extract_text_from_file(file_path)
        
        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return []
        
        # Chunk the content
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        
        # Create documents for each chunk
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "_id": f"{file_id}_chunk_{i}",
                "text": chunk,
                "file_path": rel_path,
                "file_name": file_path.name,
                "file_type": file_path.suffix.lower(),
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            
            documents.append(doc)
        
        return documents
    
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return []

def process_directory(
    docs_path: str, 
    exclude_dirs: List[str], 
    file_extensions: List[str],
    chunk_size: int, 
    chunk_overlap: int
) -> List[Dict]:
    """Process a directory of documents."""
    docs_path = Path(docs_path).expanduser().resolve()
    
    if not docs_path.exists() or not docs_path.is_dir():
        raise ValueError(f"Documents path '{docs_path}' does not exist or is not a directory")
    
    logger.info(f"Processing documents at {docs_path}")
    
    all_documents = []
    
    # Walk through the directory
    for root, dirs, files in os.walk(docs_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        root_path = Path(root)
        
        # Process files with specified extensions
        for file in files:
            file_path = root_path / file
            if any(file.lower().endswith(ext) for ext in file_extensions):
                logger.info(f"Processing file: {file_path}")
                
                documents = process_file(file_path, docs_path, chunk_size, chunk_overlap)
                all_documents.extend(documents)
    
    logger.info(f"Processed {len(all_documents)} chunks from {docs_path}")
    return all_documents

def main():
    """Main entry point."""
    args = parse_args()
    
    # Process the documents directory
    documents = process_directory(
        args.docs_path, 
        args.exclude_dirs, 
        args.file_extensions,
        args.chunk_size, 
        args.chunk_overlap
    )
    
    if not documents:
        logger.warning("No documents processed")
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