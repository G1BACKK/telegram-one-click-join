import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import threading

# --- CONFIGURATION --- (Set these in Render's dashboard)
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'your_bot_token_here')
CHANNEL_HASHES = os.environ.get('CHANNEL_HASHES', 'hash1,hash2,hash3').split(',')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'YourBotUsername')  # Without @

app = Flask(__name__)

# Function to run the bot
def run_bot():
    """Runs the Telegram bot in a separate thread."""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(button_click_handler, pattern='^show_individual$'))
        
        print("🤖 Bot is running on Render...")
        print(f"📋 Channels configured: {len(CHANNEL_HASHES)}")
        application.run_polling()
    except Exception as e:
        print(f"❌ Bot error: {e}")

# Telegram Bot Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    try:
        # Build the magic tg:// link
        channels_param = ",".join(CHANNEL_HASHES)
        magic_link = f"tg://join?invite={channels_param}"
        
        # Create the main keyboard
        keyboard = [
            [InlineKeyboardButton("🚀 JOIN ALL (1-CLICK)", url=magic_link)],
            [InlineKeyboardButton("🔗 Join Individually", callback_data='show_individual')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
        <b>Instant Access</b>
        
        Click the button below to join all our private channels with <b>one click</b>.
        """
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        print(f"Error in start command: {e}")

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows individual join links as a fallback."""
    try:
        query = update.callback_query
        await query.answer()
        
        keyboard = []
        for i, channel_hash in enumerate(CHANNEL_HASHES, 1):
            link = f"https://t.me/+{channel_hash}"
            button = InlineKeyboardButton(f"Channel {i}", url=link)
            keyboard.append([button])
        
        # Add a back button
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data='back_to_main')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="<b>Select a channel to join:</b>", 
            reply_markup=reply_markup, 
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error in button handler: {e}")

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
        <meta name="description" content="Get instant access to exclusive private Telegram channels">
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
            p {{
                margin-bottom: 10px;
                line-height: 1.6;
            }}
            .small {{
                font-size: 14px;
                opacity: 0.8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to the Inner Circle</h1>
            <p>Get instant access to our exclusive private channels with premium content.</p>
            <a class="btn" href="https://t.me/{BOT_USERNAME}?start=render_landing">
                🚀 GET ACCESS NOW
            </a>
            <p class="small">You will be redirected to Telegram to complete the join process.</p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
    return "✅ OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Optional webhook endpoint for future use."""
    return "Webhook received", 200

def start_bot():
    """Starts the bot in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_bot()

# Start the bot when the app loads
if os.environ.get('RENDER', False):  # Check if running on Render
    print("🚀 Starting on Render...")
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
