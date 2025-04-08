import marqo
from typing import Optional, List, Dict, Any
import logging
import uuid

from open_webui.retrieval.vector.main import VectorItem, SearchResult, GetResult
from open_webui.config import MARQO_URL, MARQO_API_KEY
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])

class MarqoClient:
    def __init__(self):
        """Initialize Marqo client with the configured URL and API key."""
        self.client = marqo.Client(url=MARQO_URL, api_key=MARQO_API_KEY)
        
    def has_collection(self, collection_name: str) -> bool:
        """Check if a collection exists in Marqo.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if the collection exists, False otherwise
        """
        try:
            self.client.index(collection_name).get_stats()
            return True
        except Exception:
            return False
            
    def create_collection(self, collection_name: str, dimension: int = 1536) -> None:
        """Create a collection in Marqo.
        
        Args:
            collection_name: Name of the collection
            dimension: Dimension of the vectors to be stored
            
        Returns:
            None
        """
        try:
            # Marqo handles vector dimensions internally based on the model
            self.client.create_index(collection_name)
            log.info(f"Created collection: {collection_name}")
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
            
    def insert(self, collection_name: str, items: List[Dict[str, Any]]) -> None:
        """Insert items into a Marqo collection.
        
        Args:
            collection_name: Name of the collection
            items: List of items to insert
            
        Returns:
            None
        """
        try:
            # Convert items to Marqo document format
            documents = []
            
            for item in items:
                document = {
                    "text": item["text"]
                }
                
                # Add metadata if available
                if "metadata" in item and item["metadata"]:
                    for key, value in item["metadata"].items():
                        document[key] = value
                
                # Add ID if available, otherwise Marqo will generate one
                if "id" in item and item["id"]:
                    document["_id"] = item["id"]
                    
                documents.append(document)
            
            # Add documents to Marqo
            # Note: Marqo handles vector creation internally, so we don't need to pass vectors
            response = self.client.index(collection_name).add_documents(
                documents, 
                tensor_fields=["text"],
                client_batch_size=50  # Adjust based on needs
            )
            
            log.info(f"Inserted {len(documents)} items into collection: {collection_name}")
        except Exception as e:
            log.error(f"Error inserting items into collection {collection_name}: {e}")
            raise
            
    def delete(self, collection_name: str, ids: List[str]) -> None:
        """Delete items from a Marqo collection.
        
        Args:
            collection_name: Name of the collection
            ids: List of IDs to delete
            
        Returns:
            None
        """
        try:
            self.client.index(collection_name).delete_documents(ids=ids)
            log.info(f"Deleted {len(ids)} items from collection: {collection_name}")
        except Exception as e:
            log.error(f"Error deleting items from collection {collection_name}: {e}")
            raise
            
    def search(
        self, 
        collection_name: str, 
        vectors: List[List[float]], 
        limit: Optional[int] = None
    ) -> Optional[SearchResult]:
        """Search a Marqo collection for similar items.
        
        Args:
            collection_name: Name of the collection
            vectors: List of vector queries
            limit: Maximum number of results to return
            
        Returns:
            SearchResult or None
        """
        try:
            if not vectors or len(vectors) == 0:
                return None
                
            # Initialize result containers
            ids = []
            distances = []
            documents = []
            metadatas = []
            
            # Process each query vector
            for query_vector in vectors:
                # For Marqo, we need to use a text query or convert the vector to a weighted query
                # Since we have vectors, we'll need to use a workaround
                # We'll use a dummy document with the vector and search for similar documents
                
                # Create a temp query collection for this search
                temp_collection_name = f"temp_query_{str(uuid.uuid4())[:8]}"
                
                try:
                    # Create a temp collection with the query vector
                    self.client.create_index(temp_collection_name)
                    
                    # Add the query vector as a document
                    query_doc = {"text": "query_document"}
                    
                    self.client.index(temp_collection_name).add_documents(
                        [query_doc],
                        tensor_fields=["text"]
                    )
                    
                    # Get the embedding ID from the temp collection
                    results = self.client.index(temp_collection_name).search(
                        q="query_document",
                        limit=1
                    )
                    
                    query_id = results["hits"][0]["_id"]
                    
                    # Now, search the actual collection using the query document
                    limit_val = limit if limit is not None else 10
                    
                    results = self.client.index(collection_name).search(
                        q={"$document": {"index_name": temp_collection_name, "document_id": query_id}},
                        limit=limit_val
                    )
                    
                    # Process results
                    query_ids = []
                    query_distances = []
                    query_documents = []
                    query_metadatas = []
                    
                    for hit in results.get("hits", []):
                        query_ids.append(hit.get("_id", ""))
                        query_distances.append(1.0 - hit.get("_score", 0.0))  # Convert similarity to distance
                        query_documents.append(hit.get("text", ""))
                        
                        # Extract metadata
                        metadata = {}
                        for key, value in hit.items():
                            if key not in ["text", "_id", "_score", "_highlights"]:
                                metadata[key] = value
                                
                        query_metadatas.append(metadata)
                    
                    # Add to main results
                    ids.append(query_ids)
                    distances.append(query_distances)
                    documents.append(query_documents)
                    metadatas.append(query_metadatas)
                    
                finally:
                    # Clean up the temp collection
                    try:
                        self.client.index(temp_collection_name).delete()
                    except Exception as delete_error:
                        log.warning(f"Error deleting temp collection {temp_collection_name}: {delete_error}")
            
            return SearchResult(
                ids=ids,
                distances=distances,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            log.error(f"Error searching collection {collection_name}: {e}")
            return None
            
    def query(
        self, 
        collection_name: str, 
        filter: Dict[str, Any], 
        limit: Optional[int] = None
    ) -> Optional[GetResult]:
        """Query a Marqo collection using filters.
        
        Args:
            collection_name: Name of the collection
            filter: Filter to apply to the query
            limit: Maximum number of results to return
            
        Returns:
            GetResult or None
        """
        try:
            if not self.has_collection(collection_name):
                return None
                
            # Build the filter query for Marqo
            # Example: {"title": "example"} becomes {'title': {'$eq': 'example'}}
            marqo_filter = {}
            for key, value in filter.items():
                marqo_filter[key] = {"$eq": value}
                
            # Execute the query
            limit_val = limit if limit is not None else 10
            
            results = self.client.index(collection_name).search(
                q="",  # Empty query to match all documents
                filter=marqo_filter,
                limit=limit_val,
                search_method=marqo.SearchMethods.LEXICAL  # Use lexical search for filter-only queries
            )
            
            # Process results
            query_ids = []
            query_documents = []
            query_metadatas = []
            
            for hit in results.get("hits", []):
                query_ids.append(hit.get("_id", ""))
                query_documents.append(hit.get("text", ""))
                
                # Extract metadata
                metadata = {}
                for key, value in hit.items():
                    if key not in ["text", "_id", "_score", "_highlights"]:
                        metadata[key] = value
                        
                query_metadatas.append(metadata)
                
            # Return empty result if no hits found
            if len(query_ids) == 0:
                return None
                
            return GetResult(
                ids=[query_ids],
                documents=[query_documents],
                metadatas=[query_metadatas]
            )
        except Exception as e:
            log.error(f"Error querying collection {collection_name}: {e}")
            return None
            
    def get(
        self, 
        collection_name: str, 
        limit: Optional[int] = None
    ) -> Optional[GetResult]:
        """Get all items from a Marqo collection.
        
        Args:
            collection_name: Name of the collection
            limit: Maximum number of results to return
            
        Returns:
            GetResult or None
        """
        try:
            if not self.has_collection(collection_name):
                return None
                
            # Execute the query to get all documents
            limit_val = limit if limit is not None else 10
            
            results = self.client.index(collection_name).search(
                q="",  # Empty query to match all documents
                limit=limit_val,
                search_method=marqo.SearchMethods.LEXICAL  # Use lexical search for get-all queries
            )
            
            # Process results
            query_ids = []
            query_documents = []
            query_metadatas = []
            
            for hit in results.get("hits", []):
                query_ids.append(hit.get("_id", ""))
                query_documents.append(hit.get("text", ""))
                
                # Extract metadata
                metadata = {}
                for key, value in hit.items():
                    if key not in ["text", "_id", "_score", "_highlights"]:
                        metadata[key] = value
                        
                query_metadatas.append(metadata)
                
            # Return empty result if no hits found
            if len(query_ids) == 0:
                return None
                
            return GetResult(
                ids=[query_ids],
                documents=[query_documents],
                metadatas=[query_metadatas]
            )
        except Exception as e:
            log.error(f"Error getting documents from collection {collection_name}: {e}")
            return None 