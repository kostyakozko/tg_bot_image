# Telegram Power Status Bot

Bot that monitors a Telegram channel for power status messages and adds images to them.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `token.txt` with your bot token from @BotFather

3. **IMPORTANT:** Add bot to your channel as admin with these permissions:
   - ✅ Edit messages of others
   - (All other permissions can be disabled)

4. Run:
```bash
python bot.py
```

## Configuration

Send commands to bot in DM:
- `/start` - show available commands
- `/set_channel <channel_id>` - set which channel to configure
- `/set_red` - set image for 🔴 (power off)
- `/set_green` - set image for 🟢 (power on)
- `/status` - check current configuration
- `/transfer <user_id>` - transfer ownership to another user
- `/remove_channel` - delete channel configuration

**To get your channel ID:**
Forward any message from your channel to the bot in DM, and it will show you the channel ID.

**Configuration workflow:**
1. Add bot to your channel as admin (with "Edit messages" permission)
2. Forward a message from your channel to the bot in DM
3. Use `/set_channel <channel_id>` with the ID shown
4. Use `/set_red` and send a photo
5. Use `/set_green` and send a photo

Each channel has its own independent configuration.

**Ownership:**
- First user to configure a channel becomes its owner
- Only the owner can modify settings
- Owner can transfer ownership with `/transfer <user_id>`
- Owner can remove channel config with `/remove_channel`

**Testing:**
You can create a test channel first, configure the bot there, test it, then use `/remove_channel` to clean up and configure your real channel.

## How it works

Bot monitors channel for messages containing:
- `🔴` + "світло зникло" → adds red image
- `🟢` + "світло з'явилося" → adds green image
