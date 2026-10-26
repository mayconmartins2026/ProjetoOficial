from __future__ import annotations

import base64
import os
import re
from datetime import date, datetime, timezone
from html import unescape
from typing import Any
from zoneinfo import ZoneInfo

import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from ggreviews.auth_client import (
    AuthAPI,
    AuthAPIError,
    email_validation_error,
    password_policy_error,
)
from ggreviews.config import ConfigurationError, load_auth_config


def _capture_password_reset_link() -> None:
    magic_token = st.query_params.get("magic_token")
    email = st.query_params.get("email")
    if magic_token is None and email is None:
        return

    st.query_params.clear()
    if isinstance(magic_token, str) and magic_token and isinstance(email, str) and email:
        st.session_state["password_reset_link"] = {
            "magic_token": magic_token,
            "email": email,
        }
    else:
        st.session_state["password_reset_link"] = None


def _render_password_reset(api: AuthAPI, link: dict[str, str]) -> None:
    st.subheader("Redefinir senha")
    with st.form("complete_password_reset"):
        password = st.text_input("Nova senha", type="password")
        confirm_password = st.text_input("Confirme a nova senha", type="password")
        submitted = st.form_submit_button("Salvar nova senha")

    if not submitted:
        return
    if error := password_policy_error(password):
        st.error(error)
        return
    if password.strip() != confirm_password.strip():
        st.error("As senhas não correspondem.")
        return

    try:
        api.complete_password_reset(
            link["magic_token"], link["email"], password, confirm_password
        )
    except AuthAPIError as error:
        if error.code == "invalid_reset_link":
            st.session_state.pop("password_reset_link", None)
        st.error(error.message)
        return

    st.session_state.pop("password_reset_link", None)
    st.session_state["auth_notice"] = "Senha atualizada. Entre com sua nova senha."
    st.rerun()


def _render_signup(api: AuthAPI) -> None:
    with st.form("signup"):
        name = st.text_input("Nome")
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        confirm_password = st.text_input("Confirme a senha", type="password")
        submitted = st.form_submit_button("Criar conta")

    if not submitted:
        return
    if not name.strip():
        st.error("Informe seu nome.")
        return
    if email_error := email_validation_error(email):
        st.error(email_error)
        return
    if password_policy := password_policy_error(password):
        st.error(password_policy)
        return
    if password.strip() != confirm_password.strip():
        st.error("As senhas não correspondem.")
        return

    try:
        result = api.signup(name, email, password)
    except AuthAPIError as error:
        st.error(error.message)
        return

    st.session_state["auth_token"] = result.token
    st.session_state["user_profile"] = {
        "name": name.strip(),
        "email": email.strip().lower(),
    }
    st.session_state["auth_notice"] = f"Bem-vindo, {name.strip()}!"
    st.rerun()


def _render_login(api: AuthAPI) -> None:
    with st.form("login"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if not submitted:
        return
    if email_error := email_validation_error(email):
        st.error(email_error)
        return
    try:
        result = api.login(email, password)
    except AuthAPIError as error:
        st.error(error.message)
        return

    try:
        user = api.current_user(result.token)
    except AuthAPIError:
        user = {}
        st.session_state["auth_notice"] = "Bem-vindo!"
        st.session_state["auth_token"] = result.token
        st.rerun()
        return

    st.session_state["auth_token"] = result.token
    st.session_state["user_profile"] = user
    user_name = user.get("name") or user.get("email") or "Jogador"
    st.session_state["auth_notice"] = f"Bem-vindo, {user_name}!"
    st.rerun()


def _render_recovery(api: AuthAPI) -> None:
    with st.form("request_password_reset"):
        email = st.text_input("E-mail da conta")
        submitted = st.form_submit_button("Enviar link de recuperação")

    if not submitted:
        return
    if email_error := email_validation_error(email):
        st.error(email_error)
        return
    try:
        api.request_password_reset(email)
    except AuthAPIError as error:
        st.error(error.message)
        return

    st.success(
        "Se houver uma conta associada a esse e-mail, você receberá um link de recuperação."
    )


def _render_auth_forms(api: AuthAPI) -> None:
    login_tab, signup_tab, recovery_tab = st.tabs(
        ["Entrar", "Criar conta", "Recuperar senha"]
    )
    with login_tab:
        _render_login(api)
    with signup_tab:
        _render_signup(api)
    with recovery_tab:
        _render_recovery(api)


@st.cache_data(ttl=3600)
def buscar_jogos_rawg(api_key: str, termo_busca: str = "") -> list:
    """Busca jogos na API do RAWG, com suporte a pesquisa."""
    url = f"https://api.rawg.io/api/games?key={api_key}&page_size=10"

    if termo_busca:
        url += f"&search={termo_busca}"
    else:
        # Se não tiver busca, traz os populares/recentes
        url += "&ordering=-added"

    try:
        resposta = requests.get(url, timeout=10)
        if resposta.status_code == 200:
            dados = resposta.json()
            return dados.get("results", [])
    except Exception as e:
        st.error(f"Erro ao conectar com a API: {e}")

    return []


@st.cache_data(ttl=3600)
def buscar_detalhes_jogo_rawg(api_key: str, game_id: int) -> dict[str, Any]:
    resposta = requests.get(
        f"https://api.rawg.io/api/games/{game_id}",
        params={"key": api_key},
        timeout=10,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    if not isinstance(dados, dict):
        raise ValueError("A API RAWG retornou detalhes inválidos.")
    return dados


@st.cache_data(ttl=3600, max_entries=256)
def buscar_capa_jogo_rawg(api_key: str, nome_jogo: str) -> str | None:
    resposta = requests.get(
        "https://api.rawg.io/api/games",
        params={"key": api_key, "search": nome_jogo, "page_size": 10},
        timeout=10,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    resultados = dados.get("results") if isinstance(dados, dict) else None
    if not isinstance(resultados, list):
        raise ValueError("A API RAWG retornou uma lista de jogos inválida.")

    nome_normalizado = nome_jogo.strip().casefold()
    jogos = [jogo for jogo in resultados if isinstance(jogo, dict)]
    jogo = next(
        (
            item
            for item in jogos
            if isinstance(item.get("name"), str)
            and item["name"].strip().casefold() == nome_normalizado
            and isinstance(item.get("background_image"), str)
        ),
        None,
    )
    if jogo is None:
        jogo = next(
            (
                item
                for item in jogos
                if isinstance(item.get("background_image"), str)
            ),
            None,
        )
    capa = jogo.get("background_image") if jogo else None
    return capa if isinstance(capa, str) and capa else None


def _resumo_texto(descricao: str) -> str:
    texto = unescape(re.sub(r"<[^>]*>", " ", descricao))
    texto = re.sub(r"\s+", " ", texto).strip()
    frases = re.split(r"(?<=[.!?])\s+", texto)
    resumo = " ".join(frases[:2]).strip()
    if len(resumo) > 500:
        resumo = resumo[:497].rsplit(" ", 1)[0] + "..."
    return resumo


@st.cache_data(ttl=86400, max_entries=256)
def _traduzir_para_portugues(texto: str) -> str:
    resposta = requests.get(
        "https://api.mymemory.translated.net/get",
        params={
            "q": texto,
            "langpair": "autodetect|pt-BR",
        },
        timeout=10,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    response_data = dados.get("responseData") if isinstance(dados, dict) else None
    traducao = (
        response_data.get("translatedText")
        if isinstance(response_data, dict)
        else None
    )
    if not isinstance(traducao, str) or not traducao.strip():
        raise ValueError("O serviço de tradução não retornou um resumo.")
    return unescape(traducao).strip()


def _placeholder_data_uri(label: str, *, kind: str) -> str:
    safe_label = re.sub(r"[^A-Za-z0-9 ]+", "", label or kind).strip() or kind.title()
    initials = safe_label[:2].upper()
    if kind == "avatar":
        svg = f"""
        <svg xmlns='http://www.w3.org/2000/svg' width='320' height='320' viewBox='0 0 320 320'>
          <defs>
            <linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'>
              <stop offset='0%' stop-color='#7c3aed'/>
              <stop offset='100%' stop-color='#22d3ee'/>
            </linearGradient>
          </defs>
          <rect width='320' height='320' rx='160' fill='url(#g)'/>
          <circle cx='160' cy='120' r='52' fill='rgba(255,255,255,0.18)'/>
          <path d='M80 248c18-36 54-56 80-56s62 20 80 56v26H80z' fill='rgba(255,255,255,0.18)'/>
          <text x='160' y='284' text-anchor='middle' font-family='Arial, sans-serif' font-size='42' font-weight='700' fill='white'>{initials}</text>
        </svg>
        """.strip()
    else:
        svg = f"""
        <svg xmlns='http://www.w3.org/2000/svg' width='640' height='360' viewBox='0 0 640 360'>
          <defs>
            <linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'>
              <stop offset='0%' stop-color='#111827'/>
              <stop offset='100%' stop-color='#7c3aed'/>
            </linearGradient>
          </defs>
          <rect width='640' height='360' rx='28' fill='url(#g)'/>
          <circle cx='134' cy='108' r='84' fill='rgba(255,255,255,0.08)'/>
          <circle cx='520' cy='250' r='92' fill='rgba(34,211,238,0.12)'/>
          <text x='320' y='192' text-anchor='middle' font-family='Arial, sans-serif' font-size='88' font-weight='800' fill='white'>{initials}</text>
          <text x='320' y='240' text-anchor='middle' font-family='Arial, sans-serif' font-size='20' fill='rgba(255,255,255,0.8)'>{safe_label[:18]}</text>
        </svg>
        """.strip()
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _url_imagem_perfil(valor: Any, api: AuthAPI) -> str | None:
    if isinstance(valor, dict):
        valor = valor.get("url") or valor.get("path")
    if not isinstance(valor, str) or not valor:
        return _placeholder_data_uri("Usuário", kind="avatar")
    if valor.startswith(("https://", "http://")):
        return valor
    return api.public_file_url(valor)


def _url_capa_jogo(game: dict[str, Any]) -> str:
    cover_url = game.get("background_image")
    if isinstance(cover_url, str) and cover_url:
        return cover_url
    return _placeholder_data_uri(game.get("name") or "Jogo", kind="game")


def _format_review_date(value: Any) -> str:
    if isinstance(value, bool):
        return "Data não disponível"
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        epoch = value / 1000 if abs(value) >= 100_000_000_000 else value
        try:
            timestamp = datetime.fromtimestamp(epoch, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return "Data não disponível"
    if isinstance(value, str):
        timestamp = value.strip()
        if not timestamp:
            return "Data não disponível"
        if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", timestamp):
            return _format_review_date(float(timestamp))
        if "T" not in timestamp and " " not in timestamp:
            try:
                return date.fromisoformat(timestamp).strftime("%d/%m/%Y")
            except ValueError:
                return "Data não disponível"
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            try:
                return date.fromisoformat(timestamp).strftime("%d/%m/%Y")
            except ValueError:
                return "Data não disponível"
    if not isinstance(value, (datetime, int, float, str)):
        return "Data não disponível"

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(ZoneInfo("America/Sao_Paulo")).strftime(
        "%d/%m/%Y às %H:%M"
    )


def _review_date_value(review: dict[str, Any]) -> Any:
    for key in ("created_at", "createdAt", "timestamp", "data_criacao", "created"):
        value = review.get(key)
        if value is not None:
            if isinstance(value, dict):
                for nested_key in ("value", "timestamp", "date", "created_at"):
                    if value.get(nested_key) is not None:
                        return value[nested_key]
            return value
    return None


def _render_review_date(review: dict[str, Any]) -> None:
    with st.container(horizontal_alignment="right"):
        st.caption(_format_review_date(_review_date_value(review)))


def _game_platforms(game: dict[str, Any]) -> str:
    platforms = game.get("platforms")
    if not isinstance(platforms, list):
        return ""

    icons = (
        ("pc", "🖥️"),
        ("windows", "🖥️"),
        ("xbox", "🎮"),
        ("playstation", "🎮"),
        ("nintendo", "🎮"),
        ("mac", "🍎"),
        ("linux", "🐧"),
        ("ios", "📱"),
        ("android", "📱"),
        ("web", "🌐"),
    )
    names: list[str] = []
    seen: set[str] = set()
    for entry in platforms:
        platform = entry.get("platform") if isinstance(entry, dict) else None
        name = platform.get("name") if isinstance(platform, dict) else None
        if not isinstance(name, str) or not name.strip():
            continue
        name = name.strip()
        normalized_name = name.casefold()
        if normalized_name in seen:
            continue
        seen.add(normalized_name)
        icon = next(
            (symbol for fragment, symbol in icons if fragment in normalized_name),
            "🎮",
        )
        names.append(f"{icon} {name}")
    return " · ".join(names)


def _apply_gamer_background() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #090b13;
            background-image:
                linear-gradient(130deg, rgba(15, 23, 42, 0.78), rgba(12, 18, 32, 0.72)),
                linear-gradient(140deg, rgba(124, 58, 237, 0.22), rgba(34, 211, 238, 0.12)),
                url("https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1800&q=80");
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }
        [data-testid="stHeader"] {
            background: transparent;
            box-shadow: none;
        }
        [data-testid="stSidebar"] {
            background: rgba(10, 12, 23, 0.82);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(148, 163, 184, 0.15);
        }
        [data-testid="stImage"] img,
        .stImage img {
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            box-shadow: 0 18px 48px rgba(2, 6, 23, 0.45);
            object-fit: cover;
            background: linear-gradient(145deg, #1f2937, #0f172a);
        }
        [data-testid="stSidebar"] [data-testid="stImage"] img,
        [data-testid="stSidebar"] .stImage img {
            border-radius: 50%;
        }
        [data-testid="stImage"] img:hover,
        .stImage img:hover {
            transform: scale(1.02);
            transition: transform 0.2s ease;
        }
        .block-container {
            background: rgba(15, 23, 42, 0.12);
            border-radius: 22px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_game_review(
    api: AuthAPI, token: str, rawg_key: str | None, game: dict[str, Any]
) -> None:
    game_name = str(game.get("name") or "Jogo")
    game_id = game.get("id")

    if st.button("Voltar ao início", key="voltar_inicio"):
        st.session_state.pop("jogo_selecionado", None)
        st.rerun()

    st.title(game_name)
    cover_url = _url_capa_jogo(game)
    st.image(cover_url, alt=f"Capa de {game_name}", width="stretch")

    if not rawg_key:
        st.error("Configure RAWG_API_KEY para carregar o resumo do jogo.")
        return
    if not isinstance(game_id, int):
        st.error("Não foi possível identificar este jogo.")
        return

    try:
        details = buscar_detalhes_jogo_rawg(rawg_key, game_id)
    except (requests.RequestException, ValueError):
        st.error(
            "Não foi possível carregar os detalhes do jogo. "
            "Verifique a conexão e a chave da API RAWG."
        )
        return

    resumo = details.get("description_raw") or details.get("description") or ""
    if isinstance(resumo, str) and _resumo_texto(resumo):
        st.subheader("Sobre o jogo")
        try:
            st.write(_traduzir_para_portugues(_resumo_texto(resumo)))
        except (requests.RequestException, ValueError):
            st.error("Não foi possível traduzir o resumo do jogo para português.")
    else:
        st.info("A API RAWG não disponibilizou um resumo para este jogo.")

    st.divider()
    st.subheader("Sua avaliação")
    with st.form(f"review_{game_id}"):
        rating = st.select_slider(
            "Sua nota (de 1 a 5)",
            options=[1, 2, 3, 4, 5],
            value=5,
            format_func=lambda value: f"{value} / 5",
        )
        review_text = st.text_area(
            "Comentário",
            placeholder="O que você achou deste jogo?",
            max_chars=2000,
        )
        submitted = st.form_submit_button("Enviar avaliação")

    if not submitted:
        return
    if not review_text.strip():
        st.error("Escreva um comentário antes de enviar sua avaliação.")
        return

    try:
        api.create_review(
            token,
            game_name=game_name,
            rating=rating,
            review_text=review_text,
        )
    except AuthAPIError as error:
        st.error(error.message)
        return

    st.session_state["auth_notice"] = "Sua avaliação foi enviada."
    st.rerun()


def _render_game_comments(
    api: AuthAPI, token: str, game_name: str
) -> None:
    try:
        reviews = api.game_reviews(token, game_name)
    except AuthAPIError as error:
        st.error(error.message)
        return

    st.divider()
    st.subheader("Comentários da comunidade")
    if not reviews:
        st.info("Este jogo ainda não recebeu comentários.")
        return

    for review in reviews:
        author = review.get("_user", {})
        if not isinstance(author, dict):
            author = {}
        username = author.get("name") or "Jogador"
        avatar = _url_imagem_perfil(author.get("img_perfil"), api)

        with st.container(border=True):
            avatar_col, content_col = st.columns([1, 5])
            with avatar_col:
                st.image(
                    avatar,
                    alt=f"Foto de perfil de {username}",
                    width=48,
                )
            with content_col:
                st.markdown(f"**{username}**")
                st.caption(f"Nota: {review.get('nota', '—')} / 5")
                st.write(review.get("comentario", ""))
            _render_review_date(review)


def _render_profile_settings(
    api: AuthAPI, token: str, user: dict[str, Any]
) -> None:
    st.title("Configurações")
    if st.button("Voltar ao início", key="voltar_configuracoes"):
        st.session_state["pagina"] = "inicio"
        st.rerun()

    st.subheader("Foto de perfil")
    current_image = _url_imagem_perfil(user.get("img_perfil"), api)
    st.image(current_image, alt="Sua foto de perfil", width=140)

    with st.form("atualizar_foto_perfil"):
        imagem = st.file_uploader(
            "Escolha uma imagem",
            type=["jpg", "jpeg", "png", "webp", "gif"],
            max_upload_size=5,
            help="Formatos aceitos: JPG, PNG, WebP ou GIF. Tamanho máximo: 5 MB.",
        )
        submitted = st.form_submit_button("Salvar foto de perfil")

    if not submitted:
        return
    if imagem is None:
        st.error("Selecione uma imagem antes de salvar.")
        return
    if imagem.type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        st.error("O arquivo selecionado não é um formato de imagem aceito.")
        return

    try:
        updated_user = api.update_profile_photo(
            token,
            file_name=imagem.name,
            content=imagem.getvalue(),
            content_type=imagem.type,
        )
    except AuthAPIError as error:
        st.error(error.message)
        return

    st.session_state["user_profile"] = updated_user
    st.session_state["auth_notice"] = "Sua foto de perfil foi atualizada."
    st.rerun()


def _clear_cached_rawg_data() -> None:
    for func in (
        buscar_jogos_rawg,
        buscar_detalhes_jogo_rawg,
        buscar_capa_jogo_rawg,
        _traduzir_para_portugues,
    ):
        clear = getattr(func, "clear", None)
        if callable(clear):
            clear()


def _render_my_reviews(
    api: AuthAPI, token: str, rawg_key: str | None
) -> None:
    st.title("Minhas Reviews")
    if st.button("Voltar ao início", key="voltar_minhas_reviews"):
        st.session_state["pagina"] = "inicio"
        st.rerun()

    try:
        reviews = api.my_reviews(token)
    except AuthAPIError as error:
        st.error(error.message)
        return

    if not reviews:
        st.info("Você ainda não avaliou nenhum jogo.")
        return

    for index, review in enumerate(reviews):
        game_name = review.get("nome_jogo")
        if not isinstance(game_name, str) or not game_name.strip():
            continue

        cover_url = None
        if rawg_key:
            try:
                cover_url = buscar_capa_jogo_rawg(rawg_key, game_name.strip())
            except (requests.RequestException, ValueError):
                st.warning(f"Não foi possível carregar a capa de {game_name}.")
        cover_url = cover_url or _placeholder_data_uri(game_name.strip(), kind="game")

        with st.container(border=True):
            cover_col, review_col = st.columns([1, 4])
            with cover_col:
                st.image(
                    cover_url,
                    alt=f"Capa de {game_name}",
                    width=100,
                )
            with review_col:
                st.subheader(game_name)
                st.caption(f"Nota: {review.get('nota', '—')} / 5")
                st.write(review.get("comentario", ""))
            _render_review_date(review)


def _render_authenticated(
    api: AuthAPI, token: str, rawg_key: str | None
) -> None:
    cached_user = st.session_state.get("user_profile")
    if isinstance(cached_user, dict) and cached_user:
        user = dict(cached_user)
    else:
        try:
            user = api.current_user(token)
        except AuthAPIError as error:
            if error.code == "unauthenticated":
                st.session_state.pop("auth_token", None)
                st.warning(error.message)
            else:
                st.error(error.message)
                return
            _render_auth_forms(api)
            return

    user.update(st.session_state.get("user_profile", {}))
    nome_utilizador = user.get('name') or user.get('email') or 'Jogador'

    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.title("Menu GGReviews")
        if st.button("Sair", width="stretch", type="primary"):
            st.session_state.pop("auth_token", None)
            st.rerun()

        avatar = _url_imagem_perfil(user.get("img_perfil"), api)
        avatar_col, greeting_col = st.columns([1, 4])
        with avatar_col:
            st.image(
                avatar,
                alt=f"Foto de perfil de {nome_utilizador}",
                width=40,
            )
        with greeting_col:
            st.write(f"Olá, **{nome_utilizador}**!")
        st.divider()

        if st.button("🏠 Início", width="stretch"):
            st.session_state["pagina"] = "inicio"
            st.session_state.pop("jogo_selecionado", None)
            st.rerun()
        if st.button("📝 Minhas Reviews", width="stretch"):
            st.session_state["pagina"] = "minhas_reviews"
            st.session_state.pop("jogo_selecionado", None)
            st.rerun()
        if st.button("⚙️ Configurações", width="stretch"):
            st.session_state["pagina"] = "configuracoes"
            st.rerun()

    jogo_selecionado = st.session_state.get("jogo_selecionado")
    if st.session_state.get("pagina") == "configuracoes":
        _render_profile_settings(api, token, user)
        return
    if st.session_state.get("pagina") == "minhas_reviews":
        _render_my_reviews(api, token, rawg_key)
        return
    if isinstance(jogo_selecionado, dict):
        _render_game_review(api, token, rawg_key, jogo_selecionado)
        game_name = jogo_selecionado.get("name")
        if isinstance(game_name, str) and game_name:
            _render_game_comments(api, token, game_name)
        return

    st.write("Aqui você encontra os destaques e as últimas avaliações da comunidade.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Jogos Registrados", value="152")
    with col2:
        st.metric(label="Suas Avaliações", value="0")
    with col3:
        st.metric(label="Jogadores Ativos", value="34")

    st.divider()

    # --- FEED DE JOGOS (Via API RAWG) ---
    st.write("### Catálogo de Jogos")

    if rawg_key:
        # 1. Barra de pesquisa
        pesquisa = st.text_input("🔍 Procure um jogo para avaliar:", placeholder="Ex: The Last of Us, FIFA, Mario...")

        # 2. Busca os jogos baseados na pesquisa
        lista_de_jogos = buscar_jogos_rawg(rawg_key, pesquisa)

        if not lista_de_jogos:
            st.warning("Nenhum jogo encontrado com esse nome.")

        col_esquerda, col_direita = st.columns(2)

        for index, jogo in enumerate(lista_de_jogos):
            coluna_atual = col_esquerda if index % 2 == 0 else col_direita

            with coluna_atual:
                with st.container(border=True):
                    # Exibe a imagem de capa
                    cover_url = _url_capa_jogo(jogo)
                    st.image(
                        cover_url,
                        alt=f"Capa de {jogo.get('name', 'jogo')}",
                        width="stretch",
                    )

                    nome = jogo.get("name", "Desconhecido")
                    st.subheader(nome)

                    # Formatar data de lançamento
                    data_completa = jogo.get("released", "")
                    ano = data_completa.split("-")[0] if data_completa else "N/D"

                    nota = jogo.get("rating", "0.0")

                    plataformas = _game_platforms(jogo)
                    if plataformas:
                        st.caption(plataformas)

                    st.caption(f"📅 Lançamento: {ano}")
                    st.write(f"⭐ Nota global: **{nota} / 5.0**")

                    if st.button(
                        "Fazer Avaliação",
                        key=f"btn_avaliar_{jogo.get('id', index)}",
                        width="stretch",
                    ):
                        st.session_state["jogo_selecionado"] = jogo
                        st.rerun()
    else:
        st.error("Chave da API RAWG não configurada no secrets.toml.")

    st.divider()
    st.write("### Últimas Avaliações")
    st.info("Nenhuma avaliação encontrada. Seja o primeiro a avaliar um jogo!")


def main() -> None:
    st.set_page_config(
        page_title="GGReviews",
        page_icon="🎮",
        initial_sidebar_state="collapsed",
    )
    _apply_gamer_background()
    _capture_password_reset_link()

    if "auth_token" not in st.session_state:
        st.title("GGReviews")

    try:
        secrets = dict(st.secrets)
    except StreamlitSecretNotFoundError:
        secrets = {}

    try:
        config = load_auth_config(secrets=secrets)
    except ConfigurationError as error:
        st.error(str(error))
        st.stop()

    api = AuthAPI(config.api_base_url)
    if notice := st.session_state.pop("auth_notice", None):
        st.success(notice)

    reset_link = st.session_state.get("password_reset_link")
    if isinstance(reset_link, dict):
        _render_password_reset(api, reset_link)
        return
    if reset_link is None and "password_reset_link" in st.session_state:
        st.error("Link de recuperação inválido. Solicite um novo link.")
        st.session_state.pop("password_reset_link", None)
        return

    token = st.session_state.get("auth_token")
    previous_token = st.session_state.get("_last_auth_token")
    if token != previous_token:
        _clear_cached_rawg_data()
        st.session_state["_last_auth_token"] = token

    if isinstance(token, str) and token:
        rawg_key = secrets.get("RAWG_API_KEY") or os.environ.get("RAWG_API_KEY")
        _render_authenticated(api, token, rawg_key)
    else:
        st.session_state.pop("auth_token", None)
        _render_auth_forms(api)


if __name__ == "__main__":
    main()