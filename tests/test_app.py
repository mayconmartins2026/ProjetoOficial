from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest


API_URL = "https://example.xano.io/api:ZnpRG7wg"
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def response(status_code: int, payload: dict[str, object]) -> Mock:
    result = Mock()
    result.status_code = status_code
    result.ok = 200 <= status_code < 300
    result.json.return_value = payload
    return result


class AuthenticationAppTests(unittest.TestCase):
    def run_app(self, app: AppTest) -> AppTest:
        with patch.dict(os.environ, {"XANO_API_BASE_URL": API_URL}):
            return app.run()

    def test_authentication_forms_are_available(self) -> None:
        app = self.run_app(AppTest.from_file(str(APP_PATH)))

        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["Entrar", "Criar conta", "Recuperar senha"],
        )
        self.assertEqual(app.exception, [])

    @patch("requests.Session.request")
    def test_invalid_email_is_rejected_before_api_call(self, request: Mock) -> None:
        app = self.run_app(AppTest.from_file(str(APP_PATH)))
        app.text_input[0].set_value("not-an-email")
        app.text_input[1].set_value("Password1")
        self.run_app(app.button[0].click())

        request.assert_not_called()
        self.assertIn("Informe um e-mail válido.", [error.value for error in app.error])

    @patch("requests.Session.request")
    def test_signup_validates_password_and_opens_session(
        self, request: Mock
    ) -> None:
        request.side_effect = [
            response(200, {"authToken": "session-token", "user_id": 7}),
            response(200, {"id": 7, "name": "Jogador", "email": "user@example.com"}),
        ]
        app = self.run_app(AppTest.from_file(str(APP_PATH)))
        app.text_input[2].set_value("Jogador")
        app.text_input[3].set_value("USER@example.com")
        app.text_input[4].set_value("Password1")
        app.text_input[5].set_value("Password1")
        self.run_app(app.button[1].click())

        self.assertEqual(app.exception, [])
        self.assertIn("Bem-vindo, Jogador!", [message.value for message in app.success])
        self.assertEqual(
            request.call_args_list[0].args[1],
            f"{API_URL}/auth/signup",
        )

    @patch("requests.Session.request")
    def test_password_recovery_confirmation_is_generic(self, request: Mock) -> None:
        request.return_value = response(
            200, {"message": "If an account exists, a reset link has been sent."}
        )
        app = self.run_app(AppTest.from_file(str(APP_PATH)))
        app.text_input[6].set_value("user@example.com")
        self.run_app(app.button[2].click())

        self.assertEqual(app.exception, [])
        self.assertIn(
            "Se houver uma conta associada a esse e-mail, você receberá um link de recuperação.",
            [message.value for message in app.success],
        )

    @patch("requests.Session.request")
    def test_reset_link_is_removed_from_url_and_completes_reset(
        self, request: Mock
    ) -> None:
        request.return_value = response(200, {"message": "Password updated."})
        app = AppTest.from_file(str(APP_PATH))
        app.query_params["magic_token"] = "one-time-token"
        app.query_params["email"] = "user@example.com"
        self.run_app(app)

        self.assertEqual(dict(app.query_params), {})
        self.assertEqual([field.label for field in app.text_input], [
            "Nova senha",
            "Confirme a nova senha",
        ])
        app.text_input[0].set_value("Password1")
        app.text_input[1].set_value("Password1")
        self.run_app(app.button[0].click())

        self.assertEqual(app.exception, [])
        self.assertIn("Senha atualizada. Entre com sua nova senha.", [
            message.value for message in app.success
        ])
        self.assertEqual(request.call_args.kwargs["json"]["magic_token"], "one-time-token")

    @patch("requests.Session.request")
    def test_login_validates_session_and_shows_authenticated_view(
        self, request: Mock
    ) -> None:
        request.side_effect = [
            response(200, {"authToken": "session-token", "user_id": 7}),
            response(200, {"id": 7, "name": "Jogador", "email": "user@example.com"}),
        ]
        app = self.run_app(AppTest.from_file(str(APP_PATH)))
        app.text_input[0].set_value("user@example.com")
        app.text_input[1].set_value("Password1")
        self.run_app(app.button[0].click())

        self.assertEqual(app.exception, [])
        self.assertIn("Bem-vindo, Jogador!", [message.value for message in app.success])
        self.assertTrue(any(button.label == "Sair" for button in app.button))

    @patch("requests.Session.request")
    def test_expired_session_is_cleared_and_login_is_shown(
        self, request: Mock
    ) -> None:
        request.return_value = response(401, {"error": "expired"})
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "expired-token"
        self.run_app(app)

        self.assertNotIn("auth_token", app.session_state)
        self.assertIn("Sua sessão expirou. Entre novamente.", [
            warning.value for warning in app.warning
        ])
        self.assertEqual([tab.label for tab in app.tabs], [
            "Entrar",
            "Criar conta",
            "Recuperar senha",
        ])

    @patch("requests.Session.request")
    def test_logout_removes_local_token(self, request: Mock) -> None:
        request.return_value = response(
            200, {"id": 7, "name": "Jogador", "email": "user@example.com"}
        )
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        self.run_app(app)
        self.run_app(app.button[0].click())

        self.assertNotIn("auth_token", app.session_state)
        self.assertEqual(app.exception, [])

    @patch("requests.Session.request")
    def test_selected_game_shows_summary_and_review_form(
        self, request: Mock
    ) -> None:
        request.side_effect = [
            response(200, {"id": 7, "name": "Jogador", "email": "user@example.com"}),
            response(
                200,
                {
                    "avaliacoes": [
                        {
                            "nota": 4,
                            "comentario": "Uma aventura marcante.",
                            "_user": {
                                "name": "May",
                                "img_perfil": {"path": "/vault/may.png"},
                            },
                        }
                    ]
                },
            ),
        ]
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app.session_state["jogo_selecionado"] = {
            "id": 3498,
            "name": "God of War",
        }
        app_module = __import__("app")
        app_module.buscar_detalhes_jogo_rawg.clear()
        app_module._traduzir_para_portugues.clear()
        with patch(
            "requests.get",
            side_effect=[
                response(
                    200,
                    {
                        "name": "God of War",
                        "description_raw": (
                            "Kratos begins a new journey. He travels with his son."
                        ),
                    },
                ),
                response(
                    200,
                    {
                        "responseData": {
                            "translatedText": (
                                "Kratos inicia uma nova jornada. "
                                "Ele viaja com seu filho."
                            )
                        }
                    },
                ),
            ],
        ):
            with patch.dict(os.environ, {"RAWG_API_KEY": "test-key"}):
                self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertIn("Sobre o jogo", [item.value for item in app.subheader])
        self.assertTrue(
            any(
                "Kratos inicia uma nova jornada." in item.value
                for item in app.markdown
            )
        )
        self.assertEqual(app.text_area[0].label, "Comentário")
        self.assertTrue(any(button.label == "Enviar avaliação" for button in app.button))
        self.assertTrue(any("May" in item.value for item in app.markdown))
        self.assertTrue(
            any("Uma aventura marcante." in item.value for item in app.markdown)
        )
        self.assertTrue(
            any(
                image.proto.imgs[0].url.endswith("/vault/may.png")
                for image in app.image
            )
        )
        self.assertFalse(
            any("Dashboard Principal" in item.value for item in app.subheader)
        )

    @patch("requests.Session.request")
    def test_profile_photo_is_shown_before_sidebar_greeting(
        self, request: Mock
    ) -> None:
        request.return_value = response(
            200,
            {
                "id": 7,
                "name": "Maycon Oliveira",
                "email": "user@example.com",
                "img_perfil": {"path": "/vault/maycon.png"},
            },
        )
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"

        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertTrue(
            any(
                image.proto.imgs[0].url.endswith("/vault/maycon.png")
                for image in app.sidebar.image
            )
        )
        self.assertTrue(
            any("Olá, **Maycon Oliveira**!" in item.value for item in app.markdown)
        )

    @patch("requests.Session.request")
    def test_my_reviews_shows_only_authenticated_user_reviews(
        self, request: Mock
    ) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/avaliacoes/minhas"):
                return response(
                    200,
                    {
                        "avaliacoes": [
                            {
                                "created_at": "2026-10-23T04:34:12.382Z",
                                "nome_jogo": "God of War",
                                "nota": 4,
                                "comentario": "Uma aventura marcante.",
                            }
                        ]
                    },
                )
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app_module = __import__("app")
        app_module.buscar_jogos_rawg.clear()
        app_module.buscar_capa_jogo_rawg.clear()

        with patch(
            "requests.get",
            side_effect=[
                response(200, {"results": []}),
                response(
                    200,
                    {
                        "results": [
                            {
                                "name": "God of War",
                                "background_image": "https://images.example/god-of-war.jpg",
                            }
                        ]
                    },
                ),
            ],
        ) as rawg_request:
            with patch.dict(os.environ, {"RAWG_API_KEY": "test-key"}):
                self.run_app(app)
                my_reviews_button = next(
                    button
                    for button in app.sidebar.button
                    if button.label == "📝 Minhas Reviews"
                )
                self.run_app(my_reviews_button.click())

        self.assertEqual(app.exception, [])
        self.assertEqual(app.session_state["pagina"], "minhas_reviews")
        self.assertIn("Minhas Reviews", [item.value for item in app.title])
        self.assertTrue(any("God of War" in item.value for item in app.subheader))
        self.assertTrue(any("Nota: 4 / 5" in item.value for item in app.caption))
        self.assertTrue(
            any("23/10/2026 às 01:34" in item.value for item in app.caption)
        )
        self.assertTrue(
            any("Uma aventura marcante." in item.value for item in app.markdown)
        )
        self.assertTrue(
            any(
                image.proto.imgs[0].url
                == "https://images.example/god-of-war.jpg"
                for image in app.image
            )
        )
        my_reviews_request = next(
            call for call in request.call_args_list
            if call.args[1].endswith("/avaliacoes/minhas")
        )
        self.assertTrue(my_reviews_request.kwargs["headers"]["Authorization"])
        self.assertEqual(rawg_request.call_count, 2)

    @patch("requests.Session.request")
    def test_submitting_evaluation_uses_avaliacoes_table_endpoint(
        self, request: Mock
    ) -> None:
        review_created = False

        def respond(method: str, url: str, **kwargs: object) -> Mock:
            nonlocal review_created
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/avaliacoes/by-game"):
                reviews = []
                if review_created:
                    reviews.append(
                        {
                            "created_at": "2026-10-23T04:34:12.382Z",
                            "nota": 5,
                            "comentario": "Uma aventura marcante.",
                            "_user": {
                                "name": "Jogador",
                                "img_perfil": {"path": "/vault/jogador.png"},
                            },
                        }
                    )
                return response(200, {"avaliacoes": reviews})
            if url.endswith("/avalia_es"):
                review_created = True
                return response(
                    200,
                    {
                        "id": 18,
                        "user_id": 7,
                        "nome_jogo": "God of War",
                        "nota": 5,
                        "comentario": "Uma aventura marcante.",
                    },
                )
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app.session_state["jogo_selecionado"] = {
            "id": 3498,
            "name": "God of War",
        }
        app_module = __import__("app")
        app_module.buscar_detalhes_jogo_rawg.clear()
        app_module._traduzir_para_portugues.clear()
        with patch(
            "requests.get",
            side_effect=[
                response(
                    200,
                    {
                        "description_raw": (
                            "Kratos begins a new journey. He travels with his son."
                        )
                    },
                ),
                response(
                    200,
                    {"responseData": {"translatedText": "Kratos inicia uma jornada."}},
                ),
            ],
        ):
            with patch.dict(os.environ, {"RAWG_API_KEY": "test-key"}):
                self.run_app(app)
                app.text_area[0].set_value("Uma aventura marcante.")
                submit_index = next(
                    index
                    for index, button in enumerate(app.button)
                    if button.label == "Enviar avaliação"
                )
                self.run_app(app.button[submit_index].click())

        evaluation_request = next(
            call for call in request.call_args_list
            if call.args[1].endswith("/avalia_es")
        )
        self.assertEqual(
            evaluation_request.kwargs["json"],
            {
                "nome_jogo": "God of War",
                "nota": 5,
                "comentario": "Uma aventura marcante.",
            },
        )
        self.assertEqual(app.session_state["jogo_selecionado"]["name"], "God of War")
        self.assertTrue(
            any("Comentários da comunidade" in item.value for item in app.subheader)
        )
        self.assertTrue(any("Jogador" in item.value for item in app.markdown))
        self.assertTrue(
            any("23/10/2026 às 01:34" in item.value for item in app.caption)
        )
        self.assertTrue(
            any("Uma aventura marcante." in item.value for item in app.markdown)
        )
        self.assertEqual(app.exception, [])

    def test_review_date_formats_iso_timestamp_and_handles_missing_values(
        self,
    ) -> None:
        app_module = __import__("app")

        self.assertEqual(
            app_module._format_review_date("2026-10-23T04:34:12.382Z"),
            "23/10/2026 às 01:34",
        )
        self.assertEqual(
            app_module._format_review_date(1792730052382),
            "23/10/2026 às 01:34",
        )
        self.assertEqual(
            app_module._format_review_date("2026-10-23"),
            "23/10/2026",
        )
        self.assertEqual(
            app_module._format_review_date(None),
            "Data não disponível",
        )
        self.assertEqual(
            app_module._format_review_date(True),
            "Data não disponível",
        )

    def test_rawg_platforms_are_rendered_with_icons_and_deduplicated(self) -> None:
        app_module = __import__("app")

        self.assertEqual(
            app_module._game_platforms(
                {
                    "platforms": [
                        {"platform": {"name": "PC"}},
                        {"platform": {"name": "PlayStation 5"}},
                        {"platform": {"name": "PC"}},
                        {"platform": {"name": "Xbox Series X|S"}},
                    ]
                }
            ),
            "🖥️ PC · 🎮 PlayStation 5 · 🎮 Xbox Series X|S",
        )

    @patch("requests.Session.request")
    def test_settings_shows_profile_photo_upload(self, request: Mock) -> None:
        request.return_value = response(
            200,
            {
                "id": 7,
                "name": "Jogador",
                "email": "user@example.com",
                "img_perfil": {"path": "/vault/profile.png"},
            },
        )
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app.session_state["pagina"] = "configuracoes"
        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertIn("Configurações", [item.value for item in app.title])
        self.assertEqual(app.file_uploader[0].label, "Escolha uma imagem")
        self.assertTrue(
            any(button.label == "Salvar foto de perfil" for button in app.button)
        )


if __name__ == "__main__":
    unittest.main()
