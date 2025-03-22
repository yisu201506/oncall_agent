# Documentation Query System with Slack Integration

This system consists of two main components:
1. A Vector Database API Server
2. A Slack Bot that queries the database and responds to user questions

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Slack workspace where you can create apps
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-directory>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables by creating a `.env` file:
```bash
# API Server settings
OPENAI_API_KEY=your_openai_api_key

# Slack Bot settings
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

## Setting up the Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app and select your workspace

4. Enable Socket Mode:
   - In the left sidebar, click on "Socket Mode"
   - Toggle "Enable Socket Mode" to ON
   - Click "Generate Token"
   - Give it a name (e.g., "socket-token")
   - This generates your `SLACK_APP_TOKEN` (starts with `xapp-`)
   - Save this token immediately - you'll need it for your `.env` file

5. Under "OAuth & Permissions":
   - Add these Bot Token Scopes:
     - `chat:write`
     - `app_mentions:read`
   - Install the app to your workspace
   - Save the Bot User OAuth Token (starts with `xoxb-`) - this is your `SLACK_BOT_TOKEN`

6. Under "Event Subscriptions":
   - Enable Events
   - Subscribe to `app_mention` under Bot Events

7. Create a `.env` file with both tokens:
```env
# API Server settings
OPENAI_API_KEY=your_openai_api_key

# Slack Bot settings
SLACK_BOT_TOKEN=xoxb-your-bot-token    # From OAuth & Permissions
SLACK_APP_TOKEN=xapp-your-app-token    # From Socket Mode
```

**Important Note**: If you ever accidentally expose these tokens, immediately rotate them in your Slack App settings.

## Running the System

1. Start the API Server:
```bash
python query_api.py
```
The server will start on http://localhost:8000

2. In a new terminal, start the Slack Bot:
```bash
python slack_bot.py
```

## Using the System

1. Invite the bot to your channel:
```bash
/invite @Y
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