# Oncall Agent

A Python-based oncall agent for managing and automating oncall responsibilities.

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - On Unix/macOS: `source venv/bin/activate`
   - On Windows: `.\venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export SLACK_TOKEN="your-slack-token"
   ```

## Running the Vector Database and Text Processing

1. Initialize and run the vector database (ChromaDB):
   - The vector database (ChromaDB) will be automatically initialized when you run the text processing script
   - The database will be stored in the `chroma_db` directory in your project root
   - No separate startup is needed as ChromaDB runs embedded in the application

2. Run the text processing script:
   ```bash
   python text_processing.py
   ```
   This will:
   - Fetch messages from your Slack channel (default: #general)
   - Save raw messages to `slack_messages.json`
   - Process messages and create embeddings
   - Store embeddings in ChromaDB
   - Save formatted messages to `formatted_slack_messages.txt`

3. Query the results:
   - The vector database stores messages with their embeddings in the `slack_messages` collection
   - To search through the messages, use:
   ```bash
   python query_api.py "your search query here"
   ```
   
   Options:
   - `-n NUMBER`: Specify the number of results to return (default: 5)
   - `--no-similarity`: Don't show similarity scores in the output
   
   Examples:
   ```bash
   # Get 10 results
   python query_api.py "deployment issues" -n 10
   
   # Get results without similarity scores
   python query_api.py "oncall runbook" --no-similarity
   
   # Combine options
   python query_api.py "incident response" -n 3 --no-similarity
   ```

## Usage

[Add usage instructions here]

## Contributing

[Add contribution guidelines here]

## License

[Add license information here] 