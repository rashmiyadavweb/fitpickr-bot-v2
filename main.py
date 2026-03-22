import os
import requests
import re
from bs4 import BeautifulSoup

# ============================================
# CONFIGURATION
# ============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = os.environ.get("CHANNEL", "@fitpickrdeals")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "rashmiyadav02-20")
OWNER_ID = os.environ.get("OWNER_ID")  # Your Telegram user ID

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ============================================
# ADD AFFILIATE TAG
# ============================================
def add_affiliate(url):
    # Clean URL first
    url = url.split("?")[0]
    return f"{url}?tag={AFFILIATE_TAG}"

# ============================================
# FETCH AMAZON PRODUCT TITLE
# ============================================
def get_product_info(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get title
        title = soup.find("span", {"id": "productTitle"})
        if title:
            return title.text.strip()
        
        # Try alternate
        title = soup.find("h1", {"id": "title"})
        if title:
            return title.text.strip()
            
        return None
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None

# ============================================
# SEND MESSAGE TO TELEGRAM
# ============================================
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": False
    }
    response = requests.post(url, json=payload)
    return response.json()

# ============================================
# POST DEAL TO CHANNEL
# ============================================
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

# ============================================
# CHECK IF URL IS AMAZON
# ============================================
def is_amazon_url(text):
    return "amazon.com" in text or "amzn.to" in text

# ============================================
# GET UPDATES FROM TELEGRAM
# ============================================
def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    response = requests.get(url, params=params)
    return response.json()

# ============================================
# EXPAND SHORT URL (amzn.to)
# ============================================
def expand_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except:
        return url

# ============================================
# PROCESS MESSAGE
# ============================================
def process_message(message):
    chat_id = message["chat"]["id"]
    user_id = str(message["chat"]["id"])
    text = message.get("text", "")

    # Check if owner
    if OWNER_ID and user_id != OWNER_ID:
        send_message(chat_id, "Sorry, this bot is private!")
        return

    if not text:
        return

    # Check if Amazon URL
    if is_amazon_url(text):
        send_message(chat_id, "⏳ Amazon link mila! Product info fetch kar raha hoon...")
        
        # Expand short URL if needed
        url = text.strip()
        if "amzn.to" in url:
            url = expand_url(url)
        
        # Clean URL - get just the product URL
        match = re.search(r'https://www\.amazon\.com/[^\s]+', url)
        if match:
            url = match.group(0)
        
        # Add affiliate tag
        affiliate_url = add_affiliate(url)
        
        # Get product title
        title = get_product_info(url)
        
        if title:
            # Post to channel
            result = post_to_channel(title, affiliate_url)
            if result.get("ok"):
                send_message(chat_id, f"✅ Channel pe post ho gaya!\n\n💪 {title[:100]}\n\n🔗 {affiliate_url}")
            else:
                send_message(chat_id, f"❌ Post karne mein error: {result}")
        else:
            # Post with URL only if title not found
            result = post_to_channel("Amazon Fitness Deal", affiliate_url)
            if result.get("ok"):
                send_message(chat_id, f"✅ Post ho gaya! (Title fetch nahi hua)\n\n🔗 {affiliate_url}")
            else:
                send_message(chat_id, "❌ Error posting to channel!")
    
    elif text == "/start":
        send_message(chat_id, 
            "👋 FitPickr Deals Bot mein aapka swagat hai!\n\n"
            "Kaise use karein:\n"
            "1. Amazon product ka link copy karo\n"
            "2. Mujhe bhejo\n"
            "3. Main automatically @fitpickrdeals channel pe post kar dunga with your affiliate link!\n\n"
            "Amazon links supported:\n"
            "✅ amazon.com links\n"
            "✅ amzn.to short links"
        )
    else:
        send_message(chat_id, "Amazon product link bhejo — main channel pe post kar dunga! 🛒")

# ============================================
# MAIN LOOP
# ============================================
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
