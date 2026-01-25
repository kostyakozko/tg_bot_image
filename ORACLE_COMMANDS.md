# Oracle Cloud Management Commands

## SSH Access
```bash
ssh ubuntu@<your_ip>
```

## Bot Service Management

### Check bot status
```bash
ssh ubuntu@<your_ip> 'sudo systemctl status telegram-bot'
```

### View live logs
```bash
ssh ubuntu@<your_ip> 'sudo journalctl -u telegram-bot -f'
```

### View recent logs (last 50 lines)
```bash
ssh ubuntu@<your_ip> 'sudo journalctl -u telegram-bot -n 50 --no-pager'
```

### Restart bot
```bash
ssh ubuntu@<your_ip> 'sudo systemctl restart telegram-bot'
```

### Stop bot
```bash
ssh ubuntu@<your_ip> 'sudo systemctl stop telegram-bot'
```

### Start bot
```bash
ssh ubuntu@<your_ip> 'sudo systemctl start telegram-bot'
```

## Update Bot Code

After pushing changes to GitHub:
```bash
ssh ubuntu@<your_ip> 'cd ~/tg_bot_image && git pull && sudo systemctl restart telegram-bot'
```

## Database Management

### Backup database
```bash
scp ubuntu@<your_ip>:~/tg_bot_image/data/config.db ./config_backup.db
```

### Restore database
```bash
scp ./config_backup.db ubuntu@<your_ip>:~/tg_bot_image/data/config.db
ssh ubuntu@<your_ip> 'sudo systemctl restart telegram-bot'
```

### View database contents
```bash
ssh ubuntu@<your_ip> 'sqlite3 ~/tg_bot_image/data/config.db "SELECT * FROM channels;"'
```

## Bot Token

Current token stored in:
```bash
~/tg_bot_image/token.txt
```

To update token:
```bash
ssh ubuntu@<your_ip> 'echo "NEW_TOKEN_HERE" > ~/tg_bot_image/token.txt && sudo systemctl restart telegram-bot'
```

## System Information

### Check disk space
```bash
ssh ubuntu@<your_ip> 'df -h'
```

### Check memory usage
```bash
ssh ubuntu@<your_ip> 'free -h'
```

### Check bot process
```bash
ssh ubuntu@<your_ip> 'ps aux | grep bot.py'
```

## BotFather Commands List

For setting up command menu in @BotFather:
```
start - Show available commands
set_channel - Set which channel to configure
set_red - Replace all images for 🔴 (power off)
set_green - Replace all images for 🟢 (power on)
add_red - Add image to 🔴 collection
add_green - Add image to 🟢 collection
list_red - List all 🔴 images
list_green - List all 🟢 images
remove_red - Remove 🔴 image by number
remove_green - Remove 🟢 image by number
status - Check current configuration
transfer - Transfer ownership to another user
remove_channel - Delete channel configuration
```
