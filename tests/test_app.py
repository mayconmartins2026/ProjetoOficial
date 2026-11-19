from __future__ import annotations

import os
import unittest
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image
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
    def run_app(
        self,
        app: AppTest,
        *,
        timeout: float = 10,
    ) -> AppTest:
        with patch.dict(
            os.environ,
            {
                "XANO_API_BASE_URL": API_URL,
                "TWITCH_CLIENT_ID": "test-client-id",
                "TWITCH_CLIENT_SECRET": "test-client-secret",
            },
        ):
            return app.run(timeout=timeout)

    def test_featured_game_covers_have_identical_dimensions(self) -> None:
        import app as app_module

        normalized_sizes = []
        for source_size in ((900, 300), (300, 900)):
            source = Image.new("RGB", source_size, "#ffffff")
            source_bytes = BytesIO()
            source.save(source_bytes, format="PNG")

            normalized = app_module._normalize_featured_game_cover(
                source_bytes.getvalue()
            )
            with Image.open(BytesIO(normalized)) as image:
                normalized_sizes.append(image.size)

        self.assertEqual(
            normalized_sizes,
            [app_module.FEATURED_COVER_SIZE, app_module.FEATURED_COVER_SIZE],
        )

    def test_review_cover_accent_comes_from_game_art(self) -> None:
        import app as app_module

        source = Image.new("RGB", (64, 64), "#d4148e")
        source_bytes = BytesIO()
        source.save(source_bytes, format="PNG")

        self.assertEqual(
            app_module._extract_cover_accent_color(source_bytes.getvalue()),
            "#d4148e",
        )

    @patch("app.requests.get")
    def test_featured_covers_accept_supported_image_hosts(self, get: Mock) -> None:
        import app as app_module

        source = Image.new("RGB", (231, 87), "#ffffff")
        source_bytes = BytesIO()
        source.save(source_bytes, format="PNG")
        image_response = Mock()
        image_response.content = source_bytes.getvalue()
        image_response.raise_for_status.return_value = None
        get.return_value = image_response
        app_module._load_featured_game_cover.clear()

        cover_urls = (
            "https://shared.fastly.steamstatic.com/test-cover.jpg",
            "https://cdn.fanatical.com/test-cover.jpg",
            "https://cdn.humblebundle.com/test-cover.jpg",
            "https://images.gog-statics.com/test-cover.jpg",
            "https://images.greenmangaming.com/test-cover.jpg",
            "https://sttc.gamersgate.com/test-cover.jpg",
        )
        for cover_url in cover_urls:
            cover = app_module._load_featured_game_cover(
                cover_url,
                app_module.FEATURED_COVER_SIZE,
                tuple(sorted(app_module.FEATURED_COVER_HOSTS)),
            )
            if cover is None:
                self.fail(f"A supported cover URL was not normalized: {cover_url}")
            with Image.open(BytesIO(cover)) as image:
                self.assertEqual(image.size, app_module.FEATURED_COVER_SIZE)

        self.assertEqual(get.call_count, len(cover_urls))

    @patch("app.buscar_jogos_igdb")
    def test_review_media_resolves_edition_to_base_game(
        self, search_games: Mock
    ) -> None:
        import app as app_module

        base_game = {
            "id": 123,
            "name": "Shelter",
            "background_image": (
                "https://images.igdb.com/igdb/image/upload/"
                "t_cover_big/shelter.jpg"
            ),
            "summary": "A game about protecting a family of animals.",
            "screenshots": [{"image_id": "shelter-screen"}],
            "videos": [],
        }
        search_games.side_effect = [[], [base_game]]
        promoted_game = {
            "id": "featured-deal",
            "name": "Shelter: The Heart Edition",
            "background_image": "https://images.example/shelter.jpg",
            "cheapest": Decimal("4.99"),
            "cheapest_deal_id": "deal-id",
        }

        resolved_game = app_module._load_review_game_media(promoted_game)

        self.assertEqual(
            [call.args[0] for call in search_games.call_args_list],
            ["Shelter: The Heart Edition", "Shelter"],
        )
        self.assertEqual(resolved_game["id"], "featured-deal")
        self.assertEqual(resolved_game["name"], "Shelter: The Heart Edition")
        self.assertEqual(
            resolved_game["background_image"],
            base_game["background_image"],
        )
        self.assertEqual(resolved_game["screenshots"], base_game["screenshots"])
        self.assertEqual(resolved_game["cheapest_deal_id"], "deal-id")

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
                        "screenshots": [{"image_id": "hades-screen"}],
                        "videos": [
                            {"name": "Trailer", "video_id": "abcdefghijk"}
                        ],
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
        self.assertIn(
            "screenshots.image_id",
            post.call_args_list[1].kwargs["data"],
        )
        self.assertIn(
            "videos.video_id",
            post.call_args_list[1].kwargs["data"],
        )
        self.assertEqual(
            games,
            [
                {
                    "id": 123,
                    "name": "Hades",
                    "cover": {"image_id": "cover_hades"},
                    "screenshots": [{"image_id": "hades-screen"}],
                    "videos": [
                        {"name": "Trailer", "video_id": "abcdefghijk"}
                    ],
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
    @patch("requests.get")
    def test_selected_game_shows_cover_description_rating_and_review_form(
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
                    {"medias": [{"nome_jogo": "God of War", "media": 4.5, "total": 2}]},
                )
            if url.endswith("/avaliacoes/by-game"):
                return response(
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
                )
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        get.side_effect = [
            response(
                200,
                {
                    "items": [
                        {"type": "app", "name": "God of War", "id": 1593500}
                    ]
                },
            ),
            response(
                200,
                {
                    "1593500": {
                        "success": True,
                        "data": {
                            "short_description": (
                                "Kratos e Atreus viajam pelos reinos nórdicos."
                            )
                        },
                    }
                },
            ),
        ]
        app = AppTest.from_file(str(APP_PATH))
        app_module = __import__("app")
        app_module._load_brazilian_game_description.clear()
        app.session_state["auth_token"] = "session-token"
        app.session_state["jogo_selecionado"] = {
            "id": "3498",
            "name": "God of War",
            "background_image": "https://images.example/god-of-war.jpg",
            "summary": "Kratos and Atreus journey through Norse realms.",
            "first_release_date": 1516060800,
            "platforms": [
                {"name": "PlayStation 5"},
                {"name": "PC (Microsoft Windows)"},
            ],
            "genres": [{"name": "Action"}, {"name": "Adventure"}],
            "themes": [{"name": "Open world"}],
            "involved_companies": [
                {
                    "developer": True,
                    "company": {"name": "Sony Interactive Entertainment"},
                }
            ],
            "screenshots": [
                {"image_id": "gow-screen-01"},
                {"image_id": "gow-screen-02"},
            ],
            "videos": [
                {"name": "Trailer oficial", "video_id": "dQw4w9WgXcQ"}
            ],
        }
        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertTrue(any("Sobre o jogo" in item.value for item in app.subheader))
        self.assertTrue(any("God of War" in item.value for item in app.title))
        self.assertTrue(
            any(
                "Kratos e Atreus viajam pelos reinos nórdicos." in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                "Nota atual no site" in item.value for item in app.markdown
            )
        )
        self.assertTrue(any("## 4,5 / 5" in item.value for item in app.markdown))
        self.assertTrue(
            any("2 avaliações da comunidade" in item.value for item in app.caption)
        )
        self.assertTrue(
            any("★★★★★" in item.value for item in app.markdown)
        )
        for metadata in (
            "Plataformas: PS5, PC",
            "Gênero: Ação, Aventura",
            "Estilo: Mundo aberto",
            "Desenvolvedora: Sony Interactive Entertainment",
            "Lançamento: 2018",
        ):
            self.assertTrue(
                any(metadata in item.value for item in app.markdown),
                metadata,
            )
        self.assertEqual(len(app.text_area), 1)
        self.assertEqual(app.text_area[0].label, "Comentário")
        self.assertIn("Sua avaliação", [item.value for item in app.subheader])
        self.assertFalse(
            any(button.label == "Avaliar este jogo" for button in app.button)
        )
        self.assertTrue(
            any(
                image.proto.imgs[0].url
                == "https://images.example/god-of-war.jpg"
                for image in app.image
            )
        )
        self.assertTrue(
            any(
                image.proto.imgs[0].url.endswith(
                    "/t_screenshot_big/gow-screen-01.jpg"
                )
                for image in app.image
            )
        )
        self.run_app(
            next(button for button in app.button if button.label == "Próxima").click()
        )
        self.assertTrue(
            any(
                image.proto.imgs[0].url.endswith(
                    "/t_screenshot_big/gow-screen-02.jpg"
                )
                for image in app.image
            )
        )
        self.run_app(
            next(button for button in app.button if button.label == "Próxima").click()
        )
        self.assertEqual(len(app.get("video")), 1)
        self.assertTrue(
            any("Trailer oficial" in item.value for item in app.caption)
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
    @patch("requests.get")
    def test_review_uses_english_igdb_description_when_steam_has_no_pt_br(
        self, get: Mock, request: Mock
    ) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/avaliacoes/medias"):
                return response(200, {"medias": []})
            if url.endswith("/avaliacoes/by-game"):
                return response(200, {"avaliacoes": []})
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        get.return_value = response(200, {"items": []})
        app = AppTest.from_file(str(APP_PATH))
        app_module = __import__("app")
        app_module._load_brazilian_game_description.clear()
        app.session_state["auth_token"] = "session-token"
        app.session_state["jogo_selecionado"] = {
            "id": "english-only-game",
            "name": "English-only game",
            "summary": "This description is available in English.",
            "screenshots": [],
            "videos": [],
        }

        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertTrue(
            any(
                "This description is available in English." in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                "Sinopse original em inglês" in item.value
                for item in app.caption
            )
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
            if url.endswith("/api/storesearch/"):
                return response(200, {"items": []})
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_token"] = "session-token"
        app.session_state["jogo_selecionado"] = {
            "id": "3498",
            "name": "God of War",
            "screenshots": [],
            "videos": [],
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
                "## 5,0 / 5" in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                "1 avaliação da comunidade" in item.value
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
            if url.startswith(
                "https://images.igdb.com/igdb/image/upload/"
            ):
                source = Image.new("RGB", (64, 64), "#d4148e")
                source_bytes = BytesIO()
                source.save(source_bytes, format="PNG")
                image_response = Mock()
                image_response.content = source_bytes.getvalue()
                image_response.raise_for_status.return_value = None
                return image_response
            if url.endswith("/deals"):
                return response(200, [])
            if url.endswith("/stores"):
                return response(200, [])
            if url == "https://api.frankfurter.app/latest":
                return response(
                    200,
                    {"date": "2026-11-09", "rates": {"BRL": 5}},
                )
            if url.endswith("/api/storesearch/"):
                return response(200, {"items": []})
            self.fail(f"Unexpected external API request: {url}")

        get.side_effect = get_external
        post.side_effect = [
            response(200, {"access_token": "test-access-token"}),
            response(
                200,
                [
                    {
                        "id": 123,
                        "name": "Hades",
                        "cover": {"image_id": "hades"},
                        "artworks": [{"image_id": "hades-art"}],
                        "platforms": [
                            {"name": "Xbox Series X|S"},
                            {"name": "PlayStation 5"},
                        ],
                        "first_release_date": 1712361600,
                        "genres": [{"name": "Action"}, {"name": "Adventure"}],
                        "themes": [{"name": "Open world"}],
                        "involved_companies": [
                            {
                                "developer": True,
                                "company": {"name": "Supergiant Games"},
                            }
                        ],
                    }
                ],
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
        self.assertTrue(
            any(
                ":material/sports_esports: Xbox Series X|S · "
                ":material/videogame_asset: PlayStation 5"
                in item.value
                for item in app.caption
            )
        )
        evaluation_button = next(
            button for button in app.button if button.label == "Fazer avaliação"
        )
        self.run_app(evaluation_button.click())

        self.assertEqual(app.exception, [])
        self.assertTrue(
            any(
                "## 4,5 / 5" in item.value for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                "Desenvolvedora: Supergiant Games" in item.value
                for item in app.markdown
            )
        )
        self.assertIn("Sua avaliação", [item.value for item in app.subheader])
        self.assertEqual(app.text_area[0].label, "Comentário")
        self.assertTrue(
            any(
                image.proto.imgs[0].url
                == "https://images.igdb.com/igdb/image/upload/t_cover_big/hades.jpg"
                for image in app.image
            )
        )
        self.assertTrue(
            any("t_1080p/hades-art.jpg" in item.value for item in app.markdown)
        )
        xray_button = next(
            button for button in app.button if button.label == "Ver Raio-X técnico"
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
        igdb_query = game_searches[0].kwargs["data"]
        self.assertIn("artworks.image_id", igdb_query)
        self.assertIn("involved_companies.company.name", igdb_query)

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
                    "storeID": "15",
                    "salePrice": "4.99",
                    "normalPrice": "9.99",
                    "savings": "50.050050",
                    "isOnSale": "1",
                    "thumb": "https://images.example/game.jpg",
                },
                {
                    "title": "Desconto pequeno",
                    "dealID": "small-deal",
                    "storeID": "15",
                    "salePrice": "9.99",
                    "normalPrice": "10.00",
                    "savings": "0",
                    "isOnSale": "1",
                    "thumb": "https://images.example/small-discount.jpg",
                },
                {
                    "title": "Sem desconto",
                    "dealID": "no-discount",
                    "storeID": "15",
                    "salePrice": "9.99",
                    "normalPrice": "9.99",
                    "savings": "0",
                    "isOnSale": "1",
                    "thumb": "https://images.example/no-discount.jpg",
                },
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
                    [{"storeID": "15", "storeName": "Fanatical", "isActive": 1}],
                )
            if url.endswith("/api/storesearch/"):
                return response(200, {"items": []})
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
            any(
                "R$ 24,95" in item.value for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                "Avaliação da comunidade: 4,2/5 (5)" in item.value
                for item in app.markdown
            ),
            [item.value for item in app.markdown],
        )
        self.assertTrue(
            any(
                ":material/sports_esports: Fanatical" in item.value
                for item in app.caption
            ),
            [item.value for item in app.caption],
        )
        self.assertTrue(
            any(
                "deal-card-cover" in item.value
                and "https://images.example/game.jpg" in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                "deal-card-discount" in item.value and "-&lt;1%" in item.value
                for item in app.markdown
            )
        )
        self.assertFalse(any("Sem desconto" in item.value for item in app.markdown))
        self.assertTrue(
            any(
                "R$ 49,95" in item.value and "<s>" in item.value
                for item in app.markdown
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
                "storeID": "15",
            },
        )
        self.run_app(
            next(
                button
                for button in app.button
                if button.label == "Ver Raio-X técnico"
            ).click()
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
                "storeID": "15",
                "salePrice": "4.99",
                "normalPrice": "9.99",
                "savings": "50",
                "isOnSale": "1",
                "thumb": f"https://images.example/game-{index}.jpg",
            }
            for index in range(12)
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
                    [{"storeID": "15", "storeName": "Fanatical", "isActive": 1}],
                )
            if url.endswith("/api/storesearch/"):
                return response(200, {"items": []})
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
                ":material/sports_esports: Fanatical" in item.value
                for item in app.caption
            ),
            [item.value for item in app.caption],
        )
        self.assertTrue(
            any(
                "Ofertas 1–8 de 12" in item.value for item in app.caption
            )
        )
        self.assertTrue(
            any(
                "deal-card-discount" in item.value and "-50%" in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(any("R$ 24,95" in item.value for item in app.markdown))
        self.assertTrue(any(button.label == "Avaliar" for button in app.button))
        next_button = next(
            button for button in app.button if button.label == "Próximas"
        )
        self.run_app(next_button.click(), timeout=10)

        self.assertEqual(app.exception, [])
        self.assertEqual(app.session_state["home_promotions_page"], 1)
        self.assertTrue(
            any("Ofertas 9–12 de 12" in item.value for item in app.caption)
        )
        self.assertTrue(any("Jogo 8" in item.value for item in app.markdown))
        self.assertTrue(any("Jogo 11" in item.value for item in app.markdown))

    @patch("requests.Session.request")
    @patch("requests.get")
    @patch("requests.post")
    def test_homepage_offers_games_to_review_without_search(
        self, post: Mock, get: Mock, request: Mock
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
                            "storeID": "15",
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
                    [{"storeID": "15", "storeName": "Fanatical", "isActive": 1}],
                )
            if url.endswith("/api/storesearch/"):
                return response(200, {"items": []})
            self.fail(f"Unexpected external API request: {url}")

        get.side_effect = external_response
        post.side_effect = [
            response(200, {"access_token": "igdb-test-token"}),
            response(
                200,
                [
                    {
                        "id": 123,
                        "name": "Hades",
                        "summary": "A test description of Hades.",
                        "screenshots": [{"image_id": "hades-screen"}],
                        "videos": [
                            {"name": "Hades trailer", "video_id": "abcdefghijk"}
                        ],
                    }
                ],
            ),
        ]
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
                "★ 4,2 / 5 · 5 avaliações" in item.value
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
                image.proto.imgs[0].url.endswith(
                    "/t_screenshot_big/hades-screen.jpg"
                )
                for image in app.image
            )
        )
        self.assertTrue(
            any(
                "A test description of Hades." in item.value
                for item in app.markdown
            )
        )
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
            if url.endswith("/api/storesearch/"):
                return response(200, {"items": []})
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
        app.session_state["compatibility_catalog"] = None
        app.session_state["compatibility_preferences"] = None
        app.session_state["compatibility_preferences_error"] = None
        app.session_state["compatibility_results"] = None
        app.session_state["compatibility_owner"] = "7"
        app.session_state["compatibility_genres"] = []
        app.session_state["compatibility_styles"] = []
        app.session_state["compatibility_modes"] = []
        app.session_state["compatibility_platforms"] = []
        app.session_state["auth_token"] = "session-token"
        app.session_state["pagina"] = "compatibilidade"
        st.cache_data.clear()
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
                if len(call.args) > 1
            )
        )
        self.assertFalse(
            any(
                call.args[1].endswith("/compatibilidade/catalogo")
                for call in request.call_args_list
                if len(call.args) > 1
            )
        )
        catalog_requests = [
            call
            for call in post.call_args_list
            if call.args[0].endswith("/games")
        ]
        self.assertEqual(len(catalog_requests), 1, repr(post.call_args_list))
        catalog_request = catalog_requests[0]
        self.assertIn("genres.name", catalog_request.kwargs["data"])
        self.assertIn("themes.name", catalog_request.kwargs["data"])
        self.assertIn("game_modes.name", catalog_request.kwargs["data"])
        self.assertIn("platforms.name", catalog_request.kwargs["data"])

    @patch("requests.Session.request")
    @patch("requests.post")
    def test_compatibility_filters_work_when_xano_preferences_are_unavailable(
        self, post: Mock, request: Mock
    ) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/compatibilidade/preferencias"):
                return response(404, {"message": "missing"})
            if url.endswith("/api/storesearch/"):
                return response(200, {"items": []})
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
                        "summary": "A test description.",
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
        app.session_state["compatibility_catalog"] = None
        app.session_state["compatibility_preferences"] = None
        app.session_state["compatibility_preferences_error"] = None
        app.session_state["compatibility_results"] = None
        app.session_state["compatibility_owner"] = "7"
        app.session_state["compatibility_genres"] = []
        app.session_state["compatibility_styles"] = []
        app.session_state["compatibility_modes"] = []
        app.session_state["compatibility_platforms"] = []
        app.session_state["auth_token"] = "session-token"
        app.session_state["pagina"] = "compatibilidade"
        st.cache_data.clear()

        self.run_app(app)

        self.assertEqual(app.exception, [])
        self.assertEqual(
            {field.label for field in app.multiselect},
            {
                "Gêneros favoritos",
                "Temas favoritos",
                "Modo de jogo",
                "Plataformas utilizadas",
            },
        )
        self.assertFalse(app.warning)
        app.multiselect(key="compatibility_genres").set_value(["Action"])
        app.multiselect(key="compatibility_styles").set_value(["Fantasy"])
        search_button = next(
            button for button in app.button if button.label == "Ver jogos compatíveis"
        )
        self.run_app(search_button.click())

        self.assertEqual(app.exception, [])
        self.assertEqual(app.session_state["compatibility_results"][0].score, 100)
        self.assertTrue(
            any("Recomendações atualizadas" in item.value for item in app.success)
        )
        self.assertFalse(app.warning)
        self.assertTrue(
            any("A test description." in item.value for item in app.markdown)
        )
        self.assertTrue(
            any(
                "exibindo o texto original em inglês" in item.value
                for item in app.caption
            )
        )
        self.assertFalse(
            any(
                call.args[0] == "PUT"
                for call in request.call_args_list
                if len(call.args) > 0
            )
        )
        self.assertFalse(
            any(
                call.args[1].endswith("/compatibilidade/catalogo")
                for call in request.call_args_list
                if len(call.args) > 1
            )
        )

    @patch("requests.Session.request")
    def test_missing_preferences_endpoint_saves_only_for_current_session(
        self, request: Mock
    ) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/compatibilidade/preferencias"):
                return response(404, {"message": "missing"})
            self.fail(f"Unexpected API request: {method} {url}")

        request.side_effect = respond
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["compatibility_catalog"] = {
            "jogos": [{"id": 11}],
            "vocabulario": {
                "generos": ["Action"],
                "estilos": [],
                "modos": [],
                "plataformas": [],
            },
        }
        app.session_state["compatibility_preferences"] = None
        app.session_state["compatibility_preferences_error"] = None
        app.session_state["compatibility_preferences_error_code"] = None
        app.session_state["compatibility_results"] = None
        app.session_state["compatibility_owner"] = "7"
        app.session_state["compatibility_genres"] = []
        app.session_state["compatibility_styles"] = []
        app.session_state["compatibility_modes"] = []
        app.session_state["compatibility_platforms"] = []
        app.session_state["auth_token"] = "session-token"
        app.session_state["pagina"] = "compatibilidade"

        self.run_app(app)
        app.multiselect(key="compatibility_genres").set_value(["Action"])
        save_button = next(
            button for button in app.button if button.label == "Salvar preferências"
        )
        self.run_app(save_button.click())

        self.assertEqual(app.exception, [])
        self.assertFalse(app.error)
        self.assertFalse(app.warning)
        self.assertEqual(
            app.session_state["compatibility_preferences"]["generos"],
            ["Action"],
        )
        self.assertTrue(
            any("apenas nesta sessão" in item.value for item in app.caption)
        )
        self.assertFalse(
            any(
                call.args[0] == "PUT"
                for call in request.call_args_list
                if call.args
            )
        )

    @patch("requests.Session.request")
    @patch("requests.post")
    @patch("requests.get")
    def test_compatibility_uses_brazilian_steam_descriptions(
        self, get: Mock, post: Mock, request: Mock
    ) -> None:
        def respond(method: str, url: str, **kwargs: object) -> Mock:
            if url.endswith("/auth/me"):
                return response(
                    200,
                    {"id": 7, "name": "Jogador", "email": "user@example.com"},
                )
            if url.endswith("/compatibilidade/preferencias"):
                return response(404, {"message": "missing"})
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
                        "summary": "A test description.",
                        "cover": {"image_id": "hades-cover"},
                        "genres": [{"name": "Action"}],
                    }
                ],
            ),
        ]
        get.side_effect = [
            response(
                200,
                {"items": [{"type": "app", "name": "Hades", "id": 1145360}]},
            ),
            response(
                200,
                {
                    "1145360": {
                        "success": True,
                        "data": {"short_description": "Descrição da Steam em pt-BR."},
                    }
                },
            ),
        ]
        app_module = __import__("app")
        app_module.buscar_catalogo_compatibilidade_igdb.clear()
        app_module._load_brazilian_game_description.clear()
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["compatibility_catalog"] = None
        app.session_state["compatibility_preferences"] = None
        app.session_state["compatibility_preferences_error"] = None
        app.session_state["compatibility_results"] = None
        app.session_state["compatibility_owner"] = "7"
        app.session_state["compatibility_genres"] = []
        app.session_state["compatibility_styles"] = []
        app.session_state["compatibility_modes"] = []
        app.session_state["compatibility_platforms"] = []
        app.session_state["auth_token"] = "session-token"
        app.session_state["pagina"] = "compatibilidade"
        st.cache_data.clear()

        self.run_app(app)
        app.multiselect(key="compatibility_genres").set_value(["Action"])
        search_button = next(
            button for button in app.button if button.label == "Ver jogos compatíveis"
        )
        self.run_app(search_button.click())

        self.assertEqual(app.exception, [])
        self.assertTrue(
            any("Descrição da Steam em pt-BR." in item.value for item in app.markdown)
        )
        self.assertEqual(get.call_count, 2)

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
