from flask import Flask, request, redirect
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import threading

# --- CONFIGURATION --- (Set these in Railway's dashboard)
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Will be set via environment variable
CHANNEL_HASHES = ["2TMb-Fb1VUIzYzVl", "xrUNBGG5n_k0ZWY1", "HASH_3"]  # Without the '+' sign

app = Flask(__name__)

# Function to run the bot
def run_bot():
    """Runs the Telegram bot in a separate thread."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_click_handler, pattern='^show_individual$'))
    
    print("Bot is running...")
    application.run_polling()

# Telegram Bot Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
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

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows individual join links as a fallback."""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for i, channel_hash in enumerate(CHANNEL_HASHES, 1):
        link = f"https://t.me/+{channel_hash}"
        button = InlineKeyboardButton(f"Channel {i}", url=link)
        keyboard.append([button])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="<b>Select a channel to join:</b>", reply_markup=reply_markup, parse_mode='HTML')

# Flask Routes
@app.route('/')
def landing_page():
    """Serves the landing page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Join Our Private Channels</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 400px; margin: 0 auto; }
            .btn { background: #25D366; color: white; padding: 15px 25px; border-radius: 50px; text-decoration: none; display: inline-block; margin: 10px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to the Inner Circle</h1>
            <p>Get instant access to our exclusive private channels.</p>
            <a class="btn" href="https://t.me/YourBotUsername?start=source_landing">GET ACCESS NOW</a>
            <p><small>You will be redirected to Telegram to complete the join process.</small></p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    """Health check endpoint for Railway."""
    return "OK", 200

def start_bot():
    """Starts the bot in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    run_bot()

if __name__ == '__main__':
    # Start the bot in a background thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=8000, debug=False)
