import json
import openai
import chromadb
from chromadb.config import Settings
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

# Initialize OpenAI and ChromaDB
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not found. Please add it to your .bash_profile file.")

# Initialize Slack client
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
slack_client = WebClient(token=SLACK_TOKEN)
CHANNEL_NAME = "general"

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="chroma_db")

def get_embedding(text):
    """Get OpenAI embedding for a given text"""
    client = openai.OpenAI()
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

def fetch_slack_messages():
    """Fetch messages from Slack and save to JSON"""
    try:
        # Get the target channel ID
        channels = slack_client.conversations_list(types="public_channel")
        target_channel = next(channel for channel in channels["channels"] 
                            if channel["name"] == CHANNEL_NAME)
        channel_id = target_channel["id"]

        # Get messages from the channel
        messages = slack_client.conversations_history(channel=channel_id)["messages"]
        
        # Get thread replies for each message
        result = []
        for message in messages:
            message_data = {
                "user": message.get("user"),
                "ts": message.get("ts"),
                "text": message.get("text"),
                "thread_replies": []
            }
            
            if "thread_ts" in message:
                thread_replies = slack_client.conversations_replies(
                    channel=channel_id,
                    ts=message["thread_ts"]
                )["messages"]
                message_data["thread_replies"] = thread_replies[1:]  # Exclude the parent message
                
            result.append(message_data)

        # Save results to JSON file
        with open("slack_messages.json", "w") as f:
            json.dump(result, f, indent=2)
            
        print("Messages and threads saved to slack_messages.json")
        return True

    except SlackApiError as e:
        print(f"Error fetching Slack messages: {e.response['error']}")
        return False

def process_slack_messages():
    """Process messages and store embeddings in ChromaDB"""
    try:
        # Read the existing JSON file
        with open("slack_messages.json", "r") as f:
            messages = json.load(f)
        
        # Create or get ChromaDB collection
        collection = chroma_client.get_or_create_collection(name="slack_messages")
        
        # Get existing message IDs from ChromaDB
        existing_ids = set(collection.get()['ids'])
        
        # Process each message
        formatted_messages = []
        for idx, message in enumerate(messages):
            message_id = message['ts']
            
            # Skip if message already processed
            if message_id in existing_ids:
                print(f"Skipping already processed message {message_id}")
                continue
                
            # Format main message
            formatted_message = f"|<message_start>| {message['text']} |<message_end>|"
            
            # Format thread replies
            if message['thread_replies']:
                for reply in message['thread_replies']:
                    formatted_message += f" |<thread_start>| {reply['text']} |<thread_end>|"
            
            formatted_messages.append(formatted_message)
            
            # Get embedding for new message
            embedding = get_embedding(formatted_message)
            
            # Log processing details
            print(f"Processing new message {message_id}")
            print(f"Message: {formatted_message[:100]}...")
            print(f"Embedding shape: {len(embedding)}")
            print(f"Embedding sample: {embedding[:5]}...")
            
            # Store in ChromaDB
            collection.add(
                documents=[formatted_message],
                embeddings=[embedding],
                ids=[message_id]
            )
        
        # Append new formatted messages to text file
        with open("formatted_slack_messages.txt", "a") as f:
            if formatted_messages:  # Only write if there are new messages
                f.write("\n".join(formatted_messages) + "\n")
                print(f"Added {len(formatted_messages)} new messages to formatted_slack_messages.txt")
            else:
                print("No new messages to add")

        total_messages = len(collection.get()['ids'])
        print(f"Total messages in ChromaDB: {total_messages}")
        return True

    except Exception as e:
        print(f"Error processing messages: {str(e)}")
        return False

def main():
    """Main function to run the entire workflow"""
    print("Starting Slack message processing workflow...")
    
    # Step 1: Fetch messages from Slack
    print("\n1. Fetching messages from Slack...")
    if not fetch_slack_messages():
        print("Failed to fetch Slack messages. Aborting.")
        return
    
    # Step 2: Process messages and create embeddings
    print("\n2. Processing messages and creating embeddings...")
    if not process_slack_messages():
        print("Failed to process messages. Aborting.")
        return
    
    print("\nWorkflow completed successfully!")

if __name__ == "__main__":
    main()
