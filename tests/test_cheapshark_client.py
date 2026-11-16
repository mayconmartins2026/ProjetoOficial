from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import requests

from ggreviews.cheapshark_client import (
    CHEAPSHARK_API_BASE,
    EXCHANGE_RATE_URL,
    fetch_game_details,
    fetch_promotions,
    fetch_store_names,
    fetch_usd_to_brl_rate,
    promotion_url,
    search_games,
)


def json_response(payload: object) -> Mock:
    response = Mock()
    response.json.return_value = payload
    return response


class CheapSharkClientTests(unittest.TestCase):
    @patch("ggreviews.cheapshark_client.requests.get")
    def test_search_games_normalizes_cheapshark_results(self, get: Mock) -> None:
        get.return_value = json_response(
            [
                {
                    "gameID": "196149",
                    "external": "Hades",
                    "thumb": "https://images.example/hades.jpg",
                    "cheapest": "24.99",
                    "cheapestDealID": "deal-id",
                },
                {"gameID": "invalid", "external": "Invalid"},
            ]
        )

        games = search_games(" Hades ")

        self.assertEqual(
            games,
            [
                {
                    "id": "196149",
                    "name": "Hades",
                    "background_image": "https://images.example/hades.jpg",
                    "cheapest": Decimal("24.99"),
                    "cheapest_deal_id": "deal-id",
                }
            ],
        )
        get.assert_called_once_with(
            f"{CHEAPSHARK_API_BASE}/games",
            params={"title": "Hades"},
            headers={"User-Agent": "GGReviews/1.0"},
            timeout=10,
        )

    @patch("ggreviews.cheapshark_client.requests.get")
    def test_empty_game_search_does_not_call_api(self, get: Mock) -> None:
        self.assertEqual(search_games("  "), [])
        get.assert_not_called()

    @patch("ggreviews.cheapshark_client.requests.get")
    def test_fetch_game_details_uses_curated_cheapshark_id(self, get: Mock) -> None:
        get.return_value = json_response(
            {
                "info": {
                    "title": "Hades",
                    "thumb": "https://images.example/hades.jpg",
                },
                "deals": [
                    {"dealID": "deal-2", "price": "12.99"},
                    {"dealID": "deal-1", "price": "8.49"},
                    {"dealID": "invalid", "price": "not-a-price"},
                ],
            }
        )

        details = fetch_game_details("196149")

        self.assertEqual(
            details,
            {
                "id": "196149",
                "name": "Hades",
                "background_image": "https://images.example/hades.jpg",
                "deal_id": "deal-1",
                "sale_price": Decimal("8.49"),
            },
        )
        get.assert_called_once_with(
            f"{CHEAPSHARK_API_BASE}/games",
            params={"id": "196149"},
            headers={"User-Agent": "GGReviews/1.0"},
            timeout=10,
        )

    @patch("ggreviews.cheapshark_client.requests.get")
    def test_fetch_game_details_handles_missing_match_and_rejects_bad_id(
        self, get: Mock
    ) -> None:
        get.return_value = json_response({"info": None})

        self.assertIsNone(fetch_game_details("196149"))
        with self.assertRaises(ValueError):
            fetch_game_details("not-an-id")
        get.assert_called_once()

    @patch("ggreviews.cheapshark_client.requests.get")
    def test_fetch_promotions_keeps_valid_discounted_deals(self, get: Mock) -> None:
        get.return_value = json_response(
            [
                {
                    "title": "Game",
                    "dealID": "deal-id",
                    "storeID": "1",
                    "salePrice": "4.99",
                    "normalPrice": "9.99",
                    "savings": "50.050050",
                    "isOnSale": "1",
                    "thumb": "https://images.example/game.jpg",
                },
                {
                    "title": "Not on sale",
                    "dealID": "other-id",
                    "storeID": "2",
                    "salePrice": "9.99",
                    "normalPrice": "9.99",
                    "savings": "0",
                    "isOnSale": "0",
                },
            ]
        )

        promotions = fetch_promotions()

        self.assertEqual(len(promotions), 1)
        self.assertEqual(promotions[0]["sale_price"], Decimal("4.99"))
        self.assertEqual(promotions[0]["normal_price"], Decimal("9.99"))
        self.assertAlmostEqual(float(promotions[0]["savings"]), 50.05005, places=5)
        get.assert_called_once_with(
            f"{CHEAPSHARK_API_BASE}/deals",
            params={"onSale": 1, "pageSize": 60, "sortBy": "Savings", "desc": 1},
            headers={"User-Agent": "GGReviews/1.0"},
            timeout=10,
        )

    @patch("ggreviews.cheapshark_client.requests.get")
    def test_fetches_store_names_by_id(self, get: Mock) -> None:
        get.return_value = json_response(
            [
                {"storeID": "1", "storeName": "Steam", "isActive": 1},
                {"storeID": "2", "storeName": "GamersGate", "isActive": 1},
                {"storeID": "invalid", "storeName": "Invalid"},
            ]
        )

        self.assertEqual(fetch_store_names(), {"1": "Steam", "2": "GamersGate"})
        get.assert_called_once_with(
            f"{CHEAPSHARK_API_BASE}/stores",
            params=None,
            headers={"User-Agent": "GGReviews/1.0"},
            timeout=10,
        )

    @patch("ggreviews.cheapshark_client.requests.get")
    def test_fetches_usd_to_brl_rate_and_effective_date(self, get: Mock) -> None:
        get.return_value = json_response(
            {"date": "2026-11-09", "rates": {"BRL": 5.5167}}
        )

        rate, rate_date = fetch_usd_to_brl_rate()

        self.assertEqual(rate, Decimal("5.5167"))
        self.assertEqual(rate_date, date(2026, 11, 9))
        get.assert_called_once_with(
            EXCHANGE_RATE_URL,
            params={"from": "USD", "to": "BRL"},
            headers={"User-Agent": "GGReviews/1.0"},
            timeout=10,
        )

    @patch("ggreviews.cheapshark_client.requests.get")
    def test_invalid_exchange_rate_is_reported(self, get: Mock) -> None:
        get.return_value = json_response({"date": "not-a-date", "rates": {"BRL": 0}})

        with self.assertRaises(ValueError):
            fetch_usd_to_brl_rate()

    @patch("ggreviews.cheapshark_client.requests.get")
    def test_http_errors_are_propagated(self, get: Mock) -> None:
        response = json_response({})
        response.raise_for_status.side_effect = requests.HTTPError("unavailable")
        get.return_value = response

        with self.assertRaises(requests.HTTPError):
            fetch_promotions()

    def test_promotion_link_uses_cheapshark_redirect(self) -> None:
        self.assertEqual(
            promotion_url("deal%2Fid%2Btoken%3D"),
            "https://www.cheapshark.com/redirect?dealID=deal%2Fid%2Btoken%3D",
        )
