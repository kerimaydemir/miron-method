from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from textwrap import shorten
from typing import Any

import httpx

TELEGRAM_MESSAGE_LIMIT = 4096
SAFE_CHUNK_LIMIT = 3600
BOT_LINK = "https://t.me/MironMethodbot"


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, dict):
        return value
    return {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _text(value: object, fallback: str = "-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _percent(value: object) -> str:
    decimal = _decimal(value)
    if decimal is None:
        return "-"
    if decimal <= Decimal("1"):
        decimal *= Decimal("100")
    return f"{decimal.quantize(Decimal('0.1'))}%"


def _odds(value: object) -> str:
    decimal = _decimal(value)
    if decimal is None:
        return "-"
    return f"{decimal.quantize(Decimal('0.01'))}"


def _compact(value: object, width: int = 170) -> str:
    return shorten(_text(value), width=width, placeholder="…")


def _bookmaker_suffix(value: object) -> str:
    bookmaker = "" if value is None else " ".join(str(value).split())
    return f" [{bookmaker}]" if bookmaker else ""


def _title(report: Mapping[str, object]) -> str:
    phase = _text(report.get("phase"))
    day = _text(report.get("day"))
    if phase == "post_match":
        return f"📊 MİRON BABA AI sonuç kontrolü — {day}"
    return f"🎯 MİRON BABA AI günlük kupon — {day}"


def build_pre_match_message(report: Mapping[str, object]) -> str:
    lines = [_title(report)]

    tickets = _as_sequence(report.get("tickets"))
    if tickets:
        for ticket_index, ticket_value in enumerate(tickets, start=1):
            ticket = _as_mapping(ticket_value)
            lines.append(
                f"Kupon {ticket_index} | Toplam oran: {_odds(ticket.get('combined_decimal_odds'))}"
            )
            for leg_index, leg_value in enumerate(_as_sequence(ticket.get("legs")), start=1):
                leg = _as_mapping(leg_value)
                lines.append(
                    f"{leg_index}) {_text(leg.get('fixture'))} — "
                    f"{_text(leg.get('pick'))} @{_odds(leg.get('odds'))}"
                    f"{_bookmaker_suffix(leg.get('bookmaker'))}"
                )
    else:
        priced_predictions = tuple(
            item
            for item in _as_sequence(report.get("daily_predictions"))
            if _decimal(_as_mapping(item).get("odds")) is not None
        )
        if not priced_predictions:
            lines.append("Bugün doğrulanmış oran yok; kupon paylaşılmadı.")
        else:
            lines.append("Kupon kilitlenmedi. En iyi fiyatlı fikirler:")
        for index, item_value in enumerate(priced_predictions[:3], start=1):
            item = _as_mapping(item_value)
            lines.append(
                f"{index}) {_text(item.get('fixture'))} — {_text(item.get('pick'))} "
                f"@{_odds(item.get('odds'))}{_bookmaker_suffix(item.get('bookmaker'))}"
            )
    return "\n".join(lines).strip()


def build_post_match_message(report: Mapping[str, object]) -> str:
    ticket_reviews = _as_sequence(report.get("ticket_reviews"))
    daily_reviews = _as_sequence(report.get("daily_reviews"))
    if not ticket_reviews and not daily_reviews:
        return ""
    performance = _as_mapping(report.get("performance"))
    lines = [_title(report)]
    if ticket_reviews:
        lines.append("Kupon sonucu:")
        icons = {
            "won": "✅ Tuttu",
            "lost": "❌ Kaybetti",
            "void": "➖ Void",
            "pending": "⏳ Bekliyor",
        }
        for ticket_value in ticket_reviews:
            ticket = _as_mapping(ticket_value)
            lines.append(
                f"- {icons.get(_text(ticket.get('status')), '⏳ Bekliyor')}: "
                f"{_text(ticket.get('label'))} | toplam oran {_odds(ticket.get('odds'))}"
            )
            for leg_value in _as_sequence(ticket.get("legs")):
                leg = _as_mapping(leg_value)
                lines.append(
                    f"• {_text(leg.get('fixture'))}: {_text(leg.get('pick'))} "
                    f"@{_odds(leg.get('odds'))} | {_text(leg.get('score'))} | "
                    f"{icons.get(_text(leg.get('status')), '⏳ Bekliyor')}"
                    f"{_bookmaker_suffix(leg.get('bookmaker'))}"
                )

    if daily_reviews:
        lines.append("Diğer sonuçlar:")
        icons = {"won": "✅ Tuttu", "lost": "❌ Kaybetti", "void": "➖ Void"}
        for review_value in daily_reviews[:3]:
            review = _as_mapping(review_value)
            lines.append(
                f"• {icons.get(_text(review.get('status')), '•')} "
                f"{_text(review.get('fixture'))} — {_text(review.get('pick'))} "
                f"@{_odds(review.get('odds'))} | {_text(review.get('score'))}"
            )
    if performance:
        lines.append(
            f"Genel: {_text(performance.get('wins'), '0')}/"
            f"{_text(performance.get('settled'), '0')} | %{_percent(performance.get('hit_rate')).rstrip('%')}"
        )
    return "\n".join(lines).strip()


def build_message(report: Mapping[str, object]) -> str:
    if _text(report.get("phase")) == "post_match":
        return build_post_match_message(report)
    return build_pre_match_message(report)


def split_message(message: str) -> list[str]:
    if len(message) <= TELEGRAM_MESSAGE_LIMIT:
        return [message]
    chunks: list[str] = []
    pending = message
    while len(pending) > SAFE_CHUNK_LIMIT:
        split_at = pending.rfind("\n", 0, SAFE_CHUNK_LIMIT)
        if split_at < 1:
            split_at = SAFE_CHUNK_LIMIT
        chunks.append(pending[:split_at].strip())
        pending = pending[split_at:].strip()
    if pending:
        chunks.append(pending)
    return chunks


def send_telegram_message(token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with httpx.Client(timeout=20) as client:
        for chunk in split_message(message):
            response = client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
            )
            response.raise_for_status()


def discover_chat_ids(token: str) -> list[str]:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = httpx.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()
    results = _as_sequence(_as_mapping(payload).get("result"))
    chat_ids: list[str] = []
    for update_value in results:
        update = _as_mapping(update_value)
        message = _as_mapping(update.get("message") or update.get("channel_post"))
        chat = _as_mapping(message.get("chat"))
        chat_id = chat.get("id")
        if chat_id is not None:
            chat_ids.append(str(chat_id))
    return sorted(set(chat_ids))


def load_report(path: Path) -> Mapping[str, object]:
    with path.open(encoding="utf-8") as file:
        payload: Any = json.load(file)
    if not isinstance(payload, dict):
        msg = f"Telegram report must be a JSON object: {path}"
        raise ValueError(msg)
    return payload


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send MİRON BABA daily report to Telegram.")
    parser.add_argument("report", nargs="?", type=Path, help="Path to pre_match/post_match JSON report")
    parser.add_argument(
        "--get-chat-id",
        action="store_true",
        help="Print chat ids from Telegram getUpdates after the user sends /start.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token:
        print("Telegram skipped: TELEGRAM_BOT_TOKEN secret is not configured.")
        print(f"Open the bot first: {BOT_LINK}")
        return 0
    if args.get_chat_id:
        chat_ids = discover_chat_ids(token)
        if not chat_ids:
            print(f"No chat id yet. Open {BOT_LINK}, send /start, then rerun this command.")
            return 0
        print("Telegram chat id candidates:")
        for candidate in chat_ids:
            print(candidate)
        return 0
    if not chat_id:
        print("Telegram skipped: TELEGRAM_CHAT_ID secret is not configured.")
        print(f"Open {BOT_LINK}, send /start, then run with --get-chat-id.")
        return 0
    if args.report is None:
        print("Telegram skipped: report path was not provided.")
        return 0
    report = load_report(args.report)
    message = build_message(report)
    if not message:
        print("Telegram skipped: no newly settled results.")
        return 0
    send_telegram_message(token=token, chat_id=chat_id, message=message)
    print("Telegram notification sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
