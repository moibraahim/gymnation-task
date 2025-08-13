"""
Pinecone vector database service for RAG (Retrieval-Augmented Generation)
"""
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class PineconeService:
    def __init__(self):
        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")
        
        self.pc = Pinecone(api_key=api_key)
        
        # Get or create index
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "business-knowledge")
        self.dimension = int(os.getenv("PINECONE_DIMENSION", "1536"))  # OpenAI embedding dimension
        
        # Connect to existing index (assuming it's already created with your documents)
        try:
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            print(f"Note: Could not connect to Pinecone index '{self.index_name}'. Error: {e}")
            print("Make sure your Pinecone index exists and contains your business documents.")
            self.index = None
        
        # Initialize OpenAI for embeddings
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            import httpx
            http_client = httpx.Client()
            self.openai_client = OpenAI(api_key=openai_api_key, http_client=http_client)
        else:
            raise ValueError("OPENAI_API_KEY not found for embedding generation")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",  # Match the 512 dimension index
                input=text,
                dimensions=512
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the Pinecone knowledge base for relevant documents
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        if not self.index:
            return []
        
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            documents = []
            for match in results.matches:
                doc = {
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "title": match.metadata.get("title", ""),
                    "source": match.metadata.get("source", ""),
                    "metadata": match.metadata
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Error searching Pinecone: {e}")
            return []
    
    def get_context_for_prompt(self, query: str, max_context_length: int = 2000) -> str:
        """
        Get relevant context from the knowledge base to include in the prompt
        
        Args:
            query: The user's query
            max_context_length: Maximum length of context to return
            
        Returns:
            Formatted context string to include in the prompt
        """
        documents = self.search_knowledge_base(query, top_k=3)
        
        if not documents:
            return ""
        
        context_parts = []
        total_length = 0
        
        for doc in documents:
            text = doc.get("text", "")
            title = doc.get("title", "")
            
            # Format each document
            if title:
                doc_text = f"[{title}]\n{text}"
            else:
                doc_text = text
            
            # Check length
            if total_length + len(doc_text) > max_context_length:
                break
            
            context_parts.append(doc_text)
            total_length += len(doc_text)
        
        if context_parts:
            return "### Relevant Business Information:\n" + "\n\n".join(context_parts)
        
        return ""


# Singleton instance
pinecone_service = None

def get_pinecone_service() -> Optional[PineconeService]:
    """Get or create Pinecone service instance"""
    global pinecone_service
    if pinecone_service is None:
        try:
            pinecone_service = PineconeService()
        except Exception as e:
            print(f"Pinecone service not available: {e}")
            return None
    return pinecone_service