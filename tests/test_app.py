from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import streamlit as st
from streamlit.testing.v1 import AppTest


API_URL = "https://example.xano.io/api:ZnpRG7wg"
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def response(status_code: int, payload: object) -> Mock:
    result = Mock()
    result.status_code = status_code
    result.ok = 200 <= status_code < 300
    result.json.return_value = payload
    return result


class AuthenticationAppTests(unittest.TestCase):
    def run_app(self, app: AppTest, *, timeout: float = 10) -> AppTest:
        with patch.dict(
            os.environ,
            {
                "XANO_API_BASE_URL": API_URL,
                "TWITCH_CLIENT_ID": "test-client-id",
                "TWITCH_CLIENT_SECRET": "test-client-secret",
            },
        ):
            return app.run(timeout=timeout)

    @patch("app.load_dotenv")
    @patch("requests.post")
    def test_igdb_search_authenticates_with_twitch_and_normalizes_games(
        self, post: Mock, load_dotenv: Mock
    ) -> None:
        import app as app_module

        app_module.buscar_jogos_igdb.clear()
        post.side_effect = [
            response(200, {"access_token": "test-access-token"}),
            response(
                200,
                [
                    {
                        "id": 123,
                        "name": "Hades",
                        "cover": {"image_id": "cover_hades"},
                    }
                ],
            ),
        ]
        with patch.dict(
            os.environ,
            {
                "TWITCH_CLIENT_ID": "test-client-id",
                "TWITCH_CLIENT_SECRET": "test-client-secret",
            },
        ):
            games = app_module.buscar_jogos_igdb(' Hades "II" ')

        load_dotenv.assert_called_once_with(APP_PATH.with_name(".env"))
        self.assertEqual(
            post.call_args_list[0].kwargs["data"],
            {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "grant_type": "client_credentials",
            },
        )
        self.assertEqual(
            post.call_args_list[1].kwargs["headers"],
            {
                "Client-ID": "test-client-id",
                "Authorization": "Bearer test-access-token",
            },
        )
        self.assertIn(
            'search "Hades \\"II\\"";',
            post.call_args_list[1].kwargs["data"],
        )
        self.assertEqual(
            games,
            [
                {
                    "id": 123,
                    "name": "Hades",
                    "cover": {"image_id": "cover_hades"},
                    "background_image": (
                        "https://images.igdb.com/igdb/image/upload/"
                        "t_cover_big/cover_hades.jpg"
                    ),
                }
            ],
        )

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
        self.run_app(app, timeout=10)

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
        app.session_state["pagina"] = "configuracoes"
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
        app.session_state["pagina"] = "configuracoes"
        self.run_app(app)
        logout_button = next(button for button in app.button if button.label == "Sair")
        self.run_app(logout_button.click())

        self.assertNotIn("auth_token", app.session_state)
        self.assertEqual(app.exception, [])

    @patch("requests.Session.request")
    def test_selected_game_shows_cover_description_rating_and_review_form(
        self, request: Mock
    ) -> None:
        request.side_effect = [
            response(200, {"id": 7, "name": "Jogador", "email": "user@example.com"}),
            response(200, {"medias": [{"nome_jogo": "God of War", "media": 4.5, "total": 2}]}),
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
            "id": "3498",
            "name": "God of War",
            "background_image": "https://images.example/god-of-war.jpg",
            "summary": "Kratos and Atreus journey through Norse realms.",
        }
        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertTrue(any("Sobre o jogo" in item.value for item in app.subheader))
        self.assertTrue(any("God of War" in item.value for item in app.title))
        self.assertTrue(
            any(
                "Kratos and Atreus journey through Norse realms." in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                "Nota atual no site: 4,5/5 · 2 avaliação(ões)" in item.value
                for item in app.caption
            )
        )
        self.assertTrue(
            any(
                image.proto.imgs[0].url
                == "https://images.example/god-of-war.jpg"
                for image in app.image
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
    @patch("requests.post")
    def test_my_reviews_shows_only_authenticated_user_reviews(
        self, post: Mock, request: Mock
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
            if url.endswith("/avaliacoes/medias"):
                return response(200, {"medias": []})
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app_module = __import__("app")
        app_module.buscar_capa_jogo_igdb.clear()
        app_module.buscar_jogos_igdb.clear()
        post.side_effect = [
            response(200, {"access_token": "test-access-token"}),
            response(
                200,
                [
                    {
                        "id": 123,
                        "name": "God of War",
                        "cover": {"image_id": "god_of_war"},
                    }
                ],
            ),
        ]

        with patch(
            "requests.get",
            return_value=response(
                200,
                [
                    {
                        "gameID": "236053",
                        "external": "God of War",
                        "thumb": "https://images.example/god-of-war.jpg",
                        "cheapest": "24.99",
                        "cheapestDealID": "deal-id",
                    }
                ],
            ),
        ):
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
                == (
                    "https://images.igdb.com/igdb/image/upload/"
                    "t_cover_big/god_of_war.jpg"
                )
                for image in app.image
            )
        )
        my_reviews_request = next(
            call for call in request.call_args_list
            if call.args[1].endswith("/avaliacoes/minhas")
        )
        self.assertTrue(my_reviews_request.kwargs["headers"]["Authorization"])
        game_requests = [
            call
            for call in post.call_args_list
            if call.args[0].endswith("/games")
        ]
        self.assertEqual(len(game_requests), 1)
        self.assertEqual(
            game_requests[0].kwargs["headers"]["Authorization"],
            "Bearer test-access-token",
        )

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
            if url.endswith("/avaliacoes/medias"):
                return response(
                    200,
                    {
                        "medias": (
                            [{"nome_jogo": "God of War", "media": 5, "total": 1}]
                            if review_created
                            else []
                        )
                    },
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
            "id": "3498",
            "name": "God of War",
        }
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
        self.assertTrue(
            any(
                "Nota atual no site: 5,0/5 · 1 avaliação(ões)" in item.value
                for item in app.caption
            )
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

    @patch("requests.Session.request")
    @patch("requests.get")
    @patch("requests.post")
    def test_game_catalog_uses_igdb(self, post: Mock, get: Mock, request: Mock) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/avaliacoes/medias"):
                return response(
                    200,
                    {"medias": [{"nome_jogo": "Hades", "media": 4.5, "total": 10}]},
                )
            if url.endswith("/avaliacoes/by-game"):
                return response(200, {"avaliacoes": []})
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond

        def get_external(url: str, **kwargs: object) -> Mock:
            if url.endswith("/deals"):
                return response(200, [])
            if url.endswith("/stores"):
                return response(200, [])
            if url == "https://api.frankfurter.app/latest":
                return response(
                    200,
                    {"date": "2026-11-09", "rates": {"BRL": 5}},
                )
            self.fail(f"Unexpected external API request: {url}")

        get.side_effect = get_external
        post.side_effect = [
            response(200, {"access_token": "test-access-token"}),
            response(
                200,
                [{"id": 123, "name": "Hades", "cover": {"image_id": "hades"}}],
            ),
        ]
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        st.cache_data.clear()

        self.run_app(app)
        app.text_input[0].set_value("Hades")
        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertFalse(
            any(metric.label == "Menor preço encontrado" for metric in app.metric)
        )
        evaluation_button = next(
            button for button in app.button if button.label == "Fazer avaliação"
        )
        self.run_app(evaluation_button.click())

        self.assertEqual(app.exception, [])
        self.assertIn("Sua avaliação", [item.value for item in app.subheader])
        self.assertTrue(
            any(
                "Nota atual no site: 4,5/5 · 10 avaliação(ões)" in item.value
                for item in app.caption
            )
        )
        self.assertEqual(app.text_area[0].label, "Comentário")
        self.assertTrue(
            any(
                image.proto.imgs[0].url
                == "https://images.igdb.com/igdb/image/upload/t_cover_big/hades.jpg"
                for image in app.image
            )
        )
        xray_button = next(
            button for button in app.button if button.label == "Não avaliado"
        )
        self.run_app(xray_button.click())

        self.assertEqual(app.exception, [])
        self.assertIn("Raio-X técnico", [item.value for item in app.title])
        self.assertIn("Hades", [item.value for item in app.subheader])
        self.assertEqual(
            [item.value for item in app.caption if "Estado:" in item.value],
            ["Estado: Sem dados ainda"] * 3,
        )
        self.assertTrue(
            any(
                "não significa que ele seja livre de DRM" in item.value
                for item in app.warning
            )
        )
        game_searches = [
            call for call in post.call_args_list if call.args[0].endswith("/games")
        ]
        self.assertEqual(len(game_searches), 1)

    @patch("requests.Session.request")
    def test_xray_page_explains_missing_data_and_methodology(
        self, request: Mock
    ) -> None:
        request.return_value = response(
            200,
            {"id": 7, "name": "Jogador", "email": "user@example.com"},
        )
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app.session_state["pagina"] = "raiox"

        self.run_app(app)
        app.text_input[0].set_value("Elden Ring")
        self.run_app(
            next(
                button for button in app.button if button.label == "Ver Raio-X"
            ).click()
        )

        self.assertEqual(app.exception, [])
        self.assertIn("Elden Ring", [item.value for item in app.subheader])
        self.assertEqual(
            [item.value for item in app.caption if "Estado:" in item.value],
            ["Estado: Sem dados ainda"] * 3,
        )
        self.assertTrue(
            any("Versão/patch: Sem dados" in item.value for item in app.caption)
        )
        self.assertTrue(
            any("em até 90 dias" in item.value for item in app.markdown)
        )

    @patch("requests.Session.request")
    @patch("requests.get")
    def test_promotions_page_shows_cheapshark_prices_in_reais(
        self, get: Mock, request: Mock
    ) -> None:
        def api_response(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {
                        "id": 7,
                        "name": "Jogador",
                        "email": "user@example.com",
                    },
                )
            if url.endswith("/avaliacoes/medias"):
                return response(
                    200,
                    {
                        "medias": [
                            {
                                "nome_jogo": "Jogo em promoção",
                                "media": 4.2,
                                "total": 5,
                            }
                        ]
                    },
                )
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = api_response
        deals_response = response(
            200,
            [
                {
                    "title": "Jogo em promoção",
                    "dealID": "deal-id",
                    "storeID": "1",
                    "salePrice": "4.99",
                    "normalPrice": "9.99",
                    "savings": "50.050050",
                    "isOnSale": "1",
                    "thumb": "https://images.example/game.jpg",
                }
            ],
        )
        rate_response = response(
            200,
            {
                "date": "2026-11-09",
                "rates": {"BRL": 5},
            },
        )
        def external_response(url: str, **kwargs: object) -> Mock:
            if url.endswith("/deals"):
                return deals_response
            if url == "https://api.frankfurter.app/latest":
                return rate_response
            if url.endswith("/stores"):
                return response(
                    200,
                    [{"storeID": "1", "storeName": "Steam", "isActive": 1}],
                )
            self.fail(f"Unexpected external API request: {url}")

        get.side_effect = external_response
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        st.cache_data.clear()

        self.run_app(app)
        promotions_button = next(
            button
            for button in app.sidebar.button
            if button.label == "🏷️ Promoções"
        )
        self.run_app(promotions_button.click())

        self.assertEqual(app.exception, [])
        self.assertEqual(app.session_state["pagina"], "promocoes")
        self.assertIn("Jogos em promoção", [item.value for item in app.title])
        self.assertTrue(
            app.metric,
            (
                [item.value for item in app.error],
                [item.value for item in app.warning],
                [item.value for item in app.info],
            ),
        )
        self.assertEqual(app.metric[0].value, "R$ 24,95")
        self.assertTrue(
            any(
                "Média da comunidade: 4,2/5 · 5 avaliação(ões)" in item.value
                for item in app.caption
            )
        )
        self.assertTrue(
            any("Preço normal: R$ 49,95" in item.value for item in app.caption)
        )
        self.assertTrue(
            any(
                ":material/computer: PC · :material/storefront: Steam" in item.value
                for item in app.caption
            ),
            [item.value for item in app.caption],
        )
        self.assertTrue(
            any(
                image.proto.imgs[0].url == "https://images.example/game.jpg"
                for image in app.image
            )
        )
        deal_request = next(
            call for call in get.call_args_list if call.args[0].endswith("/deals")
        )
        self.assertEqual(
            deal_request.kwargs["params"],
            {
                "onSale": 1,
                "pageSize": 60,
                "sortBy": "Savings",
                "desc": 1,
            },
        )
        self.run_app(
            next(button for button in app.button if button.label == "Não avaliado").click()
        )

        self.assertEqual(app.exception, [])
        self.assertIn("Raio-X técnico", [item.value for item in app.title])
        self.assertIn("Jogo em promoção", [item.value for item in app.subheader])
        self.run_app(next(button for button in app.button if button.label == "Voltar").click())

        self.assertEqual(app.exception, [])
        self.assertEqual(app.session_state["pagina"], "promocoes")
        app.slider[0].set_value(51)
        self.run_app(app)

        self.assertTrue(
            any(
                "Nenhuma oferta corresponde aos filtros selecionados."
                in message.value
                for message in app.info
            )
        )

    @patch("requests.Session.request")
    @patch("requests.get")
    def test_homepage_shows_promotion_carousel_without_dashboard_metrics(
        self, get: Mock, request: Mock
    ) -> None:
        def api_response(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/avaliacoes/medias"):
                return response(
                    200,
                    {
                        "medias": [
                            {"nome_jogo": "Jogo 0", "media": 4.5, "total": 10},
                            {"nome_jogo": "Jogo 1", "media": 3.8, "total": 5},
                        ]
                    },
                )
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = api_response
        deals = [
            {
                "title": f"Jogo {index}",
                "dealID": f"deal-{index}",
                "storeID": "1",
                "salePrice": "4.99",
                "normalPrice": "9.99",
                "savings": "50",
                "isOnSale": "1",
                "thumb": f"https://images.example/game-{index}.jpg",
            }
            for index in range(4)
        ]

        def external_response(url: str, **kwargs: object) -> Mock:
            if url.endswith("/deals"):
                return response(200, deals)
            if url == "https://api.frankfurter.app/latest":
                return response(
                    200,
                    {"date": "2026-11-09", "rates": {"BRL": 5}},
                )
            if url.endswith("/stores"):
                return response(
                    200,
                    [{"storeID": "1", "storeName": "Steam", "isActive": 1}],
                )
            self.fail(f"Unexpected external API request: {url}")

        get.side_effect = external_response
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        st.cache_data.clear()

        self.run_app(app, timeout=10)

        self.assertEqual(app.exception, [])
        self.assertFalse(
            any(
                metric.label
                in {"Jogos Registrados", "Suas Avaliações", "Jogadores Ativos"}
                for metric in app.metric
            )
        )
        self.assertIn("Ofertas em destaque", [item.value for item in app.subheader])
        self.assertTrue(
            any(
                ":material/computer: PC · :material/storefront: Steam" in item.value
                for item in app.caption
            ),
            [item.value for item in app.caption],
        )
        self.assertEqual(app.metric[0].delta, "-50.1%")
        self.assertTrue(
            any(
                "Média da comunidade: 4,5/5 · 10 avaliação(ões)" in item.value
                for item in app.caption
            )
        )
        self.assertEqual(
            [item.value for item in app.subheader if item.value.startswith("Jogo ")],
            ["Jogo 0", "Jogo 1"],
        )
        next_button = next(
            button for button in app.button if button.label == "Próximas"
        )
        self.run_app(next_button.click(), timeout=10)

        self.assertEqual(app.exception, [])
        self.assertEqual(app.session_state["home_promotions_page"], 1)
        self.assertTrue(
            any(item.value == "Jogo 2" for item in app.subheader)
        )
        self.assertTrue(
            any(item.value == "Jogo 3" for item in app.subheader)
        )

    @patch("requests.Session.request")
    @patch("requests.get")
    def test_homepage_offers_games_to_review_without_search(
        self, get: Mock, request: Mock
    ) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/avaliacoes/medias"):
                return response(
                    200,
                    {"medias": [{"nome_jogo": "Hades", "media": 4.2, "total": 5}]},
                )
            if url.endswith("/avaliacoes/by-game"):
                return response(200, {"avaliacoes": []})
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond

        def external_response(url: str, **kwargs: object) -> Mock:
            if url.endswith("/deals"):
                return response(
                    200,
                    [
                        {
                            "title": "Hades",
                            "dealID": "hades-deal",
                            "storeID": "1",
                            "salePrice": "4.99",
                            "normalPrice": "9.99",
                            "savings": "50",
                            "isOnSale": "1",
                            "thumb": "https://images.example/hades.jpg",
                        }
                    ],
                )
            if url == "https://api.frankfurter.app/latest":
                return response(
                    200,
                    {"date": "2026-11-09", "rates": {"BRL": 5}},
                )
            if url.endswith("/stores"):
                return response(
                    200,
                    [{"storeID": "1", "storeName": "Steam", "isActive": 1}],
                )
            self.fail(f"Unexpected external API request: {url}")

        get.side_effect = external_response
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        st.cache_data.clear()

        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertEqual(app.text_input[0].value, "")
        self.assertIn(
            "Jogos em destaque para avaliar",
            [item.value for item in app.subheader],
        )
        self.assertIn("**Hades**", [item.value for item in app.markdown])
        self.assertTrue(
            any(":material/computer: PC" in item.value for item in app.caption)
        )
        self.assertTrue(
            any(
                "Média da comunidade: 4,2/5 · 5 avaliação(ões)" in item.value
                for item in app.caption
            )
        )
        evaluation_button = next(
            button for button in app.button if button.label == "Fazer avaliação"
        )
        self.run_app(evaluation_button.click())

        self.assertEqual(app.exception, [])
        self.assertIn("Hades", [item.value for item in app.title])
        self.assertTrue(
            any(
                call.args[1].endswith("/avaliacoes/by-game")
                for call in request.call_args_list
                if len(call.args) > 1
            )
        )


    @patch("requests.Session.request")
    @patch("requests.post")
    def test_compatibility_page_saves_preferences_and_shows_explainable_results(
        self, post: Mock, request: Mock
    ) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/compatibilidade/preferencias") and method == "GET":
                return response(200, {"preferencias": None})
            if url.endswith("/compatibilidade/preferencias") and method == "PUT":
                return response(200, {"preferencias": kwargs["json"]})
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        post.side_effect = [
            response(200, {"access_token": "igdb-test-token"}),
            response(
                200,
                [
                    {
                        "id": 11,
                        "slug": "hades",
                        "name": "Hades",
                        "summary": "Um roguelike de ação com progressão entre partidas.",
                        "cover": {"image_id": "hades-cover"},
                        "genres": [{"name": "Action"}],
                        "themes": [{"name": "Fantasy"}],
                        "game_modes": [{"name": "Single player"}],
                        "platforms": [{"name": "PC (Microsoft Windows)"}],
                    }
                ],
            ),
        ]
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app.session_state["pagina"] = "compatibilidade"
        __import__("app").buscar_catalogo_compatibilidade_igdb.clear()
        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertIn(
            "Inteligência de Compatibilidade",
            [item.value for item in app.title],
        )
        app.multiselect(key="compatibility_genres").set_value(["Action"])
        app.multiselect(key="compatibility_styles").set_value(["Fantasy"])
        submit_button = next(
            button
            for button in app.button
            if button.label == "Salvar e ver recomendações"
        )
        self.run_app(submit_button.click())

        self.assertEqual(app.exception, [])
        self.assertIn(
            "Preferências salvas na sua conta.",
            [item.value for item in app.success],
        )
        self.assertEqual(
            app.session_state["compatibility_preferences"]["generos"],
            ["Action"],
        )
        self.assertEqual(app.session_state["compatibility_results"][0].score, 100)
        self.assertTrue(any("Hades" in item.value for item in app.subheader))
        self.assertTrue(any("Temas: Fantasy" in item.value for item in app.caption))
        self.assertTrue(
            any(
                image.proto.imgs[0].url
                == "https://images.igdb.com/igdb/image/upload/"
                "t_cover_big/hades-cover.jpg"
                for image in app.image
            )
        )
        self.assertTrue(any("100%" == item.value for item in app.metric))
        self.assertTrue(
            any(
                "Cobertura dos dados avaliados: 100%" in item.value
                for item in app.caption
            )
        )
        self.assertTrue(
            any(
                call.args[1].endswith("/compatibilidade/preferencias")
                and call.args[0] == "PUT"
                for call in request.call_args_list
            )
        )
        self.assertFalse(
            any(
                call.args[1].endswith("/compatibilidade/catalogo")
                for call in request.call_args_list
            )
        )
        catalog_request = next(
            call
            for call in post.call_args_list
            if call.args[0].endswith("/games")
        )
        self.assertIn("genres.name", catalog_request.kwargs["data"])
        self.assertIn("themes.name", catalog_request.kwargs["data"])
        self.assertIn("game_modes.name", catalog_request.kwargs["data"])
        self.assertIn("platforms.name", catalog_request.kwargs["data"])

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_compatibility_save_failure_does_not_claim_success(
        self, post: Mock, request: Mock
    ) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/compatibilidade/preferencias") and method == "GET":
                return response(200, {"preferencias": None})
            if url.endswith("/compatibilidade/preferencias") and method == "PUT":
                return response(500, {"message": "database unavailable"})
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        post.side_effect = [
            response(200, {"access_token": "igdb-test-token"}),
            response(200, []),
        ]
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app.session_state["pagina"] = "compatibilidade"
        __import__("app").buscar_catalogo_compatibilidade_igdb.clear()
        self.run_app(app)
        save_button = next(
            button for button in app.button if button.label == "Salvar preferências"
        )
        self.run_app(save_button.click())

        self.assertEqual(app.exception, [])
        self.assertTrue(app.error)
        self.assertFalse(app.success)
        self.assertEqual(
            app.session_state["compatibility_preferences"]["generos"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
