import chromadb
import uvicorn
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
from read_messages import COLLECTION_NAME

app = FastAPI(title="Vector Database API Service")

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# Initialize OpenAI client
client = OpenAI()

class QueryRequest(BaseModel):
    query_text: str
    n_results: int = 5

class MessageResponse(BaseModel):
    message: str
    similarity: float
    metadata: Optional[dict] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "running", "message": "Vector Database Service is running"}

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    try:
        total_messages = len(collection.get()['ids'])
        return {
            "total_messages": total_messages,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=List[MessageResponse])
async def query_messages(request: QueryRequest):
    """Query similar messages from the vector database"""
    try:
        # Get embedding for query text
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=request.query_text
        )
        query_embedding = response.data[0].embedding

        # Query the collection with include=['metadatas']
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.n_results,
            include=['metadatas', 'distances', 'documents']  # Be explicit about what we want
        )

        # Add debug logging
        print("ChromaDB Query Results:", results)

        # Format results with safety checks
        messages = []
        documents = results.get('documents', [[]])[0]
        distances = results.get('distances', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]

        # Ensure we have matching lengths
        n = min(len(documents), len(distances), len(metadatas))
        
        for i in range(n):
            messages.append(MessageResponse(
                message=documents[i],
                similarity=1 - distances[i],  # Convert distance to similarity score
                metadata=metadatas[i] if metadatas[i] is not None else {}  # Handle None metadata
            ))

        return messages

    except Exception as e:
        # Add more detailed error logging
        print(f"Error in query_messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api_service:app", host="0.0.0.0", port=8000, reload=True) 