import os
import logging
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, TypeHandler

# --- Configuration from Environment Variables ---
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'your_bot_token_here')
CHANNEL_HASHES = os.environ.get('CHANNEL_HASHES', 'hash1,hash2,hash3').split(',')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'YourBotUsername')

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Telegram Bot Application
def create_application():
    """Create and configure the Telegram bot application."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_click_handler, pattern='^(show_individual|back_to_main)$'))
    
    return application

# Create bot application instance
bot_application = create_application()

# Telegram Bot Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    try:
        logger.info(f"Received /start from user: {update.effective_user.id}")
        
        # Build the magic tg:// link
        channels_param = ",".join(CHANNEL_HASHES)
        magic_link = f"tg://join?invite={channels_param}"
        
        # Create the main keyboard
        keyboard = [
            [InlineKeyboardButton("🚀 JOIN ALL CHANNELS (1-CLICK)", url=magic_link)],
            [InlineKeyboardButton("🔗 Join Individually", callback_data='show_individual')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
<b>🎯 Instant Access</b>

Click the button below to join all our private channels with <b>one click</b>.

If the 1-click method doesn't work, use the individual option below.
        """
        
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup, 
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text("❌ Sorry, something went wrong. Please try again later.")

async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks."""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == 'show_individual':
            # Show individual join links
            keyboard = []
            for i, channel_hash in enumerate(CHANNEL_HASHES, 1):
                link = f"https://t.me/+{channel_hash}"
                button = InlineKeyboardButton(f"📢 Join Channel {i}", url=link)
                keyboard.append([button])
            
            # Add back button
            keyboard.append([InlineKeyboardButton("⬅️ Back to Main", callback_data='back_to_main')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="<b>Select a channel to join:</b>\n\nClick each button to send a join request.",
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )
            
        elif query.data == 'back_to_main':
            # Go back to main menu
            channels_param = ",".join(CHANNEL_HASHES)
            magic_link = f"tg://join?invite={channels_param}"
            
            keyboard = [
                [InlineKeyboardButton("🚀 JOIN ALL CHANNELS (1-CLICK)", url=magic_link)],
                [InlineKeyboardButton("🔗 Join Individually", callback_data='show_individual')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text="<b>🎯 Instant Access</b>\n\nClick the button below to join all our private channels with <b>one click</b>.",
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Error in button_click_handler: {e}")

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
    return jsonify({"status": "healthy", "service": "telegram-one-click-join"})

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Webhook endpoint for Telegram updates."""
    try:
        data = await request.get_json()
        update = Update.de_json(data, bot_application.bot)
        await bot_application.process_update(update)
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error"})

def start_bot_polling():
    """Start the bot in polling mode."""
    try:
        logger.info("🤖 Starting Telegram bot in polling mode...")
        logger.info(f"📋 Monitoring {len(CHANNEL_HASHES)} channels")
        bot_application.run_polling()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

# Start bot when imported
if __name__ == '__main__':
    import threading
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=start_bot_polling, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
else:
    # For Render deployment
    logger.info("🚀 Application initialized on Render")
