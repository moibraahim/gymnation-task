"""
Upload GymNation_Facts.pdf to Pinecone
"""
import os
from pinecone import Pinecone
from openai import OpenAI
import PyPDF2
from dotenv import load_dotenv
import hashlib
import httpx

load_dotenv()

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
    return text

def chunk_text(text, chunk_size=500):
    """Split text into smaller chunks"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1
        
        if current_size >= chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_size = 0
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def upload_to_pinecone():
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    
    # Initialize OpenAI
    http_client = httpx.Client()
    openai_client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        http_client=http_client
    )
    
    # Extract text from PDF
    pdf_path = "GymNation_Facts.pdf"
    print(f"Reading {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(text)} characters")
    
    # Chunk the text
    chunks = chunk_text(text, chunk_size=400)
    print(f"Created {len(chunks)} chunks")
    
    # Process each chunk
    vectors = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        # Generate embedding
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",  # This model supports 512 dimensions
                input=chunk,
                dimensions=512  # Match your Pinecone index dimension
            )
            embedding = response.data[0].embedding
            
            # Create vector
            chunk_id = f"gymnation_facts_{i}"
            vector = {
                "id": chunk_id,
                "values": embedding,
                "metadata": {
                    "text": chunk,
                    "source": "GymNation_Facts.pdf",
                    "chunk_index": i,
                    "title": f"GymNation Facts - Part {i+1}"
                }
            }
            vectors.append(vector)
        except Exception as e:
            print(f"Error processing chunk {i}: {e}")
    
    # Upload to Pinecone
    if vectors:
        print(f"Uploading {len(vectors)} vectors to Pinecone...")
        try:
            index.upsert(vectors=vectors)
            print("✅ Successfully uploaded GymNation_Facts.pdf to Pinecone!")
            print(f"Index: {os.getenv('PINECONE_INDEX_NAME')}")
            print(f"Chunks uploaded: {len(vectors)}")
        except Exception as e:
            print(f"Error uploading to Pinecone: {e}")
    else:
        print("No vectors to upload")

if __name__ == "__main__":
    upload_to_pinecone()