from __future__ import annotations

import unittest
from unittest.mock import Mock

import requests

from ggreviews.auth_client import (
    AuthAPI,
    AuthAPIError,
    email_validation_error,
    password_policy_error,
)
from ggreviews.config import ConfigurationError, load_auth_config, validate_api_base_url


class AuthClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = Mock()
        self.api = AuthAPI(
            "https://example.xano.io/api:ZnpRG7wg", session=self.session
        )

    def response(self, status_code: int, payload: object) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.ok = 200 <= status_code < 300
        response.json.return_value = payload
        return response

    def test_signup_normalizes_email_and_returns_session(self) -> None:
        self.session.request.return_value = self.response(
            200, {"authToken": "secret-token", "user_id": 7}
        )

        result = self.api.signup(" May ", " MAY@EXAMPLE.COM ", "Password1")

        self.assertEqual(result.token, "secret-token")
        request = self.session.request.call_args.kwargs
        self.assertEqual(request["json"]["email"], "may@example.com")
        self.assertEqual(request["timeout"], 10)

    def test_login_uses_generic_invalid_credentials_message(self) -> None:
        self.session.request.return_value = self.response(
            401, {"error": "account exists; password is wrong"}
        )

        with self.assertRaises(AuthAPIError) as raised:
            self.api.login("user@example.com", "wrong")

        self.assertEqual(raised.exception.code, "invalid_credentials")
        self.assertEqual(raised.exception.message, "E-mail ou senha inválidos.")
        self.assertNotIn("account exists", raised.exception.message)

    def test_current_user_sends_bearer_token(self) -> None:
        self.session.request.return_value = self.response(
            200, {"id": 7, "name": "May", "email": "may@example.com"}
        )

        self.api.current_user("secret-token")

        request = self.session.request.call_args.kwargs
        self.assertEqual(request["headers"]["Authorization"], "Bearer secret-token")

    def test_create_review_sends_authenticated_review_fields(self) -> None:
        self.session.request.return_value = self.response(
            200, {"id": 12, "nota": 4, "comentario": "Ótimo jogo"}
        )

        result = self.api.create_review(
            "secret-token",
            game_name="  God of War  ",
            rating=4,
            review_text="  Ótimo jogo  ",
        )

        request = self.session.request.call_args
        self.assertEqual(
            request.args[:2],
            ("POST", "https://example.xano.io/api:ZnpRG7wg/avalia_es"),
        )
        self.assertEqual(
            request.kwargs["headers"]["Authorization"], "Bearer secret-token"
        )
        self.assertEqual(
            request.kwargs["json"],
            {
                "nome_jogo": "God of War",
                "nota": 4,
                "comentario": "Ótimo jogo",
            },
        )
        self.assertEqual(result["id"], 12)

    def test_game_reviews_uses_game_name_as_query_parameter(self) -> None:
        self.session.request.return_value = self.response(
            200,
            {
                "avaliacoes": [
                    {
                        "nota": 5,
                        "comentario": "Excelente",
                        "_user": {"name": "May"},
                    }
                ]
            },
        )

        result = self.api.game_reviews("secret-token", "God of War")

        request = self.session.request.call_args
        self.assertEqual(request.args[:2], (
            "GET",
            "https://example.xano.io/api:ZnpRG7wg/avaliacoes/by-game",
        ))
        self.assertEqual(request.kwargs["params"], {"nome_jogo": "God of War"})
        self.assertEqual(result[0]["_user"]["name"], "May")

    def test_game_reviews_reports_http_status_when_endpoint_fails(self) -> None:
        self.session.request.return_value = self.response(500, {"message": "failed"})

        with self.assertRaises(AuthAPIError) as raised:
            self.api.game_reviews("secret-token", "God of War")

        self.assertEqual(raised.exception.code, "reviews_unavailable")
        self.assertIn("HTTP 500", raised.exception.message)

    def test_game_reviews_reports_authorization_failure(self) -> None:
        self.session.request.return_value = self.response(401, {"message": "denied"})

        with self.assertRaises(AuthAPIError) as raised:
            self.api.game_reviews("secret-token", "God of War")

        self.assertEqual(raised.exception.code, "reviews_unauthorized")
        self.assertIn("HTTP 401", raised.exception.message)

    def test_game_reviews_surfaces_xano_validation_message(self) -> None:
        self.session.request.return_value = self.response(
            400, {"message": "Missing required input: nome_jogo"}
        )

        with self.assertRaises(AuthAPIError) as raised:
            self.api.game_reviews("secret-token", "God of War")

        self.assertIn("HTTP 400", raised.exception.message)
        self.assertIn("nome_jogo", raised.exception.message)

    def test_my_reviews_uses_authenticated_endpoint(self) -> None:
        self.session.request.return_value = self.response(
            200,
            {
                "avaliacoes": [
                    {
                        "nome_jogo": "God of War",
                        "nota": 4,
                        "comentario": "Excelente",
                    }
                ]
            },
        )

        reviews = self.api.my_reviews("secret-token")

        request = self.session.request.call_args
        self.assertEqual(
            request.args[:2],
            ("GET", "https://example.xano.io/api:ZnpRG7wg/avaliacoes/minhas"),
        )
        self.assertTrue(request.kwargs["headers"]["Authorization"])
        self.assertEqual(reviews[0]["nome_jogo"], "God of War")

    def test_profile_photo_uses_multipart_upload(self) -> None:
        self.session.request.return_value = self.response(
            200,
            {"id": 7, "name": "May", "img_perfil": {"path": "/vault/profile.png"}},
        )

        result = self.api.update_profile_photo(
            "secret-token",
            file_name="profile.png",
            content=b"image-bytes",
            content_type="image/png",
        )

        request = self.session.request.call_args
        self.assertEqual(request.args[:2], (
            "POST",
            "https://example.xano.io/api:ZnpRG7wg/profile/photo",
        ))
        self.assertEqual(
            request.kwargs["files"]["img_perfil"],
            ("profile.png", b"image-bytes", "image/png"),
        )
        self.assertNotIn("json", request.kwargs)
        self.assertNotIn("Content-Type", request.kwargs["headers"])
        self.assertEqual(
            self.api.public_file_url("/vault/profile.png"),
            "https://example.xano.io/vault/profile.png",
        )
        self.assertEqual(result["name"], "May")

    def test_expired_session_has_distinct_code(self) -> None:
        self.session.request.return_value = self.response(401, {"error": "expired"})

        with self.assertRaises(AuthAPIError) as raised:
            self.api.current_user("secret-token")

        self.assertEqual(raised.exception.code, "unauthenticated")
        self.assertNotIn("expired", raised.exception.message)

    def test_reset_request_uses_post_body(self) -> None:
        self.session.request.return_value = self.response(
            200, {"message": "generic response"}
        )

        self.api.request_password_reset(" USER@example.com ")

        self.session.request.assert_called_once()
        request = self.session.request.call_args
        self.assertEqual(request.args[:2], ("POST", "https://example.xano.io/api:ZnpRG7wg/reset/request-reset-link"))
        self.assertEqual(request.kwargs["json"], {"email": "user@example.com"})
        self.assertNotIn("user@example.com", request.args[1])

    def test_complete_password_reset_sends_one_time_link_fields(self) -> None:
        self.session.request.return_value = self.response(
            200, {"message": "Password updated."}
        )

        self.api.complete_password_reset(
            "one-time-token", "USER@example.com", "Password1", "Password1"
        )

        request = self.session.request.call_args.kwargs
        self.assertEqual(request["json"]["email"], "user@example.com")
        self.assertEqual(request["json"]["magic_token"], "one-time-token")
        reset_url = self.session.request.call_args.args[1]
        self.assertEqual(reset_url.split("/")[-1], "complete")

    def test_timeout_does_not_surface_transport_details(self) -> None:
        self.session.request.side_effect = requests.Timeout("token=secret-token")

        with self.assertRaises(AuthAPIError) as raised:
            self.api.login("user@example.com", "Password1")

        self.assertEqual(raised.exception.code, "timeout")
        self.assertNotIn("secret-token", raised.exception.message)

    def test_password_policy(self) -> None:
        self.assertIsNone(password_policy_error("Password1"))
        self.assertIsNotNone(password_policy_error("short1"))
        self.assertIsNotNone(password_policy_error("password"))
        self.assertIsNotNone(password_policy_error("12345678"))

    def test_email_validation(self) -> None:
        self.assertIsNone(email_validation_error("user@example.com"))
        self.assertIsNotNone(email_validation_error("not-an-email"))
        self.assertIsNotNone(email_validation_error(""))


class ConfigTests(unittest.TestCase):
    def test_environment_overrides_streamlit_secrets(self) -> None:
        config = load_auth_config(
            secrets={"XANO_API_BASE_URL": "https://secrets.xano.io/api:Group"},
            environ={"XANO_API_BASE_URL": "https://env.xano.io/api:Group"},
        )

        self.assertEqual(config.api_base_url, "https://env.xano.io/api:Group")

    def test_config_can_be_loaded_from_streamlit_secrets(self) -> None:
        config = load_auth_config(
            secrets={"XANO_API_BASE_URL": "https://secrets.xano.io/api:Group"},
            environ={},
        )

        self.assertEqual(config.api_base_url, "https://secrets.xano.io/api:Group")

    def test_missing_api_url_is_an_explicit_error(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_auth_config(secrets={}, environ={})

    def test_rejects_insecure_remote_api_url(self) -> None:
        with self.assertRaises(ConfigurationError):
            validate_api_base_url("http://example.xano.io/api:Group")

    def test_accepts_local_http_for_development(self) -> None:
        self.assertEqual(
            validate_api_base_url("http://localhost:9000/api:Group"),
            "http://localhost:9000/api:Group",
        )


if __name__ == "__main__":
    unittest.main()
