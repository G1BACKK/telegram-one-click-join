import os
import logging
from flask import Flask
import requests
from threading import Thread
import time

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Configuration from Environment Variables ---
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'your_bot_token_here')
CHANNEL_HASHES = os.environ.get('CHANNEL_HASHES', 'hash1,hash2,hash3').split(',')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'YourBotUsername')

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

class TelegramBot:
    def __init__(self):
        self.last_update_id = 0
        self.running = True
        
    def send_message(self, chat_id, text, reply_markup=None):
        """Send a message to a Telegram chat."""
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
            
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
            
    def edit_message_text(self, chat_id, message_id, text, reply_markup=None):
        """Edit an existing message."""
        url = f"{TELEGRAM_API_URL}/editMessageText"
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
            
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return None
            
    def answer_callback_query(self, callback_query_id):
        """Answer a callback query."""
        url = f"{TELEGRAM_API_URL}/answerCallbackQuery"
        payload = {
            'callback_query_id': callback_query_id
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Error answering callback: {e}")
            return None
            
    def get_updates(self):
        """Get new updates from Telegram."""
        url = f"{TELEGRAM_API_URL}/getUpdates"
        payload = {
            'offset': self.last_update_id + 1,
            'timeout': 30,
            'allowed_updates': ['message', 'callback_query']
        }
        
        try:
            response = requests.post(url, json=payload, timeout=35)
            data = response.json()
            if data.get('ok'):
                return data['result']
            return []
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
            
    def process_update(self, update):
        """Process a single update."""
        if 'message' in update and 'text' in update['message']:
            self.process_message(update['message'])
        elif 'callback_query' in update:
            self.process_callback_query(update['callback_query'])
            
    def process_message(self, message):
        """Process a text message."""
        if message['text'].startswith('/start'):
            self.handle_start_command(message)
            
    def process_callback_query(self, callback_query):
        """Process a callback query."""
        self.answer_callback_query(callback_query['id'])
        
        if callback_query['data'] == 'show_individual':
            self.handle_show_individual(callback_query)
        elif callback_query['data'] == 'back_to_main':
            self.handle_back_to_main(callback_query)
            
    def handle_start_command(self, message):
        """Handle /start command."""
        chat_id = message['chat']['id']
        
        # Build the magic tg:// link
        channels_param = ",".join(CHANNEL_HASHES)
        magic_link = f"tg://join?invite={channels_param}"
        
        # Create inline keyboard
        keyboard = {
            'inline_keyboard': [
                [{
                    'text': '🚀 JOIN ALL CHANNELS (1-CLICK)',
                    'url': magic_link
                }],
                [{
                    'text': '🔗 Join Individually',
                    'callback_data': 'show_individual'
                }]
            ]
        }
        
        welcome_text = """
<b>🎯 Instant Access</b>

Click the button below to join all our private channels with <b>one click</b>.

If the 1-click method doesn't work, use the individual option below.
        """
        
        self.send_message(chat_id, welcome_text, keyboard)
        
    def handle_show_individual(self, callback_query):
        """Show individual join links."""
        message = callback_query['message']
        chat_id = message['chat']['id']
        message_id = message['message_id']
        
        # Create buttons for each channel
        keyboard_buttons = []
        for i, channel_hash in enumerate(CHANNEL_HASHES, 1):
            link = f"https://t.me/+{channel_hash}"
            keyboard_buttons.append([{
                'text': f'📢 Join Channel {i}',
                'url': link
            }])
            
        # Add back button
        keyboard_buttons.append([{
            'text': '⬅️ Back to Main',
            'callback_data': 'back_to_main'
        }])
        
        keyboard = {'inline_keyboard': keyboard_buttons}
        
        self.edit_message_text(
            chat_id,
            message_id,
            "<b>Select a channel to join:</b>\n\nClick each button to send a join request.",
            keyboard
        )
        
    def handle_back_to_main(self, callback_query):
        """Go back to main menu."""
        message = callback_query['message']
        chat_id = message['chat']['id']
        message_id = message['message_id']
        
        # Build the magic tg:// link
        channels_param = ",".join(CHANNEL_HASHES)
        magic_link = f"tg://join?invite={channels_param}"
        
        keyboard = {
            'inline_keyboard': [
                [{
                    'text': '🚀 JOIN ALL CHANNELS (1-CLICK)',
                    'url': magic_link
                }],
                [{
                    'text': '🔗 Join Individually',
                    'callback_data': 'show_individual'
                }]
            ]
        }
        
        self.edit_message_text(
            chat_id,
            message_id,
            "<b>🎯 Instant Access</b>\n\nClick the button below to join all our private channels with <b>one click</b>.",
            keyboard
        )
        
    def run_polling(self):
        """Run the bot in polling mode."""
        logger.info("🤖 Starting Telegram bot in polling mode...")
        logger.info(f"📋 Monitoring {len(CHANNEL_HASHES)} channels")
        
        while self.running:
            try:
                updates = self.get_updates()
                for update in updates:
                    self.process_update(update)
                    self.last_update_id = max(self.last_update_id, update['update_id'])
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(5)

# Create bot instance
bot = TelegramBot()

def run_bot():
    """Run the bot in a separate thread."""
    bot.run_polling()

# Start bot in background thread
bot_thread = Thread(target=run_bot, daemon=True)
bot_thread.start()

# Flask Routes
@app.route('/')
def landing_page():
    """Serves the landing page."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Join Our Private Channels</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            max-width: 400px;
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }}
        .btn {{
            background: #25D366;
            color: white;
            padding: 16px 32px;
            border-radius: 50px;
            text-decoration: none;
            display: inline-block;
            margin: 20px 0;
            font-weight: bold;
            font-size: 18px;
            transition: transform 0.2s;
        }}
        .btn:hover {{
            transform: scale(1.05);
            background: #20BD5C;
        }}
        h1 {{
            margin-bottom: 20px;
            font-size: 28px;
        }}
        .small {{
            font-size: 14px;
            opacity: 0.8;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Premium Access</h1>
        <p>Get instant access to our exclusive private Telegram channels with premium content.</p>
        <a class="btn" href="https://t.me/{BOT_USERNAME}?start=render_landing">
            GET ACCESS NOW
        </a>
        <p class="small">You'll be redirected to Telegram to complete the join process.</p>
    </div>
</body>
</html>
"""

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return "✅ OK - Service is running"

@app.route('/test')
def test_bot():
    """Test endpoint to check bot status."""
    return f"✅ Bot is running. Monitoring {len(CHANNEL_HASHES)} channels."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
