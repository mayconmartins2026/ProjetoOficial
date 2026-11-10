from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import unquote, urlencode

import requests


CHEAPSHARK_API_BASE = "https://www.cheapshark.com/api/1.0"
EXCHANGE_RATE_URL = "https://api.frankfurter.app/latest"
REQUEST_HEADERS = {"User-Agent": "GGReviews/1.0"}


def _get_json(url: str, *, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(
        url,
        params=params,
        headers=REQUEST_HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as error:
        raise ValueError("A API retornou uma resposta JSON inválida.") from error


def _parse_price(value: Any) -> Decimal | None:
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        return None
    try:
        price = Decimal(str(value))
    except InvalidOperation:
        return None
    return price if price.is_finite() and price >= 0 else None


def search_games(title: str) -> list[dict[str, Any]]:
    query = title.strip()
    if not query:
        return []

    payload = _get_json(
        f"{CHEAPSHARK_API_BASE}/games",
        params={"title": query},
    )
    if not isinstance(payload, list):
        raise ValueError("A CheapShark não retornou uma lista de jogos válida.")

    games = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        game_id = item.get("gameID")
        name = item.get("external")
        if (
            not isinstance(game_id, str)
            or not game_id.isdigit()
            or not isinstance(name, str)
            or not name.strip()
        ):
            continue

        cover = item.get("thumb")
        cheapest_deal_id = item.get("cheapestDealID")
        games.append(
            {
                "id": game_id,
                "name": name.strip(),
                "background_image": (
                    cover
                    if isinstance(cover, str) and cover.startswith("https://")
                    else None
                ),
                "cheapest": _parse_price(item.get("cheapest")),
                "cheapest_deal_id": (
                    cheapest_deal_id
                    if isinstance(cheapest_deal_id, str) and cheapest_deal_id
                    else None
                ),
            }
        )
    return games


def fetch_promotions() -> list[dict[str, Any]]:
    payload = _get_json(
        f"{CHEAPSHARK_API_BASE}/deals",
        params={
            "onSale": 1,
            "pageSize": 60,
            "sortBy": "Savings",
            "desc": 1,
        },
    )
    if not isinstance(payload, list):
        raise ValueError("A CheapShark não retornou uma lista de ofertas válida.")

    promotions = []
    for item in payload:
        if not isinstance(item, dict) or item.get("isOnSale") != "1":
            continue
        title = item.get("title")
        deal_id = item.get("dealID")
        store_id = item.get("storeID")
        sale_price = _parse_price(item.get("salePrice"))
        normal_price = _parse_price(item.get("normalPrice"))
        if (
            not isinstance(title, str)
            or not title.strip()
            or not isinstance(deal_id, str)
            or not deal_id
            or not isinstance(store_id, str)
            or not store_id.isdigit()
            or sale_price is None
            or normal_price is None
            or normal_price == 0
            or sale_price > normal_price
        ):
            continue

        savings = (normal_price - sale_price) / normal_price * 100
        cover = item.get("thumb")
        promotions.append(
            {
                "title": title.strip(),
                "deal_id": deal_id,
                "store_id": store_id,
                "sale_price": sale_price,
                "normal_price": normal_price,
                "savings": savings,
                "thumb": (
                    cover
                    if isinstance(cover, str) and cover.startswith("https://")
                    else None
                ),
            }
        )
    return promotions


def fetch_store_names() -> dict[str, str]:
    payload = _get_json(f"{CHEAPSHARK_API_BASE}/stores")
    if not isinstance(payload, list):
        raise ValueError("A CheapShark não retornou uma lista de lojas válida.")

    stores = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        store_id = item.get("storeID")
        store_name = item.get("storeName")
        if (
            isinstance(store_id, str)
            and store_id.isdigit()
            and isinstance(store_name, str)
            and store_name.strip()
        ):
            stores[store_id] = store_name.strip()
    return stores


def fetch_usd_to_brl_rate() -> tuple[Decimal, date]:
    payload = _get_json(
        EXCHANGE_RATE_URL,
        params={"from": "USD", "to": "BRL"},
    )
    rates = payload.get("rates") if isinstance(payload, dict) else None
    rate = _parse_price(rates.get("BRL")) if isinstance(rates, dict) else None
    rate_date = payload.get("date") if isinstance(payload, dict) else None
    if rate is None or rate <= 0 or not isinstance(rate_date, str):
        raise ValueError("A cotação USD/BRL retornada é inválida.")
    try:
        parsed_date = date.fromisoformat(rate_date)
    except ValueError as error:
        raise ValueError("A data da cotação USD/BRL é inválida.") from error
    return rate, parsed_date


def promotion_url(deal_id: str) -> str:
    return (
        "https://www.cheapshark.com/redirect?"
        f"{urlencode({'dealID': unquote(deal_id)})}"
    )
