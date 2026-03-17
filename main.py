import os
import threading
import telebot
from flask import Flask
from openai import OpenAI

# Get environment variables (You will set these in Render.com)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

# Initialize Flask App (Required by Render.com to keep the service alive)
app = Flask(__name__)

# Initialize Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize OpenAI Client pointing to Hugging Face Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# Handle '/start' and '/help' commands
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am a DeepSeek AI bot. Send me a message and I'll reply!")

# Handle all other text messages
@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # Show "typing..." status in Telegram while AI is thinking
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call Hugging Face API
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
        )
        
        # Get the response text
        reply_text = chat_completion.choices[0].message.content
        
        # Send reply back to Telegram
        bot.reply_to(message, reply_text)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I encountered an error while processing your request.")

# Render.com needs to see a successful web response on the port
@app.route('/')
def health_check():
    return "Bot is running successfully!", 200

# Function to run the bot polling
def run_bot():
    print("Starting Telegram Bot...")
    bot.infinity_polling()

if __name__ == "__main__":
    # 1. Start the Telegram bot in a background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # 2. Start the Flask web server on the main thread
    # Render assigns a dynamic port via the PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
