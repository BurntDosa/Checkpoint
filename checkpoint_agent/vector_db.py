import chromadb
from chromadb.config import Settings
import os

class VectorDB:
    def __init__(self, persistence_path=".chroma_db"):
        self.client = chromadb.PersistentClient(path=persistence_path)
        self.collection = self.client.get_or_create_collection(name="code_checkpoints")

    def add_checkpoint(self, checkpoint_id: str, content: str, metadata: dict):
        """
        Adds a checkpoint to the vector index.
        checkpoint_id: Unique ID (e.g., filename or commit hash)
        content: The text content to embed.
        metadata: Dict containing author, date, etc.
        """
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[checkpoint_id]
        )

    def search(self, query: str, n_results=5):
        """
        Searches the index for relevant checkpoints.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
