from __future__ import annotations

from scripts.telegram_notify import build_message, split_message


def test_pre_match_ticket_message_contains_coupon_summary() -> None:
    message = build_message(
        {
            "phase": "pre_match",
            "day": "2026-08-25",
            "run_id": "run-123",
            "daily_prediction_count": 4,
            "selection_count": 2,
            "ticket_count": 1,
            "notice": "Strict gate empty; forced banko mode selected the safest pair.",
            "tickets": [
                {
                    "label": "Zorunlu günlük banko ikilisi",
                    "combined_probability": "0.420280",
                    "combined_decimal_odds": "2.01",
                    "risk_label": "controlled",
                    "legs": [
                        {
                            "fixture": "Barcelona - Athletic Club",
                            "league": "La Liga",
                            "market": "Maç sonucu",
                            "pick": "Barcelona",
                            "probability": "0.706578",
                            "odds": "1.33",
                            "reason": "Home dominance and squad edge survived market sanity checks.",
                        }
                    ],
                }
            ],
        }
    )

    assert "MİRON BABA AI günlük kupon" in message
    assert "Zorunlu günlük banko ikilisi" in message
    assert "Toplam: oran 2.01 | hesap ihtimali 42.0%" in message
    assert "Barcelona - Athletic Club" in message
    assert "İhtimal: 70.7%" in message


def test_post_match_message_contains_learning_summary() -> None:
    message = build_message(
        {
            "phase": "post_match",
            "day": "2026-08-26",
            "settled_count": 3,
            "daily_reviewed_count": 7,
            "performance": {
                "settled_count": 12,
                "hit_rate": "0.5833",
                "mean_brier_score": "0.211",
                "roi": "0.082",
            },
        }
    )

    assert "sonuç kontrolü" in message
    assert "3 kupon/analiz kapandı" in message
    assert "İsabet: 58.3%" in message
    assert "ROI: 8.2%" in message
    assert "case memory" in message


def test_split_message_respects_telegram_limit() -> None:
    chunks = split_message("a\n" * 5000)

    assert len(chunks) > 1
    assert all(len(chunk) <= 4096 for chunk in chunks)
