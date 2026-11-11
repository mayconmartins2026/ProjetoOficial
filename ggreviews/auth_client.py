from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

from ggreviews.config import validate_api_base_url
from ggreviews.game_compatibility import CATEGORY_FIELDS, normalize_preferences


class AuthAPIError(Exception):
    def __init__(self, message: str, *, code: str = "api_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(frozen=True)
class AuthSession:
    token: str
    user_id: int | str


@dataclass(frozen=True)
class GameRatingAverage:
    average: Decimal
    total: int


class AuthAPI:
    def __init__(
        self,
        api_base_url: str,
        *,
        timeout: float = 10,
        session: requests.Session | None = None,
    ) -> None:
        self._api_base_url = validate_api_base_url(api_base_url)
        self._timeout = timeout
        self._session = session or requests.Session()

    def signup(self, name: str, email: str, password: str) -> AuthSession:
        response = self._request(
            "POST",
            "auth/signup",
            payload={
                "name": name.strip(),
                "email": email.strip().lower(),
                "password": password.strip(),
            },
            failure_message="Não foi possível criar a conta. Confira os dados e tente novamente.",
        )
        return self._auth_session(response)

    def login(self, email: str, password: str) -> AuthSession:
        response = self._request(
            "POST",
            "auth/login",
            payload={"email": email.strip().lower(), "password": password.strip()},
            failure_message="Não foi possível entrar agora. Tente novamente.",
        )
        return self._auth_session(response)

    def current_user(self, token: str) -> dict[str, Any]:
        response = self._request(
            "GET",
            "auth/me",
            token=token,
            failure_message="Não foi possível validar sua sessão agora.",
        )
        return response

    def create_review(
        self,
        token: str,
        *,
        game_name: str,
        rating: int,
        review_text: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "avalia_es",
            payload={
                "nome_jogo": game_name.strip(),
                "nota": rating,
                "comentario": review_text.strip(),
            },
            token=token,
            failure_message="Não foi possível enviar sua avaliação. Tente novamente.",
        )

    def game_reviews(self, token: str, game_name: str) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "avaliacoes/by-game",
            params={"nome_jogo": game_name.strip()},
            token=token,
            failure_message="Não foi possível carregar os comentários deste jogo.",
        )
        return self._review_list(response)

    def game_rating_averages(
        self, token: str, game_names: list[str]
    ) -> dict[str, GameRatingAverage]:
        normalized_names = list(
            dict.fromkeys(name.strip() for name in game_names if name.strip())
        )
        if not normalized_names:
            return {}

        response = self._request(
            "POST",
            "avaliacoes/medias",
            payload={"nomes_jogo": normalized_names},
            token=token,
            failure_message="Não foi possível carregar as médias das avaliações.",
        )
        averages = response.get("medias")
        if not isinstance(averages, list):
            raise AuthAPIError(
                "O serviço retornou uma lista de médias inválida.",
                code="rating_averages_invalid",
            )

        result: dict[str, GameRatingAverage] = {}
        for item in averages:
            if not isinstance(item, dict):
                raise AuthAPIError(
                    "O serviço retornou uma média de jogo inválida.",
                    code="rating_averages_invalid",
                )
            game_name = item.get("nome_jogo")
            raw_average = item.get("media")
            total = item.get("total")
            if (
                not isinstance(game_name, str)
                or not game_name.strip()
                or isinstance(raw_average, bool)
                or not isinstance(raw_average, (int, float, str))
                or isinstance(total, bool)
                or not isinstance(total, int)
                or total <= 0
            ):
                raise AuthAPIError(
                    "O serviço retornou uma média de jogo inválida.",
                    code="rating_averages_invalid",
                )
            try:
                average = Decimal(str(raw_average))
            except InvalidOperation as error:
                raise AuthAPIError(
                    "O serviço retornou uma média de jogo inválida.",
                    code="rating_averages_invalid",
                ) from error
            if not average.is_finite() or not Decimal("1") <= average <= Decimal("5"):
                raise AuthAPIError(
                    "O serviço retornou uma média fora da escala de 1 a 5.",
                    code="rating_averages_invalid",
                )
            result[game_name.strip().casefold()] = GameRatingAverage(
                average=average,
                total=total,
            )
        return result

    def my_reviews(self, token: str) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "avaliacoes/minhas",
            token=token,
            failure_message="Não foi possível carregar suas avaliações.",
        )
        return self._review_list(response)

    def compatibility_preferences(self, token: str) -> dict[str, Any]:
        response = self._request(
            "GET",
            "compatibilidade/preferencias",
            token=token,
            failure_message="Não foi possível carregar suas preferências de jogos.",
        )
        if "preferencias" not in response:
            raise AuthAPIError(
                "O serviço não retornou o perfil de compatibilidade.",
                code="compatibility_preferences_invalid",
            )
        preferences = response.get("preferencias")
        if preferences is None:
            return normalize_preferences(None)
        try:
            return normalize_preferences(preferences)
        except ValueError as error:
            raise AuthAPIError(
                "O serviço retornou preferências de compatibilidade inválidas.",
                code="compatibility_preferences_invalid",
            ) from error

    def save_compatibility_preferences(
        self, token: str, preferences: Mapping[str, Any]
    ) -> dict[str, Any]:
        try:
            normalized = normalize_preferences(preferences)
        except ValueError as error:
            raise AuthAPIError(
                "As preferências informadas são inválidas.",
                code="compatibility_preferences_invalid",
            ) from error
        response = self._request(
            "PUT",
            "compatibilidade/preferencias",
            payload=normalized,
            token=token,
            failure_message="Não foi possível salvar suas preferências de jogos.",
        )
        saved = response.get("preferencias")
        if not isinstance(saved, dict):
            raise AuthAPIError(
                "O serviço não confirmou o salvamento das preferências.",
                code="compatibility_preferences_invalid",
            )
        try:
            return normalize_preferences(saved)
        except ValueError as error:
            raise AuthAPIError(
                "O serviço confirmou uma resposta inválida ao salvar suas preferências.",
                code="compatibility_preferences_invalid",
            ) from error

    def compatibility_catalog(self, token: str) -> dict[str, Any]:
        page_size = 100
        maximum_pages = 20
        games: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        vocabulary: dict[str, list[str]] | None = None

        for page in range(1, maximum_pages + 2):
            response = self._request(
                "GET",
                "compatibilidade/catalogo",
                params={"page": page, "per_page": page_size},
                token=token,
                failure_message="Não foi possível carregar o catálogo de compatibilidade.",
            )
            raw_games = response.get("jogos")
            if isinstance(raw_games, dict):
                raw_games = (
                    raw_games.get("items")
                    or raw_games.get("data")
                    or raw_games.get("results")
                )
            if not isinstance(raw_games, list):
                raise AuthAPIError(
                    "O serviço retornou uma página de catálogo inválida.",
                    code="compatibility_catalog_invalid",
                )
            if page > maximum_pages:
                if raw_games:
                    raise AuthAPIError(
                        "O catálogo excede o limite de páginas permitido.",
                        code="compatibility_catalog_too_large",
                    )
                break

            page_vocabulary = self._compatibility_vocabulary(
                response.get("vocabulario")
            )
            if vocabulary is None:
                vocabulary = page_vocabulary
            elif vocabulary != page_vocabulary:
                raise AuthAPIError(
                    "O vocabulário do catálogo mudou durante a paginação.",
                    code="compatibility_catalog_invalid",
                )

            for game in raw_games:
                normalized_game = self._compatibility_catalog_game(game)
                game_id = str(normalized_game.get("slug") or normalized_game["id"])
                if game_id in seen_ids:
                    raise AuthAPIError(
                        "O catálogo retornou um jogo duplicado.",
                        code="compatibility_catalog_invalid",
                    )
                seen_ids.add(game_id)
                games.append(normalized_game)

            if len(raw_games) < page_size:
                break

        if vocabulary is None:
            raise AuthAPIError(
                "O serviço não retornou o vocabulário do catálogo.",
                code="compatibility_catalog_invalid",
            )
        return {"jogos": games, "vocabulario": vocabulary}

    @staticmethod
    def _compatibility_vocabulary(value: Any) -> dict[str, list[str]]:
        if not isinstance(value, dict):
            raise AuthAPIError(
                "O serviço retornou um vocabulário de catálogo inválido.",
                code="compatibility_catalog_invalid",
            )
        result: dict[str, list[str]] = {}
        for field in CATEGORY_FIELDS:
            values = value.get(field)
            if (
                not isinstance(values, list)
                or any(not isinstance(item, str) or not item.strip() for item in values)
            ):
                raise AuthAPIError(
                    "O serviço retornou opções de catálogo inválidas.",
                    code="compatibility_catalog_invalid",
                )
            result[field] = list(dict.fromkeys(item.strip() for item in values))
        return result

    @staticmethod
    def _compatibility_catalog_game(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise AuthAPIError(
                "O catálogo contém um jogo inválido.",
                code="compatibility_catalog_invalid",
            )
        game_id = value.get("id")
        slug = value.get("slug")
        title = value.get("titulo")
        description = value.get("descricao")
        source_url = value.get("fonte_url")
        if (
            isinstance(game_id, bool)
            or not isinstance(game_id, (int, str))
            or not str(game_id).strip()
            or not isinstance(slug, str)
            or not slug.strip()
            or not isinstance(title, str)
            or not title.strip()
            or not isinstance(description, str)
            or not description.strip()
            or not isinstance(source_url, str)
            or not source_url.startswith("https://")
        ):
            raise AuthAPIError(
                "O catálogo contém um jogo sem identidade, descrição ou fonte válida.",
                code="compatibility_catalog_invalid",
            )
        game = dict(value)
        for field in CATEGORY_FIELDS:
            items = value.get(field)
            if items is not None and (
                not isinstance(items, list)
                or any(not isinstance(item, str) or not item.strip() for item in items)
            ):
                raise AuthAPIError(
                    "O catálogo contém atributos de jogo inválidos.",
                    code="compatibility_catalog_invalid",
                )
            game[field] = (
                list(dict.fromkeys(item.strip() for item in items))
                if isinstance(items, list)
                else None
            )
        cheapshark_id = value.get("cheapshark_game_id")
        if cheapshark_id is not None and (
            not isinstance(cheapshark_id, str) or not cheapshark_id.isdigit()
        ):
            raise AuthAPIError(
                "O catálogo contém um identificador CheapShark inválido.",
                code="compatibility_catalog_invalid",
            )
        return game

    @staticmethod
    def _review_list(response: dict[str, Any]) -> list[dict[str, Any]]:
        reviews = response.get("avaliacoes")
        if not isinstance(reviews, list) or any(
            not isinstance(review, dict) for review in reviews
        ):
            raise AuthAPIError(
                "O serviço retornou uma lista de comentários inválida."
            )
        return reviews

    def update_profile_photo(
        self,
        token: str,
        *,
        file_name: str,
        content: bytes,
        content_type: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "profile/photo",
            token=token,
            failure_message="Não foi possível atualizar sua foto de perfil.",
            files={
                "img_perfil": (file_name, content, content_type),
            },
        )

    def public_file_url(self, path: str) -> str:
        if path.startswith(("https://", "http://")):
            return path
        base = urlsplit(self._api_base_url)
        return urlunsplit(
            (base.scheme, base.netloc, "/" + path.lstrip("/"), "", "")
        )

    def request_password_reset(self, email: str) -> None:
        self._request(
            "POST",
            "reset/request-reset-link",
            payload={"email": email.strip().lower()},
            failure_message=(
                "Não foi possível processar a solicitação agora. Tente novamente mais tarde."
            ),
        )

    def complete_password_reset(
        self,
        magic_token: str,
        email: str,
        password: str,
        confirm_password: str,
    ) -> None:
        self._request(
            "POST",
            "reset/complete",
            payload={
                "magic_token": magic_token,
                "email": email.strip().lower(),
                "password": password.strip(),
                "confirm_password": confirm_password.strip(),
            },
            failure_message="Não foi possível redefinir a senha. Tente novamente.",
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
        failure_message: str,
        files: dict[str, tuple[str, bytes, str]] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        service_name = (
            "serviço de compatibilidade"
            if path.startswith("compatibilidade/")
            else "serviço de autenticação"
        )
        if token:
            headers["Authorization"] = "Bearer " + token

        try:
            request_options: dict[str, Any] = {
                "headers": headers,
                "timeout": self._timeout,
            }
            if params is not None:
                request_options["params"] = params
            if files is None:
                request_options["json"] = payload
            else:
                request_options["data"] = payload
                request_options["files"] = files
            response = self._session.request(
                method,
                f"{self._api_base_url}/{path}",
                **request_options,
            )
        except requests.Timeout:
            raise AuthAPIError(
                f"O {service_name} demorou para responder. Tente novamente.",
                code="timeout",
            ) from None
        except requests.RequestException:
            raise AuthAPIError(
                f"Não foi possível conectar ao {service_name}.",
                code="connection_error",
            ) from None

        if response.status_code in (401, 403):
            if path.startswith("compatibilidade/"):
                raise AuthAPIError(
                    f"{failure_message} (HTTP {response.status_code}; "
                    "a API não autorizou a requisição).",
                    code="compatibility_unauthorized",
                )
            if path == "auth/login":
                raise AuthAPIError(
                    "E-mail ou senha inválidos.", code="invalid_credentials"
                )
            if path == "avaliacoes/by-game":
                raise AuthAPIError(
                    f"{failure_message} (HTTP {response.status_code}; "
                    "a API não autorizou a requisição).",
                    code="reviews_unauthorized",
                )
            if path == "avaliacoes/minhas":
                raise AuthAPIError(
                    f"{failure_message} (HTTP {response.status_code}; "
                    "verifique se o endpoint usa a sessão autenticada).",
                    code="my_reviews_unavailable",
                )
            if path == "avaliacoes/medias":
                raise AuthAPIError(
                    f"{failure_message} (HTTP {response.status_code}; "
                    "a API não autorizou a requisição).",
                    code="rating_averages_unauthorized",
                )
            if path == "auth/me":
                raise AuthAPIError(
                    "Sua sessão expirou. Entre novamente.", code="unauthenticated"
                )
            if path == "reset/complete":
                raise AuthAPIError(
                    "Este link é inválido ou expirou. Solicite um novo link.",
                    code="invalid_reset_link",
                )
            raise AuthAPIError(failure_message)

        if not response.ok:
            if path.startswith("compatibilidade/") and response.status_code == 404:
                raise AuthAPIError(
                    f"O endpoint Xano de compatibilidade ({path}) ainda não foi publicado.",
                    code="compatibility_endpoint_missing",
                )
            if path.startswith("compatibilidade/"):
                detail = self._error_message(response)
                detail_suffix = f": {detail}" if detail else ""
                raise AuthAPIError(
                    f"{failure_message} (HTTP {response.status_code}{detail_suffix}).",
                    code="compatibility_unavailable",
                )
            if path == "avalia_es" and response.status_code == 404:
                raise AuthAPIError(
                    "O endpoint de avaliações avalia_es não foi publicado no Xano."
                )
            if path in {
                "avaliacoes/by-game",
                "avaliacoes/minhas",
                "avaliacoes/medias",
            } and response.status_code == 404:
                raise AuthAPIError(
                    f"O endpoint de avaliações ({path}) não foi publicado no Xano."
                )
            if path == "profile/photo" and response.status_code == 404:
                raise AuthAPIError(
                    "O endpoint de foto de perfil não foi publicado no Xano."
                )
            if path == "profile/photo" and response.status_code == 413:
                raise AuthAPIError(
                    "A imagem é muito grande. Envie uma imagem de até 5 MB."
                )
            if path == "profile/photo" and response.status_code == 400:
                raise AuthAPIError(
                    "O Xano não aceitou o arquivo. Confira se o campo multipart "
                    "é img_perfil e se o endpoint recebe um arquivo."
                )
            if path in {
                "avaliacoes/by-game",
                "avaliacoes/minhas",
                "avaliacoes/medias",
            }:
                detail = self._error_message(response)
                detail_suffix = f": {detail}" if detail else ""
                raise AuthAPIError(
                    f"{failure_message} (HTTP {response.status_code}{detail_suffix}).",
                    code="reviews_unavailable",
                )
            raise AuthAPIError(failure_message)

        try:
            data = response.json()
        except ValueError:
            raise AuthAPIError(
                f"O {service_name} retornou uma resposta inválida."
            ) from None

        if not isinstance(data, dict):
            raise AuthAPIError(
                f"O {service_name} retornou uma resposta inválida."
            )
        return data

    @staticmethod
    def _error_message(response: requests.Response) -> str | None:
        try:
            payload = response.json()
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        message = payload.get("message")
        if not isinstance(message, str):
            return None
        message = " ".join(message.split())
        return message[:240] or None

    @staticmethod
    def _auth_session(response: dict[str, Any]) -> AuthSession:
        token = response.get("authToken")
        user_id = response.get("user_id")
        if not isinstance(token, str) or not token or not isinstance(
            user_id, (int, str)
        ):
            raise AuthAPIError(
                "O serviço de autenticação retornou uma resposta inválida."
            )
        return AuthSession(token=token, user_id=user_id)


def password_policy_error(password: str) -> str | None:
    normalized = password.strip()
    if len(normalized) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    if not any(character.isalpha() for character in normalized):
        return "A senha deve conter pelo menos uma letra."
    if not any(character.isdigit() for character in normalized):
        return "A senha deve conter pelo menos um número."
    return None


def email_validation_error(email: str) -> str | None:
    normalized = email.strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        return "Informe um e-mail válido."
    return None
