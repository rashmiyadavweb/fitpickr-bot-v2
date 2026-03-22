import os
import requests
import re

# ============================================
# CONFIGURATION
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = os.environ.get("CHANNEL", "@fitpickrdeals")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "rashmiyadav02-20")
OWNER_ID = os.environ.get("OWNER_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def add_affiliate(url):
    url = url.split("?")[0]
    return f"{url}?tag={AFFILIATE_TAG}"

def is_amazon_url(text):
    return "amazon.com" in text or "amzn.to" in text

def expand_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except:
        return url

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": False}
    response = requests.post(url, json=payload)
    return response.json()

def post_to_channel(title, affiliate_url):
    message = (
        "🔥 Hot Fitness Deal!\n\n"
        f"💪 {title}\n\n"
        f"🛒 {affiliate_url}\n\n"
        "🏋️ FitPickr Deals - Honest Fitness and Health Picks\n"
        "🌐 fitpickr.lifenbyte.com\n\n"
        "#fitness #deals #amazon #health #workout"
    )
    return send_message(CHANNEL, message)

def process_message(message):
    chat_id = message["chat"]["id"]
    user_id = str(message["chat"]["id"])
    text = message.get("text", "")

    if OWNER_ID and user_id != OWNER_ID:
        send_message(chat_id, "Sorry, this bot is private!")
        return

    if not text:
        return

    if "|" in text and is_amazon_url(text):
        parts = text.split("|", 1)
        title = parts[0].strip()
        url = parts[1].strip()

        if "amzn.to" in url:
            url = expand_url(url)

        match = re.search(r'https://www\.amazon\.com/\S+', url)
        if match:
            url = match.group(0)

        affiliate_url = add_affiliate(url)
        result = post_to_channel(title, affiliate_url)
        if result.get("ok"):
            send_message(chat_id, f"✅ Channel pe post ho gaya!\n\n💪 {title}\n\n🔗 {affiliate_url}")
        else:
            send_message(chat_id, f"❌ Error: {result}")

    elif is_amazon_url(text):
        send_message(chat_id,
            "⚠️ Yeh format use karo:\n\n"
            "Product Title | Amazon Link\n\n"
            "Example:\n"
            "YOTTOY Yoga Mat Non-Slip | https://amazon.com/dp/B0D3XGBPKG"
        )

    elif text == "/start":
        send_message(chat_id,
            "👋 FitPickr Deals Bot mein swagat hai!\n\n"
            "Kaise use karein:\n"
            "1. Amazon pe product dhundho\n"
            "2. Title copy karo\n"
            "3. Mujhe is format mein bhejo:\n\n"
            "Product Title | Amazon Link\n\n"
            "Example:\n"
            "YOTTOY Yoga Mat | https://amazon.com/dp/xxx\n\n"
            "Main automatically @fitpickrdeals channel pe post kar dunga with affiliate link!"
        )
    else:
        send_message(chat_id, "Amazon product link bhejne ke liye yeh format use karo:\n\nProduct Title | Amazon Link")

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    response = requests.get(url, params=params)
    return response.json()

if __name__ == "__main__":
    print("🏋️ FitPickr Deals Bot Starting...")
    print(f"📢 Channel: {CHANNEL}")
    print(f"🏷️ Affiliate: {AFFILIATE_TAG}")
    print("=" * 40)

    offset = None

    while True:
        try:
            updates = get_updates(offset)
            if updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        process_message(update["message"])
        except Exception as e:
            print(f"Error: {e}")
