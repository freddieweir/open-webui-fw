import os
import logging
from typing import Any, Dict, List, Optional, Tuple

import marqo
from langchain.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain.schema.vectorstore import VectorStoreRetriever

from ..config import MARQO_URL, MARQO_API_KEY

log = logging.getLogger(__name__)

class MarqoLoader:
    """Class for loading and interacting with Marqo vector store."""
    
    def __init__(
        self,
        embedding_model: Embeddings,
        marqo_url: str = None,
        marqo_api_key: str = None,
    ):
        """Initialize MarqoLoader.
        
        Args:
            embedding_model: Embedding model to use for embeddings
            marqo_url: URL for Marqo server
            marqo_api_key: API key for Marqo server
        """
        self.embedding_model = embedding_model
        self.marqo_url = marqo_url or MARQO_URL
        self.marqo_api_key = marqo_api_key or MARQO_API_KEY
        self.client = marqo.Client(url=self.marqo_url, api_key=self.marqo_api_key)
        
    def create_collection(self, collection_name: str, recreate: bool = False) -> None:
        """Create a collection in Marqo.
        
        Args:
            collection_name: Name of the collection
            recreate: If True, delete the collection if it exists
            
        Returns:
            None
        """
        try:
            # Check if the collection exists
            try:
                self.client.index(collection_name).get_stats()
                if recreate:
                    log.info(f"Deleting existing collection: {collection_name}")
                    self.client.index(collection_name).delete()
                    log.info(f"Creating collection: {collection_name}")
                    self.client.create_index(collection_name, model=self.embedding_model.model_name if hasattr(self.embedding_model, 'model_name') else "hf/all-MiniLM-L6-v2")
                else:
                    log.info(f"Collection already exists: {collection_name}")
            except Exception:
                log.info(f"Creating collection: {collection_name}")
                self.client.create_index(collection_name, model=self.embedding_model.model_name if hasattr(self.embedding_model, 'model_name') else "hf/all-MiniLM-L6-v2")
        except Exception as e:
            log.error(f"Error creating collection {collection_name}: {e}")
            raise
            
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection from Marqo.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            None
        """
        try:
            self.client.index(collection_name).delete()
            log.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            log.error(f"Error deleting collection {collection_name}: {e}")
            raise
            
    def add_texts(
        self, 
        collection_name: str, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add texts to a Marqo collection.
        
        Args:
            collection_name: Name of the collection
            texts: List of texts to add
            metadatas: List of metadata dicts, one for each text
            ids: List of IDs to use for the texts
            
        Returns:
            List of IDs of the added texts
        """
        try:
            documents = []
            
            for i, text in enumerate(texts):
                document = {
                    "text": text,
                }
                
                # Add metadata if available
                if metadatas and i < len(metadatas):
                    for key, value in metadatas[i].items():
                        document[key] = value
                
                # Add ID if available
                if ids and i < len(ids):
                    document["_id"] = ids[i]
                
                documents.append(document)
            
            # Add documents to Marqo
            response = self.client.index(collection_name).add_documents(
                documents, 
                tensor_fields=["text"],
                client_batch_size=50  # Adjust based on needs
            )
            
            # Extract and return IDs of added documents
            result_ids = []
            for doc in documents:
                if "_id" in doc:
                    result_ids.append(doc["_id"])
                else:
                    # If we didn't specify an ID, Marqo generated one
                    # We'd need to extract it from the response
                    result_ids.append(doc.get("_id", "unknown"))
            
            return result_ids
            
        except Exception as e:
            log.error(f"Error adding texts to collection {collection_name}: {e}")
            raise
            
    def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[Tuple[Document, float]]:
        """Search Marqo collection for similar texts.
        
        Args:
            collection_name: Name of the collection
            query: Query text
            limit: Maximum number of results to return
            filter: Filter to apply to the search
            include_metadata: Whether to include metadata in the results
            
        Returns:
            List of Documents with scores
        """
        try:
            # Search Marqo collection
            search_args = {
                "q": query,
                "limit": limit,
            }
            
            if filter:
                search_args["filter"] = filter
                
            results = self.client.index(collection_name).search(**search_args)
            
            # Convert results to Documents with scores
            documents_with_scores = []
            
            for hit in results["hits"]:
                content = hit.get("text", "")
                metadata = {}
                
                # Extract metadata from the hit
                for key, value in hit.items():
                    if key not in ["text", "_id", "_score", "_highlights"]:
                        metadata[key] = value
                        
                # Include the document ID in metadata
                metadata["_id"] = hit.get("_id", "")
                
                # Create a Document
                doc = Document(page_content=content, metadata=metadata)
                
                # Add the document and its score
                documents_with_scores.append((doc, hit.get("_score", 0.0)))
            
            return documents_with_scores
            
        except Exception as e:
            log.error(f"Error searching collection {collection_name}: {e}")
            raise
    
    def delete_texts(
        self,
        collection_name: str,
        ids: List[str],
    ) -> None:
        """Delete texts from a Marqo collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of IDs to delete
            
        Returns:
            None
        """
        try:
            self.client.index(collection_name).delete_documents(ids=ids)
            log.info(f"Deleted {len(ids)} documents from collection: {collection_name}")
        except Exception as e:
            log.error(f"Error deleting texts from collection {collection_name}: {e}")
            raise

class MarqoVectorStore(VectorStore):
    """Marqo vector store for LangChain integration."""
    
    def __init__(
        self,
        embedding_model: Embeddings,
        collection_name: str,
        marqo_url: str = None,
        marqo_api_key: str = None,
    ):
        """Initialize MarqoVectorStore.
        
        Args:
            embedding_model: Embedding model to use for embeddings
            collection_name: Name of the collection
            marqo_url: URL for Marqo server
            marqo_api_key: API key for Marqo server
        """
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.marqo_loader = MarqoLoader(
            embedding_model=embedding_model,
            marqo_url=marqo_url,
            marqo_api_key=marqo_api_key,
        )
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add texts to the vector store.
        
        Args:
            texts: List of texts to add
            metadatas: List of metadata dicts, one for each text
            ids: List of IDs to use for the texts
            
        Returns:
            List of IDs of the added texts
        """
        return self.marqo_loader.add_texts(
            collection_name=self.collection_name,
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )
    
    def delete(self, ids: Optional[List[str]] = None, **kwargs: Any) -> Optional[bool]:
        """Delete texts from the vector store.
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            True if successful
        """
        if ids:
            self.marqo_loader.delete_texts(
                collection_name=self.collection_name,
                ids=ids,
            )
        return True
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 10,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents with scores.
        
        Args:
            query: Query text
            k: Maximum number of results to return
            filter: Filter to apply to the search
            
        Returns:
            List of Documents with scores
        """
        return self.marqo_loader.search(
            collection_name=self.collection_name,
            query=query,
            limit=k,
            filter=filter,
            include_metadata=True,
        )
    
    def similarity_search(
        self,
        query: str,
        k: int = 10,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Search for similar documents.
        
        Args:
            query: Query text
            k: Maximum number of results to return
            filter: Filter to apply to the search
            
        Returns:
            List of Documents
        """
        docs_and_scores = self.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter,
            **kwargs,
        )
        return [doc for doc, _ in docs_and_scores]
    
    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        collection_name: str = "default_collection",
        marqo_url: str = None,
        marqo_api_key: str = None,
        **kwargs: Any,
    ) -> "MarqoVectorStore":
        """Create MarqoVectorStore from texts.
        
        Args:
            texts: List of texts to add
            embedding: Embedding model to use
            metadatas: List of metadata dicts, one for each text
            collection_name: Name of the collection
            marqo_url: URL for Marqo server
            marqo_api_key: API key for Marqo server
            
        Returns:
            MarqoVectorStore instance
        """
        vector_store = cls(
            embedding_model=embedding,
            collection_name=collection_name,
            marqo_url=marqo_url,
            marqo_api_key=marqo_api_key,
        )
        
        vector_store.marqo_loader.create_collection(collection_name)
        
        vector_store.add_texts(
            texts=texts,
            metadatas=metadatas,
        )
        
        return vector_store
    
    def as_retriever(
        self,
        search_type: str = "similarity",
        search_kwargs: dict = None,
        **kwargs: Any,
    ) -> VectorStoreRetriever:
        """Create a retriever from the vector store.
        
        Args:
            search_type: Type of search to perform
            search_kwargs: Arguments to pass to the search method
            
        Returns:
            VectorStoreRetriever instance
        """
        search_kwargs = search_kwargs or {}
        return VectorStoreRetriever(
            vectorstore=self,
            search_type=search_type,
            search_kwargs=search_kwargs,
            **kwargs,
        ) 