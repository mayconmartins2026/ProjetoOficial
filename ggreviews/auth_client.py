from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

from ggreviews.config import validate_api_base_url


class AuthAPIError(Exception):
    def __init__(self, message: str, *, code: str = "api_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(frozen=True)
class AuthSession:
    token: str
    user_id: int | str


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

    def my_reviews(self, token: str) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "avaliacoes/minhas",
            token=token,
            failure_message="Não foi possível carregar suas avaliações.",
        )
        return self._review_list(response)

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
                "O serviço de autenticação demorou para responder. Tente novamente.",
                code="timeout",
            ) from None
        except requests.RequestException:
            raise AuthAPIError(
                "Não foi possível conectar ao serviço de autenticação.",
                code="connection_error",
            ) from None

        if response.status_code in (401, 403):
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
            if path == "avalia_es" and response.status_code == 404:
                raise AuthAPIError(
                    "O endpoint de avaliações avalia_es não foi publicado no Xano."
                )
            if path in {"avaliacoes/by-game", "avaliacoes/minhas"} and response.status_code == 404:
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
            if path in {"avaliacoes/by-game", "avaliacoes/minhas"}:
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
                "O serviço de autenticação retornou uma resposta inválida."
            ) from None

        if not isinstance(data, dict):
            raise AuthAPIError(
                "O serviço de autenticação retornou uma resposta inválida."
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
