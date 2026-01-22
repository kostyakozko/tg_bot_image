#!/bin/bash
# Oracle Cloud deployment script for Telegram bot

set -e

echo "==> Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip git

echo "==> Cloning repository..."
cd ~
git clone https://github.com/kostyakozko/tg_bot_image.git
cd tg_bot_image

echo "==> Installing Python dependencies..."
pip3 install -r requirements.txt

echo "==> Creating token file..."
read -p "Enter your bot token: " BOT_TOKEN
echo "$BOT_TOKEN" > token.txt

echo "==> Creating systemd service..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram Power Status Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/tg_bot_image
ExecStart=/usr/bin/python3 /home/$USER/tg_bot_image/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "==> Starting bot service..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

echo "==> Done! Bot is running."
echo "Check status with: sudo systemctl status telegram-bot"
echo "View logs with: sudo journalctl -u telegram-bot -f"
