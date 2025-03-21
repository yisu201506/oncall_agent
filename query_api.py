import requests
import json
from typing import List, Optional, Tuple
from pydantic import BaseModel
import argparse
from openai import OpenAI

class MessageResponse(BaseModel):
    message: str
    similarity: float
    metadata: Optional[dict] = None

def get_no_information_response() -> str:
    """Return the standard response when no relevant information is found."""
    return ("No relevant information was found in the existing documentation. "
            "Please either:\n"
            "1. File a new ticket to document this information, or\n"
            "2. Start a new Slack thread to discuss this topic.")

def query_database(query_text: str, n_results: int = 10, similarity_threshold: float = 0.6, api_url: str = "http://localhost:8000") -> List[MessageResponse]:
    """Query the vector database for similar messages with similarity threshold."""
    try:
        response = requests.post(
            f"{api_url}/query",
            json={"query_text": query_text, "n_results": n_results},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        results = response.json()
        
        # Filter results by similarity threshold
        filtered_results = [
            MessageResponse(**result) 
            for result in results 
            if result["similarity"] >= similarity_threshold
        ]
        
        return filtered_results
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []

def get_llm_response(query: str, context_messages: List[MessageResponse]) -> Tuple[str, List[str]]:
    """Get LLM response based on query and context."""
    # If no messages above threshold, return standard response
    if not context_messages:
        return get_no_information_response(), []

    client = OpenAI()
    
    # Prepare context from retrieved messages
    context = "\n\n".join([
        f"Document {i+1}:\n{msg.message}" 
        for i, msg in enumerate(context_messages)
    ])
    
    # Collect URLs
    urls = [
        msg.metadata.get("url", "No URL available") 
        for msg in context_messages 
        if msg.metadata
    ]
    
    # Create the system message and user prompt
    system_message = """
    You are a helpful assistant. Please answer the query based on the provided context documents. 
    If the context doesn't contain relevant information, say so, and ask the user to file a new ticket or start a new Slack thread.
    """
    user_prompt = f"Query: {query}\n\nContext:\n{context}"
    
    # Get completion from OpenAI
    response = client.chat.completions.create(
        model="gpt-4",  # or your preferred model
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content, urls

def main():
    parser = argparse.ArgumentParser(description="Query the vector database and get LLM response")
    parser.add_argument("--query", "-q", 
                       help="The text to search for",
                       default=None,
                       nargs='?')
    parser.add_argument("-n", "--num-results", 
                       type=int, 
                       default=10, 
                       help="Number of results to return (default: 10)")
    parser.add_argument("--threshold", 
                       type=float, 
                       default=0.6,
                       help="Similarity threshold (default: 0.6)")
    args = parser.parse_args()

    # If no query provided, prompt the user
    if args.query is None:
        args.query = input("Enter your search query: ")

    # Query the database
    results = query_database(args.query, args.num_results, args.threshold)
    
    # Get LLM response
    llm_response, urls = get_llm_response(args.query, results)
    
    # Print results
    print("\nAI Response:")
    print("-" * 80)
    print(llm_response)
    
    # Only print sources section if there are URLs
    if urls:
        print("\nRelevant Sources:")
        print("-" * 80)
        for url in urls:
            print(f"- {url}")

if __name__ == "__main__":
    main() 