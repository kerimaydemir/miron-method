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
TELEGRAM_BOT_TOKEN="..." docker compose run --rm api \
  python scripts/telegram_notify.py --get-chat-id
```

Then save the printed id as `TELEGRAM_CHAT_ID`.

## Runtime behavior

- `pre_match` sends a short coupon summary: total odds, explicitly labelled model
  or bookmaker-consensus probability, pick, actual bookmaker price, and bookmaker
  name per leg.
- Pick labels use familiar Türkiye coupon wording where the data supports it: `MS 1`,
  `MS X`, `MS 2`, `Çifte Şans 1X/12/X2`, `KG Var/Yok`, `2.5 Üst/Alt`,
  `İY 1/X/2`, `Handikap`, `Korner Handikap`, and `Kart Handikap`.
- `post_match` sends only newly settled coupon legs plus the current hit rate; an
  empty pass does not spam Telegram.
- Missing Telegram secrets fail the unattended workflow loudly after encrypted
  state is saved, instead of silently pretending delivery succeeded.
- Detailed data remains in the encrypted `automation-state` branch and workflow artifacts.

The bot token should be rotated if it has ever been pasted into a chat, shell history, screenshot, or external tool output.
