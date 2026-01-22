# Deployment Guide

# Render.com (Recommended - Free Forever)

1. Go to https://render.com and sign up with GitHub
2. Click "New +" → "Web Service"
3. Connect your GitHub account and select `kostyakozko/tg_bot_image`
4. Settings:
   - **Name**: tg-bot-image (or whatever you want)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: Free
5. Click "Advanced" and add environment variable:
   - Key: `BOT_TOKEN`
   - Value: Your bot token from @BotFather
6. Click "Create Web Service"

Render provides:
- 750 hours/month free (enough for 24/7)
- Persistent disk (database survives deployments)
- Automatic deployments on git push
- Actually free forever (not a trial)

## Railway.app

1. Create account at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub account and select this repository
4. Add environment variable:
   - Key: `BOT_TOKEN`
   - Value: Your bot token from @BotFather
5. Add a Volume for persistence:
   - Settings → Volumes → New Volume
   - Mount path: `/app/data`
6. Deploy automatically starts

Note: Railway free tier is only 30 days trial, then paid (~$5-10/month).

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
