from __future__ import annotations

import unittest
from ggreviews.game_compatibility import (
    MINIMUM_DATA_COVERAGE,
    normalize_preferences,
    recommend_games,
    score_game,
)


class GameCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.preferences = {
            "generos": ["Action"],
            "estilos": ["Fantasy"],
            "narrativa": 4,
            "exploracao": 2,
            "dificuldade": 2,
            "modos": ["Single player"],
            "plataformas": ["PC"],
        }
        self.game = {
            "id": 1,
            "slug": "hades",
            "titulo": "Hades",
            "generos": ["Action", "Role-playing (RPG)"],
            "estilos": ["Fantasy"],
            "narrativa": 4,
            "exploracao": 2,
            "dificuldade": 2,
            "modos": ["Single player"],
            "plataformas": ["PC"],
        }

    def test_perfect_match_has_full_score_and_coverage(self) -> None:
        result = score_game(self.preferences, self.game)

        self.assertEqual(result.score, 100)
        self.assertEqual(result.coverage, 100)
        self.assertTrue(any("Gêneros" in item for item in result.justifications))
        self.assertTrue(any("100%" in item for item in result.justifications))

    def test_unanswered_preferences_are_not_penalized(self) -> None:
        preferences = {
            "generos": ["Action"],
            "estilos": [],
            "narrativa": None,
            "exploracao": None,
            "dificuldade": None,
            "modos": [],
            "plataformas": [],
        }
        game = {"titulo": "Jogo", "generos": ["Action"]}

        result = score_game(preferences, game)

        self.assertEqual(result.score, 100)
        self.assertEqual(result.coverage, 100)

    def test_unknown_metadata_reduces_coverage_without_zero_score(self) -> None:
        preferences = {
            "generos": ["Action"],
            "estilos": ["Fantasy"],
            "narrativa": 4,
            "exploracao": 3,
            "dificuldade": 2,
            "modos": ["Single-player"],
            "plataformas": [],
        }
        game = {
            "titulo": "Jogo",
            "generos": ["Action"],
        }

        result = score_game(preferences, game)

        self.assertIsNone(result.score)
        self.assertEqual(result.coverage, 50)
        self.assertLess(result.coverage, MINIMUM_DATA_COVERAGE)
        self.assertTrue(
            any("Dados insuficientes" in item for item in result.justifications)
        )

    def test_exact_70_percent_coverage_allows_a_score(self) -> None:
        preferences = {
            "generos": ["Action"],
            "estilos": ["Fantasy"],
            "narrativa": 4,
            "exploracao": 3,
            "dificuldade": 2,
            "modos": ["Single-player"],
            "plataformas": [],
        }
        game = {
            "titulo": "Jogo",
            "generos": ["Action"],
            "modos": ["Single player"],
        }

        result = score_game(preferences, game)

        self.assertEqual(result.coverage, 70)
        self.assertIsNotNone(result.score)

    def test_platform_filter_requires_known_supported_platform(self) -> None:
        preferences = {
            "generos": ["Action"],
            "estilos": [],
            "narrativa": None,
            "exploracao": None,
            "dificuldade": None,
            "modos": [],
            "plataformas": ["Nintendo Switch"],
        }
        games = [
            {**self.game, "plataformas": ["PC"]},
            {**self.game, "slug": "unknown", "titulo": "Unknown", "plataformas": None},
            {**self.game, "slug": "switch", "titulo": "Switch", "plataformas": ["Nintendo Switch"]},
        ]

        results = recommend_games(preferences, games)

        self.assertEqual([result.game["slug"] for result in results], ["switch"])

    def test_ranking_is_deterministic_for_equal_scores(self) -> None:
        games = [
            {**self.game, "slug": "zulu", "titulo": "Zulu"},
            {**self.game, "slug": "alpha", "titulo": "Alpha"},
            {**self.game, "slug": "bravo", "titulo": "Bravo"},
        ]

        first = recommend_games(self.preferences, games)
        second = recommend_games(self.preferences, list(reversed(games)))

        self.assertEqual(
            [result.game["slug"] for result in first],
            ["alpha", "bravo", "zulu"],
        )
        self.assertEqual(
            [result.game["slug"] for result in first],
            [result.game["slug"] for result in second],
        )

    def test_invalid_preferences_and_bool_levels_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_preferences({"generos": "Ação"})
        with self.assertRaises(ValueError):
            normalize_preferences({"narrativa": True})

if __name__ == "__main__":
    unittest.main()
