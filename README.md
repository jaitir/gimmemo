# GimmeMo Telegram Bot

Telegram bot with inline menu:
- Ankета
- FAQ
- Зворотній зв'язок
- Сайт

## Features
- Inline menu and navigation
- Step-by-step questionnaire form
- FAQ block in Ukrainian
- Feedback button to Telegram contact
- Website button
- Sends completed form to Telegram user id `264354988`

## Setup
1. Create and fill `.env`:
   - `BOT_TOKEN=...`
   - optional for webhook: `WEBHOOK_BASE_URL=https://your-app.up.railway.app`
   - optional: `WEBHOOK_SECRET=your_secret_token`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run:
   - `python bot.py`

## Railway deploy
1. Push project to GitHub.
2. Create Railway project from the repo.
3. Add variable:
   - `BOT_TOKEN`
   - `WEBHOOK_BASE_URL` (for example `https://your-app.up.railway.app`)
   - `WEBHOOK_SECRET` (any random string)
4. Deploy.

If `WEBHOOK_BASE_URL` is set, bot runs in webhook mode.
If it is not set, bot runs in polling mode.
