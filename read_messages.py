from abc import ABC, abstractmethod
import json
import openai
import chromadb
from chromadb.config import Settings
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from typing import List, Dict, Any, Optional

# Initialize OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not found")

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="chroma_db")

class DataSource(ABC):
    """Abstract base class for different data sources"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.collection = chroma_client.get_or_create_collection(name=collection_name)

    @abstractmethod
    def fetch_messages(self) -> bool:
        """Fetch messages from the data source"""
        pass

    @abstractmethod
    def get_message_permalink(self, message_id: str) -> Optional[str]:
        """Get permalink for a specific message"""
        pass

    @abstractmethod
    def format_message(self, message: Dict[str, Any]) -> str:
        """Format a message according to the source's specific structure"""
        pass

    @abstractmethod
    def process_messages(self) -> bool:
        """Process messages and store embeddings in ChromaDB"""
        pass

    @abstractmethod
    def save_formatted_messages(self, formatted_messages: List[str], 
                              message_permalinks: List[str]) -> None:
        """Save formatted messages according to the source's specific needs"""
        pass

    def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for a given text"""
        client = openai.OpenAI()
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    @abstractmethod
    def get_source_messages(self) -> List[Dict[str, Any]]:
        """Get messages from the source's storage"""
        pass

    def update_collection(self, message_id: str, formatted_message: str, 
                         embedding: List[float], metadata: Dict[str, Any], 
                         existing_ids: set) -> None:
        """Update or add message to ChromaDB collection"""
        if message_id in existing_ids:
            print(f"Updating message {message_id}")
            self.collection.update(
                documents=[formatted_message],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[message_id]
            )
        else:
            print(f"Adding new message {message_id}")
            self.collection.add(
                documents=[formatted_message],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[message_id]
            )

class SlackDataSource(DataSource):
    """Slack-specific implementation of DataSource"""
    
    def __init__(self, channel_name: str):
        super().__init__("slack")
        self.slack_client = WebClient(token=os.environ.get('SLACK_TOKEN'))
        self.channel_name = channel_name
        self.channel_id = self._get_channel_id()

    def _get_channel_id(self) -> str:
        channels = self.slack_client.conversations_list(types="public_channel")
        target_channel = next(channel for channel in channels["channels"] 
                            if channel["name"] == self.channel_name)
        return target_channel["id"]

    def fetch_messages(self) -> bool:
        try:
            messages = self.slack_client.conversations_history(channel=self.channel_id)["messages"]
            result = []
            
            for message in messages:
                message_data = {
                    "id": message.get("ts"),
                    "user": message.get("user"),
                    "text": message.get("text"),
                    "thread_replies": []
                }
                
                if "thread_ts" in message:
                    thread_replies = self.slack_client.conversations_replies(
                        channel=self.channel_id,
                        ts=message["thread_ts"]
                    )["messages"]
                    message_data["thread_replies"] = thread_replies[1:]
                    
                result.append(message_data)

            with open("slack_messages.json", "w") as f:
                json.dump(result, f, indent=2)
                
            return True

        except SlackApiError as e:
            print(f"Error fetching Slack messages: {e.response['error']}")
            return False

    def get_message_permalink(self, message_id: str) -> Optional[str]:
        try:
            response = self.slack_client.chat_getPermalink(
                channel=self.channel_id,
                message_ts=message_id
            )
            return response["permalink"] if response["ok"] else None
        except SlackApiError as e:
            print(f"Error getting permalink: {e.response['error']}")
            return None

    def format_message(self, message: Dict[str, Any]) -> str:
        formatted = f"|<message_start>| {message['text']} |<message_end>|"
        
        if message['thread_replies']:
            for reply in message['thread_replies']:
                formatted += f" |<thread_start>| {reply['text']} |<thread_end>|"
        
        return formatted

    def get_source_messages(self) -> List[Dict[str, Any]]:
        with open("slack_messages.json", "r") as f:
            return json.load(f)

    def process_messages(self) -> bool:
        """Slack-specific message processing implementation"""
        try:
            existing_ids = set(self.collection.get()['ids'])
            messages = self.get_source_messages()
            formatted_messages = []
            message_permalinks = []

            for message in messages:
                message_id = str(message['id'])
                message_permalink = self.get_message_permalink(message_id)
                formatted_message = self.format_message(message)
                
                if message_id in existing_ids:
                    existing_result = self.collection.get(ids=[message_id])
                    if existing_result['documents'] and existing_result['documents'][0] == formatted_message:
                        print(f"Skipping unchanged message {message_id}")
                        continue
                
                formatted_messages.append(formatted_message)
                message_permalinks.append(message_permalink if message_permalink else "No permalink available")
                
                embedding = self.get_embedding(formatted_message)
                metadata = {"url": message_permalink, "type": "slack"} if message_permalink else {}
                
                self.update_collection(message_id, formatted_message, embedding, metadata, existing_ids)
            
            self.save_formatted_messages(formatted_messages, message_permalinks)
            return True

        except Exception as e:
            print(f"Error processing messages: {str(e)}")
            return False

    def save_formatted_messages(self, formatted_messages: List[str], 
                              message_permalinks: List[str]) -> None:
        """Slack-specific implementation for saving formatted messages"""
        if not formatted_messages:
            print("No new messages to add")
            return

        filename = f"formatted_{self.collection_name}_messages.txt"
        with open(filename, "a") as f:
            for message, permalink in zip(formatted_messages, message_permalinks):
                f.write(f"{message}\nURI: {permalink}\n\n")
        print(f"Added {len(formatted_messages)} new messages to {filename}")

class JiraDataSource(DataSource):
    def __init__(self, project_key: str):
        super().__init__("jira_messages")
        self.project_key = project_key
        # Initialize Jira client

    # ... other required methods ...

    def process_messages(self) -> bool:
        """Jira-specific message processing implementation"""
        try:
            # Implement Jira-specific processing logic
            # This might include handling different types of Jira items
            # (issues, comments, attachments) differently
            pass
        except Exception as e:
            print(f"Error processing Jira messages: {str(e)}")
            return False

    def save_formatted_messages(self, formatted_messages: List[str], 
                              message_permalinks: List[str]) -> None:
        """Jira-specific implementation for saving formatted messages"""
        # Implement Jira-specific saving logic
        # This might include organizing by project, issue type, etc.
        pass

def main():
    """Main function to run the entire workflow"""
    print("Starting message processing workflow...")
    
    # Initialize Slack data source
    slack_source = SlackDataSource(channel_name="general")
    
    # Step 1: Fetch messages
    print("\n1. Fetching messages...")
    if not slack_source.fetch_messages():
        print("Failed to fetch messages. Aborting.")
        return
    
    # Step 2: Process messages and create embeddings
    print("\n2. Processing messages and creating embeddings...")
    if not slack_source.process_messages():
        print("Failed to process messages. Aborting.")
        return
    
    print("\nWorkflow completed successfully!")

if __name__ == "__main__":
    main()
