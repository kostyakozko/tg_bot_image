# Deployment Guide

## Railway.app (Recommended)

1. Create account at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub account and select this repository
4. Add environment variable:
   - Key: `BOT_TOKEN`
   - Value: Your bot token from @BotFather
5. Deploy automatically starts

Railway provides:
- 500 hours/month free (enough for 24/7)
- Automatic deployments on git push
- Built-in SQLite persistence

## Render.com (Alternative)

1. Create account at [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect repository
4. Settings:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
5. Add environment variable `BOT_TOKEN`
6. Create Web Service (free tier)

## Local Development

1. Create `token.txt` with your bot token
2. Run:
```bash
pip install -r requirements.txt
python bot.py
```

## Environment Variables

For deployment platforms, the bot reads token from:
1. `BOT_TOKEN` environment variable (if set)
2. `token.txt` file (fallback for local dev)
