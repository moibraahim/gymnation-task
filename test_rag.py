"""
Test RAG retrieval directly
"""
import os
from dotenv import load_dotenv
from services.pinecone_service import get_pinecone_service

load_dotenv()

def test_rag():
    # Initialize Pinecone service
    pinecone = get_pinecone_service()
    
    if not pinecone:
        print("❌ Pinecone service not available")
        return
    
    # Test queries
    queries = [
        "What is GymNation?",
        "How many members does GymNation have?",
        "Where is GymNation located?",
        "Who founded GymNation?",
        "What is the mission of GymNation?"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 50)
        
        # Search knowledge base
        results = pinecone.search_knowledge_base(query, top_k=2)
        
        if results:
            for i, doc in enumerate(results, 1):
                print(f"\n Result {i} (Score: {doc['score']:.3f}):")
                print(f"Text: {doc['text'][:200]}...")
        else:
            print("No results found")
        
        # Get context for prompt
        context = pinecone.get_context_for_prompt(query)
        if context:
            print(f"\n🎯 Context for prompt:\n{context[:300]}...")

if __name__ == "__main__":
    test_rag()