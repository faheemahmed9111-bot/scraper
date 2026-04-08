import os
import sys
import requests
from db import add_query, get_bot_offset, update_bot_offset

def send_message(token, chat_id, text):
    """Utility to send a message back to Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN environment variable not set. Exiting.")
        sys.exit(1)

    print("Fetching last update ID from Supabase...")
    offset = get_bot_offset()
    
    # Telegram API expects offset = last_update_id + 1 to discard previously processed messages
    poll_offset = offset + 1 if offset > 0 else 0

    print(f"Polling Telegram for messages (offset: {poll_offset})...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": poll_offset, "timeout": 10}
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error calling Telegram API: {e}")
        sys.exit(1)

    if not data.get("ok"):
        print(f"Telegram API returned an error: {data}")
        sys.exit(1)

    messages = data.get("result", [])
    print(f"Found {len(messages)} new message(s).")

    highest_update_id = offset

    for msg in messages:
        update_id = msg.get("update_id")
        message_data = msg.get("message", {})
        chat_id = message_data.get("chat", {}).get("id")
        text = message_data.get("text", "").strip()

        if update_id and update_id > highest_update_id:
            highest_update_id = update_id

        if not text or not chat_id:
            continue

        print(f"[{update_id}] Received text: '{text}' from chat {chat_id}")

        if text.startswith("/scrape "):
            query = text[len("/scrape "):].strip()
            if query:
                print(f"Adding query to queue: '{query}'")
                add_query(query)
                send_message(token, chat_id, f"✅ Query added to queue: '{query}'. It will be processed in the next scraping cycle.")
            else:
                send_message(token, chat_id, "⚠️ Invalid command. Please provide a query (e.g., /scrape plumbers in london)")
        elif text == "/start":
            send_message(token, chat_id, "Hello! Send me a query like:\n`/scrape dentists in new york`\nAnd I will add it to the background lead scraper queue.")
        else:
            send_message(token, chat_id, "To add a query, use the /scrape command. Example:\n/scrape real estate agents in miami")

    if highest_update_id > offset:
        print(f"Updating bot offset to {highest_update_id}...")
        update_bot_offset(highest_update_id)

    print("Bot polling completed successfully.")

if __name__ == "__main__":
    main()
