from __future__ import annotations

import re
import unicodedata
from html.parser import HTMLParser
from typing import Any

import requests


STEAM_STORESEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"
STEAM_REQUEST_HEADERS = {"User-Agent": "GGReviews/1.0"}


class _DescriptionTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.parts.append(text)


def _normalized_game_title(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title.casefold())
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
    for edition_suffix in (" enhanced", " legacy"):
        if normalized.endswith(edition_suffix):
            return normalized[: -len(edition_suffix)].strip()
    return normalized


def _request_json(url: str, *, params: dict[str, Any]) -> Any:
    response = requests.get(
        url,
        params=params,
        headers=STEAM_REQUEST_HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as error:
        raise ValueError("A Steam retornou uma resposta JSON inválida.") from error


def _plain_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parser = _DescriptionTextParser()
    parser.feed(value)
    description = " ".join(parser.parts).strip()
    return description or None


def fetch_brazilian_game_description(game_name: str) -> str | None:
    title = game_name.strip()
    if not title:
        return None

    search_payload = _request_json(
        STEAM_STORESEARCH_URL,
        params={"term": title, "l": "brazilian", "cc": "br"},
    )
    items = search_payload.get("items") if isinstance(search_payload, dict) else None
    if not isinstance(items, list):
        raise ValueError("A Steam retornou uma busca de jogos inválida.")

    normalized_title = _normalized_game_title(title)
    matching_app_id: int | None = None
    for item in items:
        if not isinstance(item, dict):
            continue
        item_name = item.get("name")
        app_id = item.get("id")
        if (
            item.get("type") == "app"
            and isinstance(item_name, str)
            and _normalized_game_title(item_name) == normalized_title
            and isinstance(app_id, int)
            and not isinstance(app_id, bool)
            and app_id > 0
        ):
            matching_app_id = app_id
            break
    if matching_app_id is None:
        return None

    details_payload = _request_json(
        STEAM_APPDETAILS_URL,
        params={
            "appids": matching_app_id,
            "l": "brazilian",
            "cc": "br",
        },
    )
    app_details = (
        details_payload.get(str(matching_app_id))
        if isinstance(details_payload, dict)
        else None
    )
    data = (
        app_details.get("data")
        if isinstance(app_details, dict) and app_details.get("success") is True
        else None
    )
    if not isinstance(data, dict):
        return None

    description = _plain_text(
        data.get("short_description") or data.get("about_the_game")
    )
    return description
