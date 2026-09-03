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
            "ticket_reviews": [
                {
                    "label": "Günlük ikili",
                    "odds": "2.04",
                    "status": "lost",
                    "legs": [
                        {
                            "fixture": "Valencia - Sevilla",
                            "pick": "2.5 Alt",
                            "odds": "1.55",
                            "score": "2-1",
                            "status": "lost",
                        }
                    ],
                }
            ],
            "daily_reviews": [
                {
                    "fixture": "Valencia - Sevilla",
                    "market": "Toplam gol",
                    "pick": "2.5 Alt",
                    "odds": "1.55",
                    "status": "lost",
                    "score": "2-1",
                    "explanation": "Toplam gol üçe çıktığı için alt çizgisi kaybetti.",
                    "lesson": "Aynı çizgide tekrar eden sapma takip edilecek.",
                }
            ],
        }
    )

    assert "sonuç kontrolü" in message
    assert "3 kupon/analiz kapandı" in message
    assert "İsabet: 58.3%" in message
    assert "ROI: 8.2%" in message
    assert "case memory" in message
    assert "Kupon sonuçları:" in message
    assert "Günlük ikili | toplam oran 2.04" in message
    assert "Valencia - Sevilla" in message
    assert "Toplam gol üçe çıktığı" in message


def test_split_message_respects_telegram_limit() -> None:
    chunks = split_message("a\n" * 5000)

    assert len(chunks) > 1
    assert all(len(chunk) <= 4096 for chunk in chunks)


def test_pre_match_without_live_odds_does_not_pose_fixture_as_coupon() -> None:
    message = build_message(
        {
            "phase": "pre_match",
            "day": "2026-09-04",
            "daily_prediction_count": 1,
            "selection_count": 0,
            "ticket_count": 0,
            "notice": "Canlı bookmaker oranı alınamadı.",
            "daily_predictions": [
                {
                    "fixture": "VfB Stuttgart - 1. FC Köln",
                    "market": "Oran bekleniyor",
                    "pick": "Kupon kilidi yok",
                    "odds": None,
                }
            ],
        }
    )

    assert "doğrulanmış canlı bookmaker oranı gelmedi" in message
    assert "VfB Stuttgart - 1. FC Köln" not in message
