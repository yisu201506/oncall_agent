from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import chromadb
import uvicorn
from openai import OpenAI
import os

app = FastAPI(title="Vector Database API Service")

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection(name="slack_messages")

# Initialize OpenAI client
client = OpenAI()

class QueryRequest(BaseModel):
    query_text: str
    n_results: int = 5

class MessageResponse(BaseModel):
    message: str
    similarity: float

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

        # Query the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.n_results
        )

        # Format results
        messages = []
        for idx, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
            messages.append(MessageResponse(
                message=doc,
                similarity=1 - distance  # Convert distance to similarity score
            ))

        return messages

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api_service:app", host="0.0.0.0", port=8000, reload=True) 