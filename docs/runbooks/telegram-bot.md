# Telegram daily coupon notifications

MİRON BABA AI can send the daily pre-match coupon and the next post-match learning summary to the private Telegram bot `MironMethodbot`.

## Setup

1. Open [MironMethodbot](https://t.me/MironMethodbot) and send `/start`.
2. Configure repository secrets, never plain files:

```bash
gh secret set TELEGRAM_BOT_TOKEN --repo kerimaydemir/miron-method
gh secret set TELEGRAM_CHAT_ID --repo kerimaydemir/miron-method
```

If you do not know the chat id yet, export the bot token in a private shell and run:

```bash
cd apps/api
TELEGRAM_BOT_TOKEN="..." python scripts/telegram_notify.py --get-chat-id
```

Then save the printed id as `TELEGRAM_CHAT_ID`.

## Runtime behavior

- `pre_match` sends the locked coupon summary: total odds, calculated probability, market, pick, and short reason per leg.
- `post_match` sends settlement and learning status: how many records were reviewed, hit rate, Brier score, ROI, and the case-memory note.
- If either Telegram secret is missing, the GitHub Action continues and logs a safe skip message.
- Detailed data remains in the encrypted `automation-state` branch and workflow artifacts.

The bot token should be rotated if it has ever been pasted into a chat, shell history, screenshot, or external tool output.
