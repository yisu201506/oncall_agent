import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from query_api import query_database, get_llm_response
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# get the threshold and n_results 
THRESHOLD = 0.6
N_RESULTS = 10


# Get tokens with error checking
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError(
        "Missing Slack tokens. Ensure SLACK_BOT_TOKEN and SLACK_APP_TOKEN "
        "are set in your .env file"
    )

# Initialize Slack app with your bot token
app = App(token=SLACK_BOT_TOKEN)

@app.event("app_mention")
def handle_mention(event, say):
    """Handle when the bot is mentioned in a channel."""
    try:
        # Get the message text and remove the bot mention
        text = event["text"]
        # Get the timestamp of the message for threading
        thread_ts = event["ts"]
        
        # Remove the <@BOT_ID> from the text
        message_text = text.split(">", 1)[1].strip() if ">" in text else text
        
        # Query the database
        results = query_database(message_text, n_results=N_RESULTS, similarity_threshold=THRESHOLD)
        
        # Get LLM response
        llm_response, urls = get_llm_response(message_text, results)
        
        # Format the main response
        response_text = llm_response
        
        # Send the main response in thread
        say(text=response_text, thread_ts=thread_ts)
        
        # If there are URLs, send them as a separate message in the same thread
        if urls:
            url_text = "*Relevant Sources:*\n" + "\n".join([f"• {url}" for url in urls])
            say(text=url_text, thread_ts=thread_ts)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        say(
            text="Sorry, I encountered an error while processing your request.",
            thread_ts=thread_ts
        )

def main():
    try:
        logger.info("Starting Slack bot...")
        logger.debug(f"Using Socket Mode with App Token: {SLACK_APP_TOKEN[:10]}...")
        
        # Start the app using Socket Mode
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        logger.info("Handler created, starting...")
        handler.start()
        
    except Exception as e:
        logger.error(f"Failed to start the bot: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 