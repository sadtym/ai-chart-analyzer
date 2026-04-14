# GitHub Setup Guide for AI Chart Analyzer

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and log in
2. Click the **+** button (top right) → **New repository**
3. Fill in the details:
   - **Repository name**: `ai-chart-analyzer`
   - **Description**: `Telegram Bot for Crypto Chart Analysis with AI`
   - **Visibility**: Public (free) or Private
   - **Do NOT** check "Add a README file" (we already have one)
4. Click **Create repository**

## Step 2: Connect Local Project to GitHub

After creating the repository, GitHub will show you the URL. It will look like:
```
https://github.com/YOUR_USERNAME/ai-chart-analyzer.git
```

Run these commands in your project folder:

```bash
cd /workspace/ai_chart_analyzer
git remote add origin https://github.com/YOUR_USERNAME/ai-chart-analyzer.git
git branch -M main
git push -u origin main
```

## Step 3: Verify Upload

Refresh your GitHub repository page - you should see all your files there.

## Step 4: Clone on Another Machine (Optional)

```bash
git clone https://github.com/YOUR_USERNAME/ai-chart-analyzer.git
cd ai-chart-analyzer
pip install -r requirements.txt
python bot.py
```

## Render Deployment (After GitHub Push)

1. Go to [Render](https://render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Add environment variables:
   - `TELEGRAM_TOKEN` = your_telegram_token
   - `GEMINI_API_KEY` = your_gemini_api_key
   - `AI_PROVIDER` = gemini
5. Click **Create Web Service**

---

## Quick Commands Reference

```bash
# Check git status
git status

# Add all files
git add .

# Commit changes
git commit -m "Your message"

# Push to GitHub
git push origin main

# Clone repository
git clone https://github.com/USERNAME/ai-chart-analyzer.git

# Pull latest changes
git pull origin main
```

## Troubleshooting

### Authentication Error
If you get authentication error, use GitHub Token:
```bash
git remote set-url origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/ai-chart-analyzer.git
```

### Branch Error
```bash
git branch -M main
git push -u origin main
```

### Permission Denied
- Generate new GitHub Personal Access Token
- Use token instead of password