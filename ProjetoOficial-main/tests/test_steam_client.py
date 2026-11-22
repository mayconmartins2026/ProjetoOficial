from __future__ import annotations

import unittest
from unittest.mock import Mock, call, patch

from ggreviews.steam_client import (
    STEAM_APPDETAILS_URL,
    STEAM_STORESEARCH_URL,
    fetch_brazilian_game_description,
)


def response(payload: object) -> Mock:
    result = Mock()
    result.json.return_value = payload
    result.raise_for_status.return_value = None
    return result


class SteamClientTests(unittest.TestCase):
    @patch("ggreviews.steam_client.requests.get")
    def test_fetches_matching_brazilian_description(self, get: Mock) -> None:
        get.side_effect = [
            response(
                {
                    "items": [
                        {
                            "type": "app",
                            "name": "Grand Theft Auto V Legacy",
                            "id": 271590,
                        }
                    ]
                }
            ),
            response(
                {
                    "271590": {
                        "success": True,
                        "data": {
                            "short_description": (
                                "<p>Uma aventura &amp; mundo aberto.</p>"
                            )
                        },
                    }
                }
            ),
        ]

        description = fetch_brazilian_game_description("Grand Theft Auto V")

        self.assertEqual(description, "Uma aventura & mundo aberto.")
        self.assertEqual(
            get.call_args_list,
            [
                call(
                    STEAM_STORESEARCH_URL,
                    params={
                        "term": "Grand Theft Auto V",
                        "l": "brazilian",
                        "cc": "br",
                    },
                    headers={"User-Agent": "GGReviews/1.0"},
                    timeout=10,
                ),
                call(
                    STEAM_APPDETAILS_URL,
                    params={"appids": 271590, "l": "brazilian", "cc": "br"},
                    headers={"User-Agent": "GGReviews/1.0"},
                    timeout=10,
                ),
            ],
        )

    @patch("ggreviews.steam_client.requests.get")
    def test_does_not_choose_a_different_game_from_search_results(
        self, get: Mock
    ) -> None:
        get.return_value = response(
            {
                "items": [
                    {"type": "app", "name": "Firewood", "id": 615180},
                ]
            }
        )

        description = fetch_brazilian_game_description("Fire")

        self.assertIsNone(description)
        get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
