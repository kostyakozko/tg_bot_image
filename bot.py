import re
import sqlite3
import os
import json
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Use data directory outside git repo
DB_DIR = os.path.expanduser("~/telegram_bot_data")
os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "config.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            owner_id INTEGER,
            red_image TEXT,
            green_image TEXT,
            channel_username TEXT,
            channel_title TEXT,
            text_on TEXT,
            text_off TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            active_channel_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

def get_channel_config(channel_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.execute("SELECT owner_id, red_image, green_image, channel_username, channel_title, text_on, text_off FROM channels WHERE channel_id = ?", (channel_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        # Parse JSON arrays for images, fallback to single image for backward compatibility
        red_images = json.loads(row[1]) if row[1] and row[1].startswith('[') else ([row[1]] if row[1] else [])
        green_images = json.loads(row[2]) if row[2] and row[2].startswith('[') else ([row[2]] if row[2] else [])
        return {
            "owner_id": row[0], 
            "red_images": red_images, 
            "green_images": green_images, 
            "channel_username": row[3], 
            "channel_title": row[4],
            "text_on": row[5] or "світло з'явилося",
            "text_off": row[6] or "світло зникло"
        }
    return {"owner_id": None, "red_images": [], "green_images": [], "channel_username": None, "channel_title": None, "text_on": "світло з'явилося", "text_off": "світло зникло"}

def set_channel_owner(channel_id, owner_id, username=None, title=None):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR IGNORE INTO channels (channel_id, owner_id, channel_username, channel_title) VALUES (?, ?, ?, ?)", 
                 (channel_id, owner_id, username, title))
    conn.commit()
    conn.close()

def update_channel_info(channel_id, username=None, title=None):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE channels SET channel_username = ?, channel_title = ? WHERE channel_id = ?", 
                 (username, title, channel_id))
    conn.commit()
    conn.close()

def set_user_active_channel(user_id, channel_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR REPLACE INTO user_sessions (user_id, active_channel_id) VALUES (?, ?)", 
                 (user_id, channel_id))
    conn.commit()
    conn.close()

def get_user_active_channel(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.execute("SELECT active_channel_id FROM user_sessions WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def update_channel_image(channel_id, color, file_id):
    """Replace all images with a single one (for /set_red and /set_green)"""
    conn = sqlite3.connect(DB_FILE)
    images_json = json.dumps([file_id])
    if color == "red":
        conn.execute("UPDATE channels SET red_image = ? WHERE channel_id = ?", (images_json, channel_id))
    else:
        conn.execute("UPDATE channels SET green_image = ? WHERE channel_id = ?", (images_json, channel_id))
    conn.commit()
    conn.close()

def add_channel_image(channel_id, color, file_id):
    """Add an image to existing collection"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.execute("SELECT red_image, green_image FROM channels WHERE channel_id = ?", (channel_id,))
    row = cur.fetchone()
    
    if row:
        if color == "red":
            current = json.loads(row[0]) if row[0] and row[0].startswith('[') else ([row[0]] if row[0] else [])
            current.append(file_id)
            conn.execute("UPDATE channels SET red_image = ? WHERE channel_id = ?", (json.dumps(current), channel_id))
        else:
            current = json.loads(row[1]) if row[1] and row[1].startswith('[') else ([row[1]] if row[1] else [])
            current.append(file_id)
            conn.execute("UPDATE channels SET green_image = ? WHERE channel_id = ?", (json.dumps(current), channel_id))
    
    conn.commit()
    conn.close()

def remove_channel_image(channel_id, color, index):
    """Remove an image by index"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.execute("SELECT red_image, green_image FROM channels WHERE channel_id = ?", (channel_id,))
    row = cur.fetchone()
    
    if row:
        if color == "red":
            current = json.loads(row[0]) if row[0] and row[0].startswith('[') else ([row[0]] if row[0] else [])
            if 0 <= index < len(current):
                current.pop(index)
                conn.execute("UPDATE channels SET red_image = ? WHERE channel_id = ?", (json.dumps(current), channel_id))
        else:
            current = json.loads(row[1]) if row[1] and row[1].startswith('[') else ([row[1]] if row[1] else [])
            if 0 <= index < len(current):
                current.pop(index)
                conn.execute("UPDATE channels SET green_image = ? WHERE channel_id = ?", (json.dumps(current), channel_id))
    
    conn.commit()
    conn.close()

def transfer_ownership(channel_id, new_owner_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE channels SET owner_id = ? WHERE channel_id = ?", (new_owner_id, channel_id))
    conn.commit()
    conn.close()

def remove_channel(channel_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

def is_owner(channel_id, user_id):
    config = get_channel_config(channel_id)
    return config["owner_id"] is None or config["owner_id"] == user_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команди:\n"
        "/set_channel <channel_id> - встановити канал для налаштування\n"
        "/set_red - замінити всі зображення для 🔴\n"
        "/set_green - замінити всі зображення для 🟢\n"
        "/add_red - додати зображення до 🔴\n"
        "/add_green - додати зображення до 🟢\n"
        "/list_red - список зображень 🔴\n"
        "/list_green - список зображень 🟢\n"
        "/remove_red <номер> - видалити зображення 🔴\n"
        "/remove_green <номер> - видалити зображення 🟢\n"
        "/set_text_on <текст> - встановити текст для 🟢\n"
        "/set_text_off <текст> - встановити текст для 🔴\n"
        "/reset_text - скинути текст до стандартного\n"
        "/status - перевірити налаштування\n"
        "/transfer <user_id> - передати права власності\n"
        "/remove_channel - видалити налаштування каналу\n\n"
        "Щоб дізнатися ID каналу, перешліть будь-яке повідомлення з каналу сюди."
    )

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Використання: /set_channel <channel_id>")
        return
    
    try:
        channel_id = int(context.args[0])
        user_id = update.message.from_user.id
        
        if not is_owner(channel_id, user_id):
            await update.message.reply_text("❌ Цей канал вже налаштований іншим користувачем")
            return
        
        config = get_channel_config(channel_id)
        if config["owner_id"] is None:
            set_channel_owner(channel_id, user_id)
        
        # Save to database instead of context
        set_user_active_channel(user_id, channel_id)
        
        # Build channel display name
        channel_display = f"{channel_id}"
        if config['channel_username']:
            channel_display = f"@{config['channel_username']} ({channel_id})"
        elif config['channel_title']:
            channel_display = f"{config['channel_title']} ({channel_id})"
        
        await update.message.reply_text(f"✅ Активний канал: {channel_display}")
    except ValueError:
        await update.message.reply_text("❌ Невірний ID каналу")

async def set_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    await update.message.reply_text("Надішліть фото для 🔴 (замінить всі існуючі)")
    context.user_data["waiting_for"] = "set_red"

async def set_green(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    await update.message.reply_text("Надішліть фото для 🟢 (замінить всі існуючі)")
    context.user_data["waiting_for"] = "set_green"

async def add_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    await update.message.reply_text("Надішліть фото для додавання до 🔴")
    context.user_data["waiting_for"] = "add_red"

async def add_green(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    await update.message.reply_text("Надішліть фото для додавання до 🟢")
    context.user_data["waiting_for"] = "add_green"

async def list_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    config = get_channel_config(channel_id)
    if not config['red_images']:
        await update.message.reply_text("🔴 Немає зображень")
        return
    
    await update.message.reply_text(f"🔴 Зображень: {len(config['red_images'])}\n\nВикористовуйте /remove_red <номер> для видалення")
    
    # Send each image with its number
    for i, image_id in enumerate(config['red_images'], 1):
        await update.message.reply_photo(photo=image_id, caption=f"#{i}")

async def list_green(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    config = get_channel_config(channel_id)
    if not config['green_images']:
        await update.message.reply_text("🟢 Немає зображень")
        return
    
    await update.message.reply_text(f"🟢 Зображень: {len(config['green_images'])}\n\nВикористовуйте /remove_green <номер> для видалення")
    
    # Send each image with its number
    for i, image_id in enumerate(config['green_images'], 1):
        await update.message.reply_photo(photo=image_id, caption=f"#{i}")

async def remove_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    if not context.args:
        await update.message.reply_text("Використання: /remove_red <номер>")
        return
    
    try:
        index = int(context.args[0]) - 1
        remove_channel_image(channel_id, "red", index)
        await update.message.reply_text(f"✅ Видалено зображення #{index+1} з 🔴")
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Невірний номер зображення")

async def remove_green(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    if not context.args:
        await update.message.reply_text("Використання: /remove_green <номер>")
        return
    
    try:
        index = int(context.args[0]) - 1
        remove_channel_image(channel_id, "green", index)
        await update.message.reply_text(f"✅ Видалено зображення #{index+1} з 🟢")
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Невірний номер зображення")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    config = get_channel_config(channel_id)
    
    # Build channel display name
    channel_display = f"{channel_id}"
    if config['channel_username']:
        channel_display = f"@{config['channel_username']} ({channel_id})"
    elif config['channel_title']:
        channel_display = f"{config['channel_title']} ({channel_id})"
    
    await update.message.reply_text(
        f"Канал: {channel_display}\n"
        f"Власник: {config['owner_id']}\n"
        f"🔴 зображень: {len(config['red_images'])}\n"
        f"🟢 зображень: {len(config['green_images'])}\n"
        f"Текст для 🟢: {config['text_on']}\n"
        f"Текст для 🔴: {config['text_off']}"
    )

async def set_text_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Використання: /set_text_on <текст>\n\n"
            "Приклад:\n"
            "/set_text_on Електрохарчування відновлено"
        )
        return
    
    text = " ".join(context.args)
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE channels SET text_on = ? WHERE channel_id = ?", (text, channel_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Текст для 🟢 встановлено: {text}")

async def set_text_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Використання: /set_text_off <текст>\n\n"
            "Приклад:\n"
            "/set_text_off Електрохарчування відсутнє"
        )
        return
    
    text = " ".join(context.args)
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE channels SET text_off = ? WHERE channel_id = ?", (text, channel_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Текст для 🔴 встановлено: {text}")

async def reset_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE channels SET text_on = NULL, text_off = NULL WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text("✅ Текст скинуто до стандартного (світло з'явилося / світло зникло)")

async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not context.args:
        await update.message.reply_text("Використання: /transfer <user_id>")
        return
    
    try:
        new_owner_id = int(context.args[0])
        
        if not is_owner(channel_id, user_id):
            await update.message.reply_text("❌ Ви не є власником цього каналу")
            return
        
        transfer_ownership(channel_id, new_owner_id)
        
        await update.message.reply_text(f"✅ Права власності передано користувачу {new_owner_id}")
    except ValueError:
        await update.message.reply_text("❌ Невірний ID користувача")

async def remove_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    remove_channel(channel_id)
    
    await update.message.reply_text(f"✅ Налаштування каналу {channel_id} видалено")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    
    waiting_for = context.user_data.get("waiting_for")
    if not waiting_for:
        return
    
    user_id = update.message.from_user.id
    channel_id = get_user_active_channel(user_id)
    
    if not channel_id:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    photo = update.message.photo[-1]
    
    # Handle different actions
    if waiting_for in ["set_red", "set_green"]:
        color = waiting_for.split("_")[1]
        update_channel_image(channel_id, color, photo.file_id)
        await update.message.reply_text(f"✅ Зображення для {'🔴' if color == 'red' else '🟢'} замінено")
    elif waiting_for in ["add_red", "add_green"]:
        color = waiting_for.split("_")[1]
        add_channel_image(channel_id, color, photo.file_id)
        config = get_channel_config(channel_id)
        count = len(config['red_images']) if color == 'red' else len(config['green_images'])
        await update.message.reply_text(f"✅ Додано зображення до {'🔴' if color == 'red' else '🟢'} (всього: {count})")
    
    context.user_data.pop("waiting_for")

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post or not update.channel_post.text:
        return
    
    text = update.channel_post.text
    channel_id = update.channel_post.chat_id
    config = get_channel_config(channel_id)
    
    # Update channel info if we have it
    if update.channel_post.chat:
        chat = update.channel_post.chat
        username = chat.username if hasattr(chat, 'username') else None
        title = chat.title if hasattr(chat, 'title') else None
        if username or title:
            update_channel_info(channel_id, username, title)
    
    # Use custom text patterns or defaults
    text_off = config.get("text_off", "світло зникло")
    text_on = config.get("text_on", "світло з'явилося")
    
    if re.search(rf"🔴.*{re.escape(text_off)}", text, re.IGNORECASE):
        images = config.get("red_images", [])
    elif re.search(rf"🟢.*{re.escape(text_on)}", text, re.IGNORECASE):
        images = config.get("green_images", [])
    else:
        return
    
    if images:
        # Randomly select one image
        image_id = random.choice(images)
        from telegram import InputMediaPhoto
        await update.channel_post.edit_media(
            media=InputMediaPhoto(media=image_id, caption=text)
        )

async def handle_forwarded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    
    # Check if forwarded from channel using forward_origin
    if hasattr(msg, 'forward_origin') and msg.forward_origin:
        origin = msg.forward_origin
        # Check if it's a channel forward
        if hasattr(origin, 'chat') and origin.chat and origin.chat.type == "channel":
            channel_id = origin.chat.id
            channel_username = origin.chat.username if hasattr(origin.chat, 'username') else None
            channel_title = origin.chat.title if hasattr(origin.chat, 'title') else None
            
            # Build display message
            channel_display = f"{channel_id}"
            if channel_username:
                channel_display = f"@{channel_username} ({channel_id})"
            elif channel_title:
                channel_display = f"{channel_title} ({channel_id})"
            
            await msg.reply_text(
                f"ID каналу: {channel_display}\n\n"
                f"Використайте: /set_channel {channel_id}"
            )
            return
    
    # Fallback: check old API
    if hasattr(msg, 'forward_from_chat') and msg.forward_from_chat:
        if msg.forward_from_chat.type == "channel":
            channel_id = msg.forward_from_chat.id
            await msg.reply_text(
                f"ID каналу: {channel_id}\n\n"
                f"Використайте: /set_channel {channel_id}"
            )

def main():
    init_db()
    
    # Try environment variable first, then token.txt
    import os
    token = os.getenv("BOT_TOKEN")
    if not token:
        with open("token.txt") as f:
            token = f.read().strip()
    
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_channel", set_channel))
    app.add_handler(CommandHandler("set_red", set_red))
    app.add_handler(CommandHandler("set_green", set_green))
    app.add_handler(CommandHandler("add_red", add_red))
    app.add_handler(CommandHandler("add_green", add_green))
    app.add_handler(CommandHandler("list_red", list_red))
    app.add_handler(CommandHandler("list_green", list_green))
    app.add_handler(CommandHandler("remove_red", remove_red))
    app.add_handler(CommandHandler("remove_green", remove_green))
    app.add_handler(CommandHandler("set_text_on", set_text_on))
    app.add_handler(CommandHandler("set_text_off", set_text_off))
    app.add_handler(CommandHandler("reset_text", reset_text))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("remove_channel", remove_channel_cmd))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_photo))
    app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, handle_forwarded))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    # Start health check server for Render
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")
        def log_message(self, format, *args):
            pass  # Suppress logs
    
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    
    app.run_polling()

if __name__ == "__main__":
    main()
