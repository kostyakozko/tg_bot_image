import re
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

DB_FILE = "config.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            owner_id INTEGER,
            red_image TEXT,
            green_image TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_channel_config(channel_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.execute("SELECT owner_id, red_image, green_image FROM channels WHERE channel_id = ?", (channel_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"owner_id": row[0], "red_image": row[1], "green_image": row[2]}
    return {"owner_id": None, "red_image": None, "green_image": None}

def set_channel_owner(channel_id, owner_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("INSERT OR IGNORE INTO channels (channel_id, owner_id) VALUES (?, ?)", (channel_id, owner_id))
    conn.commit()
    conn.close()

def update_channel_image(channel_id, color, file_id):
    conn = sqlite3.connect(DB_FILE)
    if color == "red":
        conn.execute("UPDATE channels SET red_image = ? WHERE channel_id = ?", (file_id, channel_id))
    else:
        conn.execute("UPDATE channels SET green_image = ? WHERE channel_id = ?", (file_id, channel_id))
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
        "/set_red - встановити зображення для 🔴\n"
        "/set_green - встановити зображення для 🟢\n"
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
        
        context.user_data["active_channel"] = channel_id
        await update.message.reply_text(f"✅ Активний канал: {channel_id}")
    except ValueError:
        await update.message.reply_text("❌ Невірний ID каналу")

async def set_red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "active_channel" not in context.user_data:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    channel_id = context.user_data["active_channel"]
    user_id = update.message.from_user.id
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    await update.message.reply_text("Надішліть фото для 🔴 (світло зникло)")
    context.user_data["waiting_for"] = "red"

async def set_green(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "active_channel" not in context.user_data:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    channel_id = context.user_data["active_channel"]
    user_id = update.message.from_user.id
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    await update.message.reply_text("Надішліть фото для 🟢 (світло з'явилося)")
    context.user_data["waiting_for"] = "green"

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "active_channel" not in context.user_data:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    channel_id = context.user_data["active_channel"]
    user_id = update.message.from_user.id
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    config = get_channel_config(channel_id)
    
    await update.message.reply_text(
        f"Канал: {channel_id}\n"
        f"Власник: {config['owner_id']}\n"
        f"🔴 зображення: {'✅' if config['red_image'] else '❌'}\n"
        f"🟢 зображення: {'✅' if config['green_image'] else '❌'}"
    )

async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "active_channel" not in context.user_data:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    if not context.args:
        await update.message.reply_text("Використання: /transfer <user_id>")
        return
    
    try:
        new_owner_id = int(context.args[0])
        channel_id = context.user_data["active_channel"]
        user_id = update.message.from_user.id
        
        if not is_owner(channel_id, user_id):
            await update.message.reply_text("❌ Ви не є власником цього каналу")
            return
        
        transfer_ownership(channel_id, new_owner_id)
        
        await update.message.reply_text(f"✅ Права власності передано користувачу {new_owner_id}")
    except ValueError:
        await update.message.reply_text("❌ Невірний ID користувача")

async def remove_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "active_channel" not in context.user_data:
        await update.message.reply_text("❌ Спочатку встановіть канал: /set_channel <channel_id>")
        return
    
    channel_id = context.user_data["active_channel"]
    user_id = update.message.from_user.id
    
    if not is_owner(channel_id, user_id):
        await update.message.reply_text("❌ Ви не є власником цього каналу")
        return
    
    remove_channel(channel_id)
    context.user_data.pop("active_channel")
    
    await update.message.reply_text(f"✅ Налаштування каналу {channel_id} видалено")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    
    waiting_for = context.user_data.get("waiting_for")
    if not waiting_for or "active_channel" not in context.user_data:
        return
    
    photo = update.message.photo[-1]
    channel_id = context.user_data["active_channel"]
    update_channel_image(channel_id, waiting_for, photo.file_id)
    
    await update.message.reply_text(f"✅ Зображення для {'🔴' if waiting_for == 'red' else '🟢'} збережено")
    context.user_data.pop("waiting_for")

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post or not update.channel_post.text:
        return
    
    text = update.channel_post.text
    channel_id = update.channel_post.chat_id
    config = get_channel_config(channel_id)
    
    if re.search(r"🔴.*світло зникло", text, re.IGNORECASE):
        image_id = config.get("red_image")
    elif re.search(r"🟢.*світло з'явилося", text, re.IGNORECASE):
        image_id = config.get("green_image")
    else:
        return
    
    if image_id:
        await update.channel_post.edit_text(
            text=text,
            photo=image_id
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
            await msg.reply_text(
                f"ID каналу: {channel_id}\n\n"
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
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("remove_channel", remove_channel_cmd))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_photo))
    app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, handle_forwarded))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    
    app.run_polling()

if __name__ == "__main__":
    main()
