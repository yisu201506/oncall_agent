import requests
import json
from typing import List, Optional
from pydantic import BaseModel
import argparse

class MessageResponse(BaseModel):
    message: str
    similarity: float
    slack_url: Optional[str] = None

def query_database(query_text: str, n_results: int = 5, api_url: str = "http://localhost:8000") -> List[MessageResponse]:
    """
    Query the vector database for similar messages.
    
    Args:
        query_text (str): The text to search for
        n_results (int): Number of results to return
        api_url (str): Base URL of the API
        
    Returns:
        List[MessageResponse]: List of messages and their similarity scores and URLs
    """
    try:
        response = requests.post(
            f"{api_url}/query",
            json={"query_text": query_text, "n_results": n_results},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        results = response.json()
        
        # Extract metadata from the response if available
        for result in results:
            if "metadata" in result and result["metadata"]:
                # Add the Slack URL from metadata if it exists
                if "url" in result["metadata"]:
                    result["slack_url"] = result["metadata"]["url"]
        return [MessageResponse(**result) for result in results]
    
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the API server is running (python api_service.py)")
        return []
    except Exception as e:
        print(f"Error querying database: {str(e)}")
        return []

def print_results(results: List[MessageResponse], show_similarity: bool = True):
    """Pretty print the query results"""
    if not results:
        print("No results found.")
        return
        
    print("\nResults:")
    print("-" * 80)
    for i, result in enumerate(results, 1):
        # Clean up the message by removing the markers
        clean_message = (result.message
            .replace("|<message_start>|", "")
            .replace("|<message_end>|", "")
            .replace("|<thread_start>|", "\n  └─ ")
            .replace("|<thread_end>|", "")
            .strip())
            
        print(f"\n{i}. Message:")
        print(f"{clean_message}")
        if result.slack_url:
            print(f"   Slack URL: {result.slack_url}")
        if show_similarity:
            print(f"   Similarity: {result.similarity:.2%}")
    print("-" * 80)

def check_api_status(api_url: str = "http://localhost:8000") -> bool:
    """Check if the API is running"""
    try:
        response = requests.get(api_url)
        return response.status_code == 200
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Query the vector database for similar Slack messages")
    parser.add_argument("--query", "-q", 
                       help="The text to search for",
                       default="Who is awesome?",  # Makes it optional with a default value
                       nargs='?')     # Makes it accept 0 or 1 argument
    parser.add_argument("-n", "--num-results", 
                       type=int, 
                       default=5, 
                       help="Number of results to return (default: 5)")
    parser.add_argument("--no-similarity", 
                       action="store_true", 
                       help="Don't show similarity scores")
    args = parser.parse_args()

    # Check if API is running
    if not check_api_status():
        print("Error: API is not running. Please start it with 'python api_service.py'")
        return

    # If no query provided, prompt the user
    if args.query is None:
        args.query = input("Enter your search query: ")

    # Query the database
    results = query_database(args.query, args.num_results)
    
    # Print results
    print_results(results, show_similarity=not args.no_similarity)

if __name__ == "__main__":
    main() 