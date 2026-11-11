from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


MINIMUM_DATA_COVERAGE = 70
PREFERENCE_WEIGHTS = {
    "generos": 50,
    "estilos": 30,
    "modos": 20,
}
CATEGORY_FIELDS = ("generos", "estilos", "modos", "plataformas")

@dataclass(frozen=True)
class CompatibilityResult:
    game: dict[str, Any]
    score: int | None
    coverage: int
    justifications: tuple[str, ...]


def default_preferences() -> dict[str, Any]:
    return {
        "generos": [],
        "estilos": [],
        "narrativa": None,
        "exploracao": None,
        "dificuldade": None,
        "modos": [],
        "plataformas": [],
    }


def normalize_preferences(
    preferences: Mapping[str, Any] | None,
    vocabulary: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    if preferences is None:
        return default_preferences()
    if not isinstance(preferences, Mapping):
        raise ValueError("As preferências devem ser um objeto.")

    normalized = default_preferences()
    for field in CATEGORY_FIELDS:
        values = preferences.get(field, [])
        if not isinstance(values, list):
            raise ValueError(f"A preferência '{field}' deve ser uma lista.")
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError(f"A preferência '{field}' contém um valor inválido.")
        unique_values = list(dict.fromkeys(value.strip() for value in values))
        if vocabulary is not None:
            allowed_values = vocabulary.get(field)
            if not isinstance(allowed_values, Sequence) or isinstance(
                allowed_values, str
            ):
                raise ValueError(f"O catálogo não definiu as opções de '{field}'.")
            allowed = set(allowed_values)
            if any(value not in allowed for value in unique_values):
                raise ValueError(f"A preferência '{field}' não existe no catálogo.")
        normalized[field] = unique_values

    for field, minimum, maximum in (
        ("narrativa", 1, 5),
        ("exploracao", 1, 5),
        ("dificuldade", 0, 3),
    ):
        value = preferences.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not minimum <= value <= maximum
        ):
            raise ValueError(f"A preferência '{field}' está fora dos limites.")
        normalized[field] = value
    return normalized


def _known_category_values(game: Mapping[str, Any], field: str) -> list[str] | None:
    values = game.get(field)
    if not isinstance(values, list) or not values:
        return None
    if any(not isinstance(value, str) or not value.strip() for value in values):
        return None
    return list(dict.fromkeys(value.strip() for value in values))


def _rounded_percent(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def score_game(
    preferences: Mapping[str, Any],
    game: Mapping[str, Any],
) -> CompatibilityResult:
    normalized_preferences = normalize_preferences(preferences)
    if not isinstance(game, Mapping):
        raise ValueError("Os metadados do jogo devem ser um objeto.")

    title = game.get("titulo")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("O jogo precisa ter um título.")

    if normalized_preferences["plataformas"]:
        game_platforms = _known_category_values(game, "plataformas")
        if game_platforms is None or not set(
            normalized_preferences["plataformas"]
        ).intersection(game_platforms):
            return CompatibilityResult(game=dict(game), score=None, coverage=0, justifications=())

    answered_weight = sum(
        weight
        for field, weight in PREFERENCE_WEIGHTS.items()
        if (
            bool(normalized_preferences[field])
            if field in {"generos", "estilos", "modos"}
            else normalized_preferences[field] is not None
        )
    )
    if answered_weight == 0:
        return CompatibilityResult(
            game=dict(game),
            score=None,
            coverage=0,
            justifications=("Informe ao menos uma preferência para calcular a compatibilidade.",),
        )

    weighted_score = Decimal(0)
    known_weight = 0
    explanations: list[str] = []
    category_labels = {
        "generos": "Gêneros",
        "estilos": "Temas",
        "modos": "Modos de jogo",
    }
    for field in ("generos", "estilos", "modos"):
        preferred = normalized_preferences[field]
        if not preferred:
            continue
        game_values = _known_category_values(game, field)
        if game_values is None:
            continue
        matches = [value for value in preferred if value in game_values]
        criterion_score = Decimal(len(matches)) * 100 / Decimal(len(preferred))
        weight = PREFERENCE_WEIGHTS[field]
        weighted_score += criterion_score * weight
        known_weight += weight
        if matches:
            explanations.append(
                f"{category_labels[field]}: {len(matches)} de {len(preferred)} preferido(s) combinam."
            )
        else:
            explanations.append(
                f"{category_labels[field]}: nenhum valor preferido coincide."
            )

    if known_weight == 0:
        return CompatibilityResult(
            game=dict(game),
            score=None,
            coverage=0,
            justifications=("Ainda não há metadados conhecidos para suas preferências.",),
        )

    coverage = _rounded_percent(
        Decimal(known_weight) * 100 / Decimal(answered_weight)
    )
    explanations.append(
        f"Cobertura dos critérios avaliados: {coverage}% "
        f"({known_weight} de {answered_weight} pontos de peso)."
    )
    if coverage < MINIMUM_DATA_COVERAGE:
        explanations.insert(
            0,
            "Dados insuficientes para calcular uma compatibilidade confiável.",
        )
        return CompatibilityResult(
            game=dict(game),
            score=None,
            coverage=coverage,
            justifications=tuple(explanations),
        )

    score = _rounded_percent(weighted_score / Decimal(known_weight))
    return CompatibilityResult(
        game=dict(game),
        score=score,
        coverage=coverage,
        justifications=tuple(explanations),
    )


def recommend_games(
    preferences: Mapping[str, Any],
    games: Sequence[Mapping[str, Any]],
) -> list[CompatibilityResult]:
    normalized_preferences = normalize_preferences(preferences)
    results = []
    for game in games:
        if not isinstance(game, Mapping):
            raise ValueError("O catálogo contém um jogo inválido.")
        if normalized_preferences["plataformas"]:
            platforms = _known_category_values(game, "plataformas")
            if platforms is None or not set(
                normalized_preferences["plataformas"]
            ).intersection(platforms):
                continue
        results.append(score_game(normalized_preferences, game))
    return sorted(
        results,
        key=lambda result: (
            result.score is None,
            -(result.score or 0),
            str(result.game.get("titulo", "")).strip().casefold(),
            str(result.game.get("slug", result.game.get("id", ""))).casefold(),
        ),
    )
