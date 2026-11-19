from __future__ import annotations

import base64
import colorsys
import json
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from html import escape as escape_html
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageOps
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

from ggreviews.auth_client import (
    AuthAPI,
    AuthAPIError,
    GameRatingAverage,
    email_validation_error,
    password_policy_error,
)
from ggreviews.config import ConfigurationError, load_auth_config
from ggreviews.cheapshark_client import (
    fetch_promotions,
    fetch_store_names,
    fetch_usd_to_brl_rate,
    promotion_url,
)
from ggreviews.game_compatibility import (
    default_preferences,
    normalize_preferences,
    recommend_games,
)
from ggreviews.steam_client import fetch_brazilian_game_description

FEATURED_COVER_SIZE = (600, 338)
FEATURED_COVER_HOSTS = frozenset(
    {
        "cdn.fanatical.com",
        "cdn.humblebundle.com",
        "cdn.cloudflare.steamstatic.com",
        "images.cheapshark.com",
        "images.gog-statics.com",
        "images.greenmangaming.com",
        "images.igdb.com",
        "shared.akamai.steamstatic.com",
        "shared.fastly.steamstatic.com",
        "sttc.gamersgate.com",
        "steamcdn-a.akamaihd.net",
    }
)


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
        submitted = st.form_submit_button(
            "Salvar nova senha",
            type="primary",
            width="stretch",
        )

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
        submitted = st.form_submit_button(
            "Criar conta",
            type="primary",
            width="stretch",
        )

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
        submitted = st.form_submit_button(
            "Entrar",
            type="primary",
            width="stretch",
        )

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
        submitted = st.form_submit_button(
            "Enviar link de recuperação",
            type="primary",
            width="stretch",
        )

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
    st.markdown(
        """
        <style>
        .st-key-auth-screen {
            min-height: calc(100vh - 3.5rem);
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .st-key-auth-brand {
            position: absolute;
            top: 0.5rem;
            left: 50%;
            width: max-content;
            max-width: calc(100vw - 2rem);
            transform: translateX(-50%);
        }
        .auth-brand-logo {
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            line-height: 1;
        }
        .auth-brand-accent {
            color: #f43f5e;
        }
        .st-key-auth-panel {
            width: min(544px, calc(100vw - 2rem)) !important;
            padding: 0.75rem 1rem 1rem !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 14px !important;
            background: rgba(31, 35, 54, 0.68) !important;
            backdrop-filter: blur(16px);
        }
        .st-key-auth-panel [data-testid="stForm"] {
            border: 0;
            background: transparent;
            padding: 0;
        }
        .st-key-auth-panel [data-testid="stTextInput"] input {
            border: 1px solid rgba(203, 213, 225, 0.32);
            border-radius: 10px;
            background: rgba(10, 13, 28, 0.76);
        }
        .st-key-auth-panel [data-testid="stTextInput"] input:focus {
            border-color: rgba(255, 255, 255, 0.58);
            box-shadow: 0 0 0 1px rgba(244, 63, 94, 0.32);
        }
        .st-key-auth-panel [data-testid="stFormSubmitButton"] button {
            width: 100%;
            min-height: 3rem;
            border: 0;
            border-radius: 999px;
            background: linear-gradient(90deg, #a20d32, #f12640);
            color: #fff;
            font-weight: 700;
        }
        .st-key-auth-panel [data-testid="stFormSubmitButton"] button:hover {
            background: linear-gradient(90deg, #ba123c, #ff344d);
            color: #fff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="auth-screen"):
        with st.container(key="auth-brand"):
            st.markdown(
                '<div class="auth-brand-logo">GG'
                '<span class="auth-brand-accent">Reviews</span></div>',
                unsafe_allow_html=True,
            )
        with st.container(width=544, border=True, key="auth-panel"):
            login_tab, signup_tab, recovery_tab = st.tabs(
                ["Entrar", "Criar conta", "Recuperar senha"]
            )
            with login_tab:
                _render_login(api)
            with signup_tab:
                _render_signup(api)
            with recovery_tab:
                _render_recovery(api)


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
        <svg xmlns='http://www.w3.org/2000/svg' width='480' height='640' viewBox='0 0 480 640'>
          <defs>
            <linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'>
              <stop offset='0%' stop-color='#111827'/>
              <stop offset='100%' stop-color='#7c3aed'/>
            </linearGradient>
          </defs>
          <rect width='480' height='640' rx='28' fill='url(#g)'/>
          <circle cx='100' cy='150' r='84' fill='rgba(255,255,255,0.08)'/>
          <circle cx='390' cy='490' r='92' fill='rgba(34,211,238,0.12)'/>
          <text x='240' y='330' text-anchor='middle' font-family='Arial, sans-serif' font-size='88' font-weight='800' fill='white'>{initials}</text>
          <text x='240' y='380' text-anchor='middle' font-family='Arial, sans-serif' font-size='20' fill='rgba(255,255,255,0.8)'>{safe_label[:18]}</text>
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
    cover_url = game.get("background_image") or game.get("thumb")
    if isinstance(cover_url, str) and cover_url:
        return cover_url
    return _placeholder_data_uri(game.get("name") or "Jogo", kind="game")


def _render_game_card_cover(game: dict[str, Any]) -> None:
    game_name = str(game.get("name") or "Jogo")
    st.image(
        _url_capa_jogo(game),
        alt=f"Capa de {game_name}",
        width=300,
    )


def _normalize_featured_game_cover(
    image_bytes: bytes,
    size: tuple[int, int] = FEATURED_COVER_SIZE,
) -> bytes:
    with Image.open(BytesIO(image_bytes)) as source:
        image = ImageOps.pad(
            ImageOps.exif_transpose(source).convert("RGB"),
            size,
            method=Image.Resampling.LANCZOS,
            color="#101522",
        )
    output = BytesIO()
    image.save(output, format="JPEG", quality=88)
    return output.getvalue()


@st.cache_data(ttl=86400, max_entries=256)
def _load_featured_game_cover(
    url: str,
    size: tuple[int, int],
    allowed_hosts: tuple[str, ...],
) -> bytes | None:
    parsed_url = urlsplit(url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in allowed_hosts
        or parsed_url.port not in (None, 443)
    ):
        return None

    response = requests.get(
        url,
        headers={"User-Agent": "GGReviews/1.0"},
        timeout=8,
        allow_redirects=False,
    )
    response.raise_for_status()
    return _normalize_featured_game_cover(response.content, size)


def _featured_game_cover_placeholder() -> bytes:
    image = Image.new("RGB", FEATURED_COVER_SIZE, "#101522")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (18, 18, FEATURED_COVER_SIZE[0] - 18, FEATURED_COVER_SIZE[1] - 18),
        radius=18,
        outline="#374151",
        width=3,
    )
    draw.text(
        (FEATURED_COVER_SIZE[0] // 2, FEATURED_COVER_SIZE[1] // 2),
        "GGReviews",
        anchor="mm",
        fill="#9ca3af",
    )
    output = BytesIO()
    image.save(output, format="JPEG", quality=88)
    return output.getvalue()


def _render_featured_game_card_cover(game: dict[str, Any]) -> None:
    game_name = str(game.get("name") or "Jogo")
    try:
        image = _load_featured_game_cover(
            _url_capa_jogo(game),
            FEATURED_COVER_SIZE,
            tuple(sorted(FEATURED_COVER_HOSTS)),
        )
    except (OSError, requests.RequestException, ValueError):
        image = None

    st.image(
        image if image is not None else _featured_game_cover_placeholder(),
        alt=(
            f"Capa de {game_name}"
            if image is not None
            else f"Capa indisponível para {game_name}"
        ),
        width="stretch",
    )


def _platform_icon(platform_name: str) -> str:
    normalized_name = platform_name.casefold()
    if "xbox" in normalized_name:
        return "sports_esports"
    if "playstation" in normalized_name or re.search(r"\bps[345]\b", normalized_name):
        return "videogame_asset"
    if "nintendo" in normalized_name or "switch" in normalized_name:
        return "videogame_asset"
    if "windows" in normalized_name or normalized_name == "pc":
        return "desktop_windows"
    if "linux" in normalized_name:
        return "terminal"
    if "mac" in normalized_name:
        return "laptop_mac"
    if "android" in normalized_name or "ios" in normalized_name:
        return "smartphone"
    return "sports_esports"


def _render_game_platforms(game: dict[str, Any]) -> None:
    platforms = game.get("platforms")
    names = [
        platform["name"].strip()
        for platform in platforms
        if isinstance(platform, dict)
        and isinstance(platform.get("name"), str)
        and platform["name"].strip()
    ] if isinstance(platforms, list) else []

    if not names:
        st.caption(":material/devices: Plataformas não informadas")
        return

    platform_labels = [
        f":material/{_platform_icon(name)}: {name}" for name in names
    ]
    st.caption(" · ".join(platform_labels))


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


def _apply_gamer_background() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #090b13;
            background-image:
                radial-gradient(circle at 18% 0%, rgba(124, 58, 237, 0.14), transparent 38%),
                linear-gradient(140deg, #090b13, #111827 58%, #090b13);
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
        [data-testid="stSidebar"] [data-testid="stButton"] > button {
            min-height: 2.65rem;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: #f8fafc;
            font-weight: 600;
            text-align: left;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
            border-color: rgba(148, 163, 184, 0.4);
            background: rgba(255, 255, 255, 0.15);
        }
        .st-key-sidebar-profile {
            padding: 1.25rem 0 0.75rem;
            text-align: center;
        }
        .st-key-sidebar-profile p {
            margin-top: 0.65rem;
            font-size: 1.05rem;
            font-weight: 700;
        }
        .st-key-sidebar-logout {
            margin-top: 3rem;
            padding-top: 0.75rem;
            border-top: 1px solid rgba(148, 163, 184, 0.18);
        }
        .st-key-sidebar-logout [data-testid="stButton"] > button {
            justify-content: center;
            border-color: #ff4d55;
            background: #ff4d55;
            color: white;
        }
        .st-key-sidebar-logout [data-testid="stButton"] > button:hover {
            border-color: #ff666d;
            background: #ff666d;
        }
        [class*="st-key-home-deal-"],
        [class*="st-key-promotions-deal-"] {
            height: 100%;
            padding: 0.6rem;
            border-color: rgba(148, 163, 184, 0.22) !important;
            border-radius: 14px !important;
            background: rgba(15, 23, 42, 0.68) !important;
            box-shadow: 0 14px 32px rgba(2, 6, 23, 0.22);
        }
        .deal-card-cover {
            position: relative;
            overflow: hidden;
            width: 100%;
            aspect-ratio: 2.8 / 1;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 11px;
            background: #101522;
        }
        .deal-card-cover img {
            display: block;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .deal-card-discount {
            position: absolute;
            top: 0.45rem;
            right: 0.45rem;
            padding: 0.2rem 0.45rem;
            border-radius: 7px;
            background: #37874b;
            color: white;
            font-size: 0.85rem;
            font-weight: 800;
        }
        .deal-card-price {
            display: flex;
            align-items: baseline;
            gap: 0.45rem;
            margin: 0.2rem 0 0.35rem;
        }
        .deal-card-price strong {
            color: #f8fafc;
            font-size: 1.25rem;
        }
        .deal-card-price s {
            color: #94a3b8;
            font-size: 0.85rem;
        }
        .deal-card-rating {
            color: #e2e8f0;
            font-size: 0.82rem;
        }
        [class*="st-key-home-deal-"] [data-testid="stButton"] > button,
        [class*="st-key-home-deal-"] [data-testid="stLinkButton"] > a,
        [class*="st-key-promotions-deal-"] [data-testid="stButton"] > button,
        [class*="st-key-promotions-deal-"] [data-testid="stLinkButton"] > a {
            min-height: 2rem;
            padding: 0.25rem 0.55rem;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _extract_cover_accent_color(image_bytes: bytes) -> str | None:
    with Image.open(BytesIO(image_bytes)) as source:
        quantized = source.convert("RGB").resize((64, 64)).quantize(colors=8)

    color_counts = quantized.getcolors(64 * 64)
    palette = quantized.getpalette()
    if not color_counts or palette is None:
        return None

    vibrant_colors: list[tuple[float, tuple[int, int, int]]] = []
    for count, palette_index in color_counts:
        offset = palette_index * 3
        red, green, blue = palette[offset : offset + 3]
        saturation = colorsys.rgb_to_hsv(
            red / 255,
            green / 255,
            blue / 255,
        )[1]
        if saturation >= 0.25 and max(red, green, blue) >= 64:
            vibrant_colors.append(
                (count * saturation, (red, green, blue))
            )

    if vibrant_colors:
        red, green, blue = max(vibrant_colors, key=lambda item: item[0])[1]
    else:
        _, palette_index = max(color_counts)
        offset = palette_index * 3
        red, green, blue = palette[offset : offset + 3]
    return f"#{red:02x}{green:02x}{blue:02x}"


def _load_review_accent_color(image_url: str) -> str | None:
    cover_bytes = _load_featured_game_cover(
        image_url,
        FEATURED_COVER_SIZE,
        tuple(sorted(FEATURED_COVER_HOSTS)),
    )
    return _extract_cover_accent_color(cover_bytes) if cover_bytes else None


def _apply_review_game_background(
    image_url: str, accent_color: str | None
) -> None:
    try:
        parsed_url = urlsplit(image_url)
        is_allowed_image = (
            parsed_url.scheme == "https"
            and parsed_url.hostname in FEATURED_COVER_HOSTS
            and parsed_url.port in (None, 443)
            and re.fullmatch(
                r"https://[A-Za-z0-9._:/?&=+%-]+",
                image_url,
            )
            is not None
        )
    except ValueError:
        is_allowed_image = False
    background_image = (
        f", url({json.dumps(image_url)})" if is_allowed_image else ""
    )
    color = (
        accent_color
        if isinstance(accent_color, str)
        and re.fullmatch(r"#[0-9a-fA-F]{6}", accent_color)
        else "#c084fc"
    )
    red, green, blue = (
        int(color[index : index + 2], 16)
        for index in (1, 3, 5)
    )
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-color: #090b13;
            background-image:
                linear-gradient(180deg, rgba(8, 10, 16, 0.35), rgba(8, 10, 16, 0.84) 72%, #090b13),
                linear-gradient(90deg, rgba(8, 10, 16, 0.64), rgba(8, 10, 16, 0.24)){background_image};
            background-size: cover;
            background-position: center 18%;
            background-attachment: fixed;
            isolation: isolate;
        }}
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            background: linear-gradient(
                180deg,
                rgba(8, 10, 16, 0.08),
                rgba(8, 10, 16, 0.30) 55%,
                rgba(9, 11, 19, 0.96)
            );
        }}
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stAppViewContainer"] > header {{
            position: relative;
            z-index: 1;
        }}
        .st-key-review-rating-card,
        .st-key-review-description-card {{
            background: rgba(18, 22, 31, 0.85) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            backdrop-filter: blur(12px);
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.18);
        }}
        .st-key-review-poster [data-testid="stImage"] img {{
            box-shadow: 0 16px 42px rgba({red}, {green}, {blue}, 0.38);
        }}
        .game-metadata-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.75rem 0 1rem;
        }}
        .game-metadata-badge {{
            display: inline-flex;
            align-items: center;
            max-width: 100%;
            padding: 0.38rem 0.7rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.82);
            color: #f3f4f6;
            font-size: 0.82rem;
            line-height: 1.2;
        }}
        .game-metadata-badge--blue {{ border-color: rgba(96, 165, 250, 0.42); }}
        .game-metadata-badge--violet {{ border-color: rgba(192, 132, 252, 0.42); }}
        .game-metadata-badge--green {{ border-color: rgba(74, 222, 128, 0.42); }}
        .game-metadata-badge--orange {{ border-color: rgba(251, 146, 60, 0.42); }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=21600, max_entries=128, show_spinner=False)
def _load_brazilian_game_description(game_name: str) -> str | None:
    return fetch_brazilian_game_description(game_name)


def _step_review_media(state_key: str, step: int, item_count: int) -> None:
    if item_count <= 0:
        return
    current_index = st.session_state.get(state_key, 0)
    if isinstance(current_index, bool) or not isinstance(current_index, int):
        current_index = 0
    st.session_state[state_key] = (current_index + step) % item_count


def _review_media_items(
    game: dict[str, Any], game_name: str
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    seen_screenshots: set[str] = set()
    screenshots = game.get("screenshots")
    if isinstance(screenshots, list):
        for screenshot in screenshots:
            if len(seen_screenshots) >= 5:
                break
            image_id = (
                screenshot.get("image_id")
                if isinstance(screenshot, dict)
                else None
            )
            if (
                not isinstance(image_id, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]+", image_id)
                or image_id in seen_screenshots
            ):
                continue
            seen_screenshots.add(image_id)
            items.append(
                {
                    "type": "image",
                    "url": (
                        "https://images.igdb.com/igdb/image/upload/"
                        f"t_screenshot_big/{image_id}.jpg"
                    ),
                    "label": f"Imagem {len(seen_screenshots)}",
                    "alt": f"{game_name}, imagem {len(seen_screenshots)}",
                }
            )

    videos = game.get("videos")
    if isinstance(videos, list):
        for video in videos:
            video_id = video.get("video_id") if isinstance(video, dict) else None
            if (
                not isinstance(video_id, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id)
            ):
                continue
            video_name = video.get("name")
            label = video_name.strip() if isinstance(video_name, str) else ""
            items.append(
                {
                    "type": "video",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "label": label or "Trailer",
                    "alt": f"Trailer de {game_name}",
                }
            )
            break
    return items


def _render_review_media_carousel(
    game: dict[str, Any], game_name: str, game_id: Any
) -> None:
    items = _review_media_items(game, game_name)
    if not items:
        st.caption("Imagens e trailer não disponíveis para este jogo.")
        return

    safe_game_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(game_id or game_name))
    state_key = f"review_media_index_{safe_game_id}"
    current_index = st.session_state.get(state_key, 0)
    if isinstance(current_index, bool) or not isinstance(current_index, int):
        current_index = 0
    current_index %= len(items)
    st.session_state[state_key] = current_index
    current_item = items[current_index]

    with st.container(border=True):
        st.subheader("Imagens e trailer")
        if current_item["type"] == "video":
            st.video(current_item["url"], alt=current_item["alt"])
        else:
            st.image(
                current_item["url"],
                alt=current_item["alt"],
                width="stretch",
            )
        previous_column, status_column, next_column = st.columns(
            [1, 2, 1],
            vertical_alignment="center",
        )
        previous_column.button(
            "Anterior",
            key=f"{state_key}_previous",
            disabled=len(items) <= 1,
            on_click=_step_review_media,
            args=(state_key, -1, len(items)),
        )
        status_column.caption(
            f"{current_item['label']} · {current_index + 1} de {len(items)}"
        )
        next_column.button(
            "Próxima",
            key=f"{state_key}_next",
            disabled=len(items) <= 1,
            on_click=_step_review_media,
            args=(state_key, 1, len(items)),
        )


_GAME_METADATA_TRANSLATIONS = {
    "action": "Ação",
    "adventure": "Aventura",
    "fighting": "Luta",
    "indie": "Independente",
    "music": "Música",
    "platform": "Plataforma",
    "puzzle": "Quebra-cabeça",
    "racing": "Corrida",
    "role-playing (rpg)": "RPG",
    "shooter": "Tiro",
    "simulator": "Simulação",
    "sport": "Esporte",
    "strategy": "Estratégia",
    "open world": "Mundo aberto",
    "pc (microsoft windows)": "PC",
    "playstation 5": "PS5",
    "xbox series x|s": "Xbox Series X|S",
    "xbox series x": "Xbox Series X|S",
    "xbox series s": "Xbox Series X|S",
    "playstation 4": "PS4",
}


def _igdb_metadata_names(game: dict[str, Any], field: str) -> list[str]:
    values = game.get(field)
    if not isinstance(values, list):
        return []
    names: list[str] = []
    for item in values:
        name = item.get("name") if isinstance(item, dict) else None
        if isinstance(name, str) and name.strip():
            localized_name = _GAME_METADATA_TRANSLATIONS.get(
                name.strip().casefold(),
                name.strip(),
            )
            if localized_name not in names:
                names.append(localized_name)
    return names


def _game_review_metadata(game: dict[str, Any]) -> list[tuple[str, str]]:
    badges: list[tuple[str, str]] = []
    platforms = _igdb_metadata_names(game, "platforms")
    if platforms:
        badges.append((f"Plataformas: {', '.join(platforms[:4])}", "blue"))

    genres = _igdb_metadata_names(game, "genres")
    if genres:
        badges.append((f"Gênero: {', '.join(genres[:4])}", "violet"))

    themes = _igdb_metadata_names(game, "themes")
    if themes:
        badges.append((f"Estilo: {', '.join(themes[:3])}", "violet"))

    involved_companies = game.get("involved_companies")
    if isinstance(involved_companies, list):
        developers: list[str] = []
        for involved_company in involved_companies:
            if (
                not isinstance(involved_company, dict)
                or involved_company.get("developer") is not True
            ):
                continue
            company = involved_company.get("company")
            developer_name = (
                company.get("name") if isinstance(company, dict) else None
            )
            if (
                isinstance(developer_name, str)
                and developer_name.strip()
                and developer_name.strip() not in developers
            ):
                developers.append(developer_name.strip())
        if developers:
            badges.append(
                (f"Desenvolvedora: {', '.join(developers[:2])}", "green")
            )

    release_timestamp = game.get("first_release_date")
    if (
        isinstance(release_timestamp, (int, float))
        and not isinstance(release_timestamp, bool)
    ):
        try:
            release_year = datetime.fromtimestamp(
                release_timestamp,
                timezone.utc,
            ).year
        except (OSError, OverflowError, ValueError):
            release_year = None
        if release_year is not None:
            badges.append((f"Lançamento: {release_year}", "orange"))

    return badges


def _render_game_review_metadata(game: dict[str, Any]) -> None:
    badges = _game_review_metadata(game)
    if not badges:
        return
    rendered_badges = "".join(
        '<span class="game-metadata-badge '
        f'game-metadata-badge--{tone}">{escape_html(label)}</span>'
        for label, tone in badges
    )
    st.markdown(
        f'<div class="game-metadata-badges">{rendered_badges}</div>',
        unsafe_allow_html=True,
    )


def _render_game_review(
    api: AuthAPI, token: str, game: dict[str, Any]
) -> None:
    game_name = str(game.get("name") or "Jogo")
    game_id = game.get("id")
    safe_game_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(game_id or game_name))

    if st.button("Voltar ao início", key="voltar_inicio"):
        st.session_state.pop("jogo_selecionado", None)
        st.rerun()

    st.title(game_name)
    ratings = _load_game_rating_averages(api, token, [game_name])
    review_media_game = game
    try:
        review_media_game = _load_review_game_media(game)
    except (requests.RequestException, ValueError) as error:
        st.warning(
            "Não foi possível carregar as imagens e o trailer do jogo: "
            f"{error}"
        )

    cover_source = (
        review_media_game
        if isinstance(review_media_game.get("background_image"), str)
        else game
    )
    cover_url = _url_capa_jogo(cover_source)
    background_art_url = (
        review_media_game.get("artwork_image")
        if isinstance(review_media_game.get("artwork_image"), str)
        else cover_url
    )
    accent_color = None
    accent_error = False
    try:
        accent_color = _load_review_accent_color(background_art_url)
    except (requests.RequestException, OSError, ValueError):
        accent_error = True
    _apply_review_game_background(background_art_url, accent_color)
    if accent_color is None:
        st.caption(
            "Não foi possível extrair a paleta da arte; usando uma cor de "
            "destaque padrão."
            if accent_error
            else "A paleta da arte não está disponível; usando uma cor de "
            "destaque padrão."
        )

    _render_game_review_metadata(review_media_game)
    _render_xray_badge(
        game_name,
        key=f"review_xray_{safe_game_id}",
        origin="review",
    )

    cover_column, details_column = st.columns([1, 2])
    with cover_column:
        with st.container(key="review-poster"):
            st.image(cover_url, alt=f"Capa de {game_name}", width="stretch")
    with details_column:
        _render_game_rating(
            game_name,
            ratings,
            label="Nota atual no site",
            show_stars=True,
            container_key="review-rating-card",
        )
        try:
            summary = _load_brazilian_game_description(game_name)
        except (requests.RequestException, ValueError) as error:
            st.warning(
                "Não foi possível carregar a descrição localizada da Steam: "
                f"{error}"
            )
            summary = None
        with st.container(
            border=True,
            key="review-description-card",
        ):
            st.subheader("Sobre o jogo")
            if summary:
                st.write(
                    f"{summary[:400].rstrip()}"
                    f"{'…' if len(summary) > 400 else ''}"
                )
            else:
                original_summary = game.get("summary")
                if (
                    not isinstance(original_summary, str)
                    or not original_summary.strip()
                ):
                    original_summary = review_media_game.get("summary")
                if isinstance(original_summary, str) and original_summary.strip():
                    st.caption("Sinopse original em inglês")
                    st.write(
                        f"{original_summary[:400].rstrip()}"
                        f"{'…' if len(original_summary) > 400 else ''}"
                    )
                else:
                    st.caption("Sinopse indisponível.")

    _render_review_media_carousel(
        review_media_game,
        game_name,
        game_id,
    )

    st.divider()
    st.subheader("Sua avaliação")
    with st.form(f"review_{safe_game_id}"):
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

    if submitted:
        if not review_text.strip():
            st.error("Escreva um comentário antes de enviar sua avaliação.")
        else:
            try:
                api.create_review(
                    token,
                    game_name=game_name,
                    rating=rating,
                    review_text=review_text,
                )
            except AuthAPIError as error:
                st.error(error.message)
            else:
                st.session_state["auth_notice"] = "Sua avaliação foi enviada."
                st.rerun()

    cheapest = game.get("cheapest")
    if isinstance(cheapest, Decimal):
        try:
            rate, rate_date = buscar_cotacao_usd_brl()
            st.metric(
                "Menor preço encontrado",
                _format_brl_price(cheapest, rate),
            )
            st.caption(
                f"Cotação de referência: US$ 1 = {_format_brl_price(Decimal('1'), rate)} "
                f"({rate_date:%d/%m/%Y}). Valor aproximado."
            )
        except (requests.RequestException, ValueError):
            st.error("Não foi possível converter o preço para reais.")
        cheapest_deal_id = game.get("cheapest_deal_id")
        if isinstance(cheapest_deal_id, str) and cheapest_deal_id:
            st.link_button(
                "Ver menor oferta",
                promotion_url(cheapest_deal_id),
            )


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


@st.cache_data(ttl=900, max_entries=1)
def buscar_ofertas_cheapshark() -> list[dict[str, Any]]:
    return fetch_promotions()


@st.cache_data(ttl=86400, max_entries=1)
def buscar_lojas_cheapshark() -> dict[str, str]:
    return fetch_store_names()


@st.cache_data(ttl=3600, max_entries=1)
def buscar_cotacao_usd_brl() -> tuple[Decimal, date]:
    return fetch_usd_to_brl_rate()


def _buscar_jogos_igdb_por_query(query: str) -> list[dict[str, Any]]:
    load_dotenv(Path(__file__).resolve().with_name(".env"))
    client_id = os.getenv("TWITCH_CLIENT_ID", "").strip()
    client_secret = os.getenv("TWITCH_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise ValueError(
            "Defina TWITCH_CLIENT_ID e TWITCH_CLIENT_SECRET no ficheiro .env."
        )

    token_response = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
        timeout=15,
    )
    token_response.raise_for_status()
    token_payload = token_response.json()
    access_token = (
        token_payload.get("access_token") if isinstance(token_payload, dict) else None
    )
    if not isinstance(access_token, str) or not access_token:
        raise ValueError("A Twitch não retornou um Access Token válido.")

    games_response = requests.post(
        "https://api.igdb.com/v4/games",
        headers={
            "Client-ID": client_id,
            "Authorization": f"Bearer {access_token}",
        },
        data=query,
        timeout=15,
    )
    games_response.raise_for_status()
    games_payload = games_response.json()
    if not isinstance(games_payload, list):
        raise ValueError("A resposta do IGDB não contém uma lista de jogos.")
    return [game for game in games_payload if isinstance(game, dict)]


@st.cache_data(ttl=3600, max_entries=128)
def buscar_jogos_igdb(termo_busca: str) -> list[dict[str, Any]]:
    termo_busca = " ".join(termo_busca.split())
    if not termo_busca:
        return []

    termo_escapado = termo_busca.replace("\\", "\\\\").replace('"', '\\"')
    query = (
        f'search "{termo_escapado}"; '
        "fields id,name,slug,cover.image_id,artworks.image_id,screenshots.image_id,"
        "videos.video_id,videos.name,first_release_date,summary,"
        "genres.name,themes.name,game_modes.name,platforms.name,"
        "involved_companies.company.name,involved_companies.developer; "
        "limit 20;"
    )
    games_payload = _buscar_jogos_igdb_por_query(query)

    games: list[dict[str, Any]] = []
    for game in games_payload:
        if not isinstance(game, dict) or not isinstance(game.get("name"), str):
            continue
        cover = game.get("cover")
        image_id = cover.get("image_id") if isinstance(cover, dict) else None
        artworks = game.get("artworks")
        artwork_id = None
        if isinstance(artworks, list):
            artwork_id = next(
                (
                    artwork.get("image_id")
                    for artwork in artworks
                    if isinstance(artwork, dict)
                    and isinstance(artwork.get("image_id"), str)
                    and re.fullmatch(r"[A-Za-z0-9_-]+", artwork["image_id"])
                ),
                None,
            )
        normalized_game = {
            **game,
            "screenshots": (
                game.get("screenshots")
                if isinstance(game.get("screenshots"), list)
                else []
            ),
            "videos": (
                game.get("videos")
                if isinstance(game.get("videos"), list)
                else []
            ),
            "background_image": (
                f"https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"
                if isinstance(image_id, str) and image_id
                else None
            ),
        }
        if isinstance(artwork_id, str):
            normalized_game["artwork_image"] = (
                "https://images.igdb.com/igdb/image/upload/"
                f"t_1080p/{artwork_id}.jpg"
            )
        games.append(normalized_game)
    return games


def _load_review_game_media(game: dict[str, Any]) -> dict[str, Any]:
    if "screenshots" in game and "videos" in game:
        return game

    game_name = game.get("name")
    if not isinstance(game_name, str) or not game_name.strip():
        return game

    normalized_name = re.sub(r"[\W_]+", "", game_name.casefold())
    edition_base = re.sub(
        r"\s*:\s*.*\bedition\b.*$",
        "",
        game_name,
        flags=re.IGNORECASE,
    ).strip()
    search_titles = [game_name.strip()]
    if edition_base and edition_base.casefold() != game_name.strip().casefold():
        search_titles.append(edition_base)

    for search_title in search_titles:
        normalized_search_title = re.sub(r"[\W_]+", "", search_title.casefold())
        for candidate in buscar_jogos_igdb(search_title):
            candidate_name = candidate.get("name")
            if not isinstance(candidate_name, str):
                continue
            normalized_candidate = re.sub(r"[\W_]+", "", candidate_name.casefold())
            if (
                normalized_candidate != normalized_name
                and normalized_candidate != normalized_search_title
            ):
                continue

            resolved_game = {**game, **candidate}
            resolved_game["id"] = game.get("id", candidate.get("id"))
            resolved_game["name"] = game_name
            return resolved_game
    return game


@st.cache_data(ttl=21600, max_entries=1)
def buscar_catalogo_compatibilidade_igdb() -> dict[str, Any]:
    games = _buscar_jogos_igdb_por_query(
        "fields id,name,slug,summary,cover.image_id,genres.name,themes.name,"
        "game_modes.name,platforms.name; "
        "where rating_count > 10 & cover != null; "
        "sort rating_count desc; "
        "limit 500;"
    )
    catalog_games: list[dict[str, Any]] = []
    vocabulary: dict[str, set[str]] = {
        "generos": set(),
        "estilos": set(),
        "modos": set(),
        "plataformas": set(),
    }

    for game in games:
        title = game.get("name")
        if not isinstance(title, str) or not title.strip():
            continue

        cover = game.get("cover")
        image_id = cover.get("image_id") if isinstance(cover, dict) else None
        traits: dict[str, list[str]] = {}
        for field, source_field in (
            ("generos", "genres"),
            ("estilos", "themes"),
            ("modos", "game_modes"),
            ("plataformas", "platforms"),
        ):
            source_values = game.get(source_field)
            values = list(
                dict.fromkeys(
                    item["name"].strip()
                    for item in source_values
                    if isinstance(item, dict)
                    and isinstance(item.get("name"), str)
                    and item["name"].strip()
                )
            ) if isinstance(source_values, list) else []
            traits[field] = values
            vocabulary[field].update(values)

        slug = game.get("slug")
        catalog_games.append(
            {
                "id": game.get("id"),
                "slug": slug if isinstance(slug, str) else str(game.get("id")),
                "titulo": title.strip(),
                "descricao": game.get("summary")
                if isinstance(game.get("summary"), str)
                else "",
                **traits,
                "url_capa": (
                    f"https://images.igdb.com/igdb/image/upload/"
                    f"t_cover_big/{image_id}.jpg"
                    if isinstance(image_id, str) and image_id
                    else None
                ),
                "fonte_url": (
                    f"https://www.igdb.com/games/{slug}"
                    if isinstance(slug, str) and slug
                    else None
                ),
            }
        )

    return {
        "jogos": catalog_games,
        "vocabulario": {
            field: sorted(values, key=str.casefold)
            for field, values in vocabulary.items()
        },
    }


@st.cache_data(ttl=3600, max_entries=256)
def buscar_capa_jogo_igdb(nome_jogo: str) -> str | None:
    jogos = buscar_jogos_igdb(nome_jogo)
    nome_normalizado = nome_jogo.strip().casefold()
    jogo = next(
        (item for item in jogos if item["name"].casefold() == nome_normalizado),
        jogos[0] if jogos else None,
    )
    cover = jogo.get("background_image") if jogo else None
    return cover if isinstance(cover, str) else None


def _format_brl_price(price_usd: Decimal, rate: Decimal) -> str:
    price_brl = (price_usd * rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    whole_reais, cents = f"{price_brl:.2f}".split(".")
    formatted_reais = f"{int(whole_reais):,}".replace(",", ".")
    return f"R$ {formatted_reais},{cents}"


def _render_exchange_rate(rate: Decimal, rate_date: date) -> None:
    st.caption(
        f"Cotação de referência: US$ 1 = {_format_brl_price(Decimal('1'), rate)} "
        f"({rate_date:%d/%m/%Y}). Os valores são aproximados; "
        "o preço final pode variar na loja."
    )


def _open_xray(game_title: str, *, origin: str) -> None:
    st.session_state["raiox_jogo"] = game_title.strip()
    st.session_state["raiox_origem"] = origin
    st.session_state["pagina"] = "raiox"
    st.rerun()


def _render_xray_badge(
    game_title: str,
    *,
    key: str,
    origin: str,
) -> None:
    if st.button(
        "Ver Raio-X técnico",
        key=key,
        type="tertiary",
        icon=":material/info:",
        help=(
            "Raio-X técnico sem dados cadastrados. Isso não significa que o jogo "
            "seja livre de DRM, launcher ou problemas de stuttering. Clique para "
            "ver os critérios e a metodologia."
        ),
    ):
        _open_xray(game_title, origin=origin)


def _load_game_rating_averages(
    api: AuthAPI,
    token: str,
    game_names: list[str],
) -> dict[str, GameRatingAverage] | None:
    if not game_names:
        return {}
    try:
        return api.game_rating_averages(token, game_names)
    except AuthAPIError as error:
        st.warning(
            "As médias da comunidade estão indisponíveis no momento. "
            f"{error.message}"
        )
        return None


def _render_game_rating(
    game_name: str,
    averages: dict[str, GameRatingAverage] | None,
    *,
    label: str = "Média da comunidade",
    show_stars: bool = False,
    container_key: str | None = None,
) -> None:
    with st.container(border=True, key=container_key):
        st.markdown(f":material/star: **{label}**")
        if averages is None:
            st.caption("Média indisponível no momento.")
            return
        rating = averages.get(game_name.strip().casefold())
        if rating is None:
            st.caption("Ainda sem avaliações. Seja o primeiro!")
            return

        formatted_average = f"{rating.average:.1f}".replace(".", ",")
        st.markdown(f"## {formatted_average} / 5")
        if show_stars:
            filled_stars = int(
                rating.average.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            )
            st.markdown(f":orange[{'★' * filled_stars}{'☆' * (5 - filled_stars)}]")
        review_label = "avaliação" if rating.total == 1 else "avaliações"
        st.caption(f"{rating.total} {review_label} da comunidade")


def _render_xray_details(game_title: str) -> None:
    st.subheader(game_title)
    st.warning(
        "Ainda não há uma avaliação técnica cadastrada para este jogo. "
        "A ausência de alertas não significa que ele seja livre de DRM, launcher "
        "secundário ou stuttering."
    )
    st.caption("Selo geral: Não avaliado · Confiança: Sem dados ainda")
    st.caption("Última verificação: Ainda não verificado; nenhuma data registrada.")
    st.caption("Versão/patch: Sem dados · Fonte geral: Nenhuma evidência cadastrada.")

    criteria = [
        {
            "title": "Conta de terceiros / launcher secundário",
            "states": "Não exige · Exige login opcional · Exige conta/launcher",
            "description": (
                "Verifica se é necessário criar uma conta externa ou instalar um "
                "launcher além da loja onde o jogo foi comprado."
            ),
            "extra": "Launcher exigido: Sem dados.",
        },
        {
            "title": "DRM / Sempre online",
            "states": "Funciona offline · Exige verificação periódica · Sempre online",
            "description": (
                "Verifica o funcionamento sem internet, inclusive em campanhas "
                "single-player, e se há checagens periódicas de licença."
            ),
            "extra": "Tipo de DRM: Sem dados.",
        },
        {
            "title": "Compilação de shaders / stuttering",
            "states": "Pré-compila no início · Engasgos leves · Engasgos frequentes",
            "description": (
                "Observa travamentos durante aproximadamente os primeiros "
                "30 minutos de jogo no PC."
            ),
            "extra": (
                "Método, fonte dos relatos e observações de hardware: Sem dados."
            ),
        },
    ]

    for criterion in criteria:
        with st.container(border=True):
            st.markdown(f"**{criterion['title']}**")
            st.caption("Estado: Sem dados ainda")
            st.write(criterion["description"])
            st.caption(f"Estados possíveis: {criterion['states']}")
            st.caption(criterion["extra"])
            st.caption(
                "Confiança: Sem dados ainda · Última verificação: Ainda não verificado."
            )
            st.caption(
                "Evidência/fonte deste critério: Nenhuma cadastrada."
            )

    with st.container(border=True):
        st.markdown("**Como interpretar o Raio-X**")
        st.write(
            "“Verificado pelo GGReviews” deve significar teste próprio com "
            "configuração e versão registradas. “Baseado em relatos da comunidade” "
            "deve incluir fontes públicas consultáveis. Sem evidências, o estado "
            "correto é sempre “Sem dados ainda”; não inferimos ausência de "
            "problemas."
        )
        st.write(
            "Uma avaliação deve ser revista após patches que alterem DRM, "
            "autenticação ou compilação de shaders, e em até 90 dias. Dados "
            "desatualizados devem ser sinalizados antes de qualquer selo voltar "
            "a ser exibido."
        )


def _render_xray_page() -> None:
    st.title("Raio-X técnico")
    game_title = st.session_state.get("raiox_jogo")
    if not isinstance(game_title, str) or not game_title.strip():
        with st.form("raiox_game_select"):
            requested_title = st.text_input(
                "Jogo para consultar",
                placeholder="Ex.: Hades, Elden Ring...",
            )
            submitted = st.form_submit_button("Ver Raio-X")
        if submitted and requested_title.strip():
            st.session_state["raiox_jogo"] = requested_title.strip()
            st.session_state["raiox_origem"] = "inicio"
            st.rerun()
        st.info("Selecione “Não avaliado” em um card ou informe o nome do jogo.")
        return

    _render_xray_details(game_title)
    origin = st.session_state.get("raiox_origem", "inicio")
    if st.button("Voltar", key="raiox_voltar"):
        st.session_state.pop("raiox_jogo", None)
        st.session_state["pagina"] = "inicio" if origin == "review" else origin
        st.rerun()


def _render_compatibility_result(
    result: Any, index: int, description_pt_br: str | None
) -> None:
    game = dict(result.game)
    title = game["titulo"]
    game["background_image"] = game.get("url_capa")
    key = str(game.get("slug") or game.get("id") or index)
    with st.container(border=True):
        cover_column, details_column = st.columns([1, 2])
        with cover_column:
            st.image(
                _url_capa_jogo(game),
                alt=f"Capa de {title}",
                width="stretch",
            )
        with details_column:
            st.subheader(title)
            genres = game.get("generos")
            st.caption(
                "Gêneros: "
                + (
                    ", ".join(genres)
                    if isinstance(genres, list) and genres
                    else "Sem dados"
                )
            )
            themes = game.get("estilos")
            st.caption(
                "Temas: "
                + (
                    ", ".join(themes)
                    if isinstance(themes, list) and themes
                    else "Sem dados"
                )
            )
            platforms = game.get("plataformas")
            st.caption(
                "Plataformas: "
                + (
                    ", ".join(platforms)
                    if isinstance(platforms, list) and platforms
                    else "Sem dados"
                )
            )
            if description_pt_br:
                st.write(description_pt_br)
            else:
                original_description = game.get("descricao")
                if (
                    isinstance(original_description, str)
                    and original_description.strip()
                ):
                    st.caption(
                        "Descrição em português indisponível; exibindo o texto "
                        "original em inglês."
                    )
                    st.write(original_description)
                else:
                    st.caption("Descrição em português não disponível.")
            if result.score is None:
                st.info(
                    "Dados insuficientes para exibir uma porcentagem confiável."
                )
            else:
                st.metric(
                    "Compatibilidade com seu perfil",
                    f"{result.score}%",
                    help=(
                        "Aderência determinística às preferências informadas, "
                        "normalizada pelos critérios com dados conhecidos."
                    ),
                )
            st.caption(f"Cobertura dos dados avaliados: {result.coverage}%")

        if result.justifications:
            st.markdown(
                "**Por que este jogo combina**"
                if result.score is not None
                else "**Dados considerados**"
            )
            for justification in result.justifications:
                st.write(f"- {justification}")

        source_url = game.get("fonte_url")
        source_date = game.get("fonte_atualizada_em")
        formatted_source_date = _format_review_date(source_date)
        if formatted_source_date != "Data não disponível":
            st.caption(f"Metadados revisados em {formatted_source_date}.")
        if isinstance(source_url, str) and source_url.startswith("https://"):
            st.link_button(
                "Ver fonte dos dados",
                source_url,
                key=f"compat_source_{key}",
            )


def _render_compatibility(
    api: AuthAPI,
    token: str,
) -> None:
    st.title("Inteligência de Compatibilidade")
    st.write(
        "Conte o que você gosta em um jogo para descobrir opções que combinam "
        "com seu perfil."
    )
    if st.button("Voltar ao início", key="compatibility_home"):
        st.session_state["pagina"] = "inicio"
        st.rerun()

    if not isinstance(st.session_state.get("compatibility_catalog"), dict):
        try:
            with st.spinner("Carregando características dos jogos do IGDB..."):
                st.session_state["compatibility_catalog"] = (
                    buscar_catalogo_compatibilidade_igdb()
                )
        except (requests.RequestException, ValueError) as error:
            st.error(f"Não foi possível carregar o catálogo do IGDB: {error}")
            return

    catalog = st.session_state["compatibility_catalog"]
    vocabulary = catalog["vocabulario"]
    if not isinstance(st.session_state.get("compatibility_preferences"), dict):
        try:
            st.session_state["compatibility_preferences"] = (
                api.compatibility_preferences(token)
            )
            st.session_state.pop("compatibility_preferences_error", None)
            st.session_state.pop("compatibility_preferences_error_code", None)
        except AuthAPIError as error:
            st.session_state["compatibility_preferences"] = default_preferences()
            st.session_state["compatibility_preferences_error"] = error.message
            st.session_state["compatibility_preferences_error_code"] = error.code

    preferences_error = st.session_state.get("compatibility_preferences_error")
    preferences_error_code = st.session_state.get(
        "compatibility_preferences_error_code"
    )
    if (
        isinstance(preferences_error, str)
        and preferences_error_code != "compatibility_endpoint_missing"
    ):
        st.warning(
            "Não foi possível carregar suas preferências salvas. Você ainda pode "
            "filtrar os jogos nesta sessão; para salvar o perfil, publique os "
            f"endpoints de preferências no Xano. {preferences_error}"
        )

    try:
        preferences = normalize_preferences(
            st.session_state["compatibility_preferences"],
            vocabulary,
        )
    except ValueError:
        st.warning(
            "Algumas preferências salvas não existem mais no catálogo. "
            "Revise as opções antes de salvar."
        )
        preferences = default_preferences()
        for key in (
            "compatibility_genres",
            "compatibility_styles",
            "compatibility_modes",
            "compatibility_platforms",
        ):
            st.session_state.pop(key, None)

    for key, field in (
        ("compatibility_genres", "generos"),
        ("compatibility_styles", "estilos"),
        ("compatibility_modes", "modos"),
        ("compatibility_platforms", "plataformas"),
    ):
        selected = st.session_state.get(key)
        if isinstance(selected, list) and any(
            value not in vocabulary[field] for value in selected
        ):
            st.session_state.pop(key, None)

    with st.form("compatibility_form"):
        st.subheader("Suas preferências")
        genres = st.multiselect(
            "Gêneros favoritos",
            vocabulary["generos"],
            default=preferences["generos"],
            key="compatibility_genres",
        )
        styles = st.multiselect(
            "Temas favoritos",
            vocabulary["estilos"],
            default=preferences["estilos"],
            key="compatibility_styles",
        )
        modes = st.multiselect(
            "Modo de jogo",
            vocabulary["modos"],
            default=preferences["modos"],
            key="compatibility_modes",
        )
        platforms = st.multiselect(
            "Plataformas utilizadas",
            vocabulary["plataformas"],
            default=preferences["plataformas"],
            key="compatibility_platforms",
        )
        save_preferences = st.form_submit_button("Salvar preferências")
        filter_games = st.form_submit_button("Ver jogos compatíveis")
        generate_recommendations = st.form_submit_button(
            "Salvar e ver recomendações",
            type="primary",
        )

    if save_preferences or filter_games or generate_recommendations:
        draft = {
            "generos": genres,
            "estilos": styles,
            "narrativa": preferences["narrativa"],
            "exploracao": preferences["exploracao"],
            "dificuldade": preferences["dificuldade"],
            "modos": modes,
            "plataformas": platforms,
        }
        try:
            normalized = normalize_preferences(draft, vocabulary)
        except ValueError as error:
            st.error(f"Revise as preferências informadas: {error}")
            return

        if filter_games or generate_recommendations:
            if not any(normalized[field] for field in ("generos", "estilos", "modos")):
                st.session_state.pop("compatibility_results", None)
                st.info("Informe ao menos uma preferência para gerar recomendações.")
            else:
                st.session_state["compatibility_results"] = recommend_games(
                    normalized,
                    catalog["jogos"],
                )

        if save_preferences or generate_recommendations:
            endpoint_missing = (
                st.session_state.get("compatibility_preferences_error_code")
                == "compatibility_endpoint_missing"
            )
            saved_preferences: dict[str, Any] | None = None
            endpoint_missing_message = st.session_state.get(
                "compatibility_preferences_error"
            )
            if not endpoint_missing:
                try:
                    saved_preferences = api.save_compatibility_preferences(
                        token,
                        normalized,
                    )
                except AuthAPIError as error:
                    if error.code == "compatibility_endpoint_missing":
                        endpoint_missing = True
                        endpoint_missing_message = error.message
                    else:
                        st.error(error.message)

            if endpoint_missing:
                st.session_state["compatibility_preferences"] = normalized
                st.session_state["compatibility_preferences_error_code"] = (
                    "compatibility_endpoint_missing"
                )
                if isinstance(endpoint_missing_message, str):
                    st.session_state["compatibility_preferences_error"] = (
                        endpoint_missing_message
                    )
                if save_preferences and not generate_recommendations:
                    st.session_state.pop("compatibility_results", None)
                st.caption(
                    "Preferências mantidas apenas nesta sessão. Para salvá-las "
                    "entre acessos, publique o endpoint de preferências no Xano."
                )
            elif saved_preferences is not None:
                st.session_state["compatibility_preferences"] = saved_preferences
                st.session_state.pop("compatibility_preferences_error", None)
                st.session_state.pop("compatibility_preferences_error_code", None)
                if save_preferences and not generate_recommendations:
                    st.session_state.pop("compatibility_results", None)
                st.success("Preferências salvas na sua conta.")

        if filter_games:
            st.success("Recomendações atualizadas com os filtros selecionados.")

    st.divider()
    with st.expander("Como a compatibilidade é calculada"):
        st.write(
            "Gêneros têm peso de 50%, temas 30% e modos de jogo 20%. Cada "
            "categoria compara as opções selecionadas com os atributos do IGDB. "
            "Plataformas são um filtro: o jogo precisa estar confirmado em ao "
            "menos uma plataforma escolhida."
        )
        st.write(
            "Critérios não respondidos não entram no cálculo. Dados desconhecidos "
            "não contam como incompatibilidade. A porcentagem só aparece quando "
            "há dados para pelo menos 70% do peso respondido; abaixo disso, o "
            "card informa que não há dados suficientes. A nota é uma aderência "
            "ao perfil, não uma previsão de satisfação."
        )

    if not catalog["jogos"]:
        st.warning(
            "O IGDB não retornou jogos com características suficientes para "
            "gerar recomendações."
        )
        return

    results = st.session_state.get("compatibility_results")
    if not isinstance(results, list):
        st.info(
            "Selecione suas preferências e escolha “Ver jogos compatíveis” "
            "para filtrar o catálogo do IGDB."
        )
        return

    scored_results = [result for result in results if result.score is not None]
    insufficient_results = [result for result in results if result.score is None]
    visible_results = scored_results[:12] + insufficient_results[:6]
    localized_descriptions: list[str | None] = []
    steam_error: requests.RequestException | ValueError | None = None
    with st.spinner("Buscando descrições em português na Steam..."):
        for result in visible_results:
            game_name = result.game.get("titulo")
            if not isinstance(game_name, str) or not game_name.strip():
                localized_descriptions.append(None)
                continue
            try:
                localized_descriptions.append(
                    _load_brazilian_game_description(game_name)
                )
            except (requests.RequestException, ValueError) as error:
                steam_error = error
                localized_descriptions.append(None)
    if steam_error is not None:
        st.warning(
            "Não foi possível carregar algumas descrições localizadas da Steam: "
            f"{steam_error}"
        )

    localized_index = 0
    if scored_results:
        st.subheader("Jogos que combinam com você")
        for index, result in enumerate(scored_results[:12]):
            _render_compatibility_result(
                result,
                index,
                localized_descriptions[localized_index],
            )
            localized_index += 1
    if insufficient_results:
        st.subheader("Jogos sem dados suficientes")
        st.caption(
            "Estes jogos não recebem porcentagem nem entram no ranking por falta "
            "de metadados para avaliar seu perfil."
        )
        for index, result in enumerate(insufficient_results[:6], start=12):
            _render_compatibility_result(
                result,
                index,
                localized_descriptions[localized_index],
            )
            localized_index += 1
    if not results:
        st.info(
            "Não encontramos recomendações confiáveis. Revise as plataformas "
            "selecionadas ou tente outras preferências."
        )


def _render_compact_promotion_card(
    deal: dict[str, Any],
    rate: Decimal,
    stores: dict[str, str],
    rating_averages: dict[str, GameRatingAverage] | None,
    *,
    key_prefix: str,
) -> None:
    title = str(deal["title"])
    deal_id = str(deal["deal_id"])
    safe_deal_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", deal_id)
    with st.container(
        border=True,
        height="stretch",
        key=f"{key_prefix}-deal-{safe_deal_id}",
    ):
        image_url = deal.get("thumb")
        try:
            parsed_image_url = (
                urlsplit(image_url) if isinstance(image_url, str) else None
            )
            image_is_safe = (
                parsed_image_url is not None
                and parsed_image_url.scheme == "https"
                and bool(parsed_image_url.hostname)
            )
        except ValueError:
            image_is_safe = False

        if image_is_safe and isinstance(image_url, str):
            savings = deal["savings"]
            formatted_savings = (
                f"{savings:.0f}%" if savings >= 1 else "&lt;1%"
            )
            st.markdown(
                f"""
                <div class="deal-card-cover">
                    <img src="{escape_html(image_url, quote=True)}"
                         alt="Capa de {escape_html(title, quote=True)}"
                         loading="lazy">
                    <span class="deal-card-discount">
                        -{formatted_savings}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.image(
                _placeholder_data_uri(title, kind="game"),
                alt=f"Capa de {title}",
                width="stretch",
            )

        st.markdown(f"**{escape_html(title)}**")
        store_name = stores.get(str(deal["store_id"]), "Loja não identificada")
        st.caption(
            f":material/sports_esports: {escape_html(store_name)}"
        )
        _render_xray_badge(
            title,
            key=f"{key_prefix}_xray_{safe_deal_id}",
            origin="promocoes" if key_prefix == "promotions" else "inicio",
        )

        sale_price = _format_brl_price(deal["sale_price"], rate)
        normal_price = _format_brl_price(deal["normal_price"], rate)
        st.markdown(
            '<div class="deal-card-price">'
            f"<strong>{escape_html(sale_price)}</strong>"
            f"<s>{escape_html(normal_price)}</s>"
            "</div>",
            unsafe_allow_html=True,
        )

        average = (
            rating_averages.get(title.strip().casefold())
            if rating_averages is not None
            else None
        )
        rating_text = (
            f"★ Avaliação da comunidade: "
            f"{average.average:.1f}".replace(".", ",")
            + f"/5 ({average.total})"
            if average is not None
            else "☆ Sem avaliações da comunidade"
        )
        rating_column, evaluate_column = st.columns([4, 1])
        rating_column.markdown(
            f'<div class="deal-card-rating">{rating_text}</div>',
            unsafe_allow_html=True,
        )
        if evaluate_column.button(
            "Avaliar",
            key=f"{key_prefix}_evaluate_{safe_deal_id}",
            help=f"Avaliar {title}",
            width="stretch",
        ):
            st.session_state["jogo_selecionado"] = {
                "id": f"featured-{deal_id}",
                "name": title,
                "background_image": image_url,
                "cheapest": deal["sale_price"],
                "cheapest_deal_id": deal_id,
            }
            st.rerun()

        st.link_button(
            "Ver oferta",
            promotion_url(deal_id),
            key=f"{key_prefix}_deal_link_{safe_deal_id}",
            width="stretch",
        )


def _render_home_promotion_grid(
    promotions: list[dict[str, Any]],
    rate: Decimal,
    stores: dict[str, str],
    rating_averages: dict[str, GameRatingAverage] | None,
) -> None:
    st.subheader("Ofertas em destaque")
    if not promotions:
        st.info("Nenhuma oferta em destaque no momento.")
        return

    page_size = 8
    page_count = (len(promotions) + page_size - 1) // page_size
    page_index = st.session_state.get("home_promotions_page", 0)
    if isinstance(page_index, bool) or not isinstance(page_index, int):
        page_index = 0
    page_index = max(0, min(page_index, page_count - 1))
    start = page_index * page_size
    visible_promotions = promotions[start : start + page_size]

    st.caption(
        f"Ofertas {start + 1}–{start + len(visible_promotions)} "
        f"de {len(promotions)}"
    )
    columns = st.columns(4)
    for index, deal in enumerate(visible_promotions):
        with columns[index % len(columns)]:
            _render_compact_promotion_card(
                deal,
                rate,
                stores,
                rating_averages,
                key_prefix="home",
            )

    previous_col, _, next_col = st.columns([1, 4, 1])
    with previous_col:
        if st.button(
            "Anterior",
            key="home_promotions_previous",
            disabled=page_index == 0,
            icon=":material/chevron_left:",
        ):
            st.session_state["home_promotions_page"] = page_index - 1
            st.rerun()
    with next_col:
        if st.button(
            "Próximas",
            key="home_promotions_next",
            disabled=page_index >= page_count - 1,
            icon=":material/chevron_right:",
        ):
            st.session_state["home_promotions_page"] = page_index + 1
            st.rerun()


def _render_promotions(api: AuthAPI, token: str) -> None:
    st.title("Jogos em promoção")
    st.write(
        "Confira ofertas disponíveis em diversas lojas. Os preços em dólar são "
        "convertidos para reais pela cotação de referência mais recente."
    )

    search_term = st.text_input(
        "Buscar jogo em promoção",
        placeholder="Ex.: Hades, Stardew Valley...",
        key="promocoes_pesquisa",
    )
    minimum_discount = st.slider(
        "Desconto mínimo",
        min_value=0,
        max_value=100,
        value=0,
        format="%d%%",
        key="promocoes_desconto_minimo",
    )

    try:
        with st.spinner("Carregando ofertas da CheapShark..."):
            promotions = buscar_ofertas_cheapshark()
            rate, rate_date = buscar_cotacao_usd_brl()
            try:
                stores = buscar_lojas_cheapshark()
            except (requests.RequestException, ValueError):
                st.warning("Não foi possível carregar os nomes das lojas.")
                stores = {}
    except (requests.RequestException, ValueError):
        st.error("Não foi possível carregar as ofertas. Tente novamente mais tarde.")
        return

    _render_exchange_rate(rate, rate_date)
    normalized_search = search_term.strip().casefold()
    filtered_promotions = [
        deal
        for deal in promotions
        if deal["savings"] > 0
        and deal["savings"] >= minimum_discount
        and normalized_search in deal["title"].casefold()
    ]
    filtered_promotions.sort(
        key=lambda deal: deal["savings"],
        reverse=True,
    )

    if not filtered_promotions:
        st.info("Nenhuma oferta corresponde aos filtros selecionados.")
        return

    rating_averages = _load_game_rating_averages(
        api,
        token,
        [deal["title"] for deal in filtered_promotions],
    )
    st.caption(f"{len(filtered_promotions)} oferta(s) encontrada(s)")
    columns = st.columns(4)
    for index, deal in enumerate(filtered_promotions):
        with columns[index % len(columns)]:
            _render_compact_promotion_card(
                deal,
                rate,
                stores,
                rating_averages,
                key_prefix="promotions",
            )


def _featured_games_from_promotions(
    promotions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    featured_games: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for deal in sorted(
        promotions,
        key=lambda item: item["savings"],
        reverse=True,
    ):
        title = deal["title"].strip()
        normalized_title = title.casefold()
        if normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)
        featured_games.append(
            {
                "id": f"featured-{deal['deal_id']}",
                "name": title,
                "background_image": deal.get("thumb"),
                "cheapest": deal["sale_price"],
                "cheapest_deal_id": deal["deal_id"],
            }
        )
        if len(featured_games) == 6:
            break
    return featured_games


def _render_featured_games(
    games: list[dict[str, Any]],
    rate: Decimal | None,
    rating_averages: dict[str, GameRatingAverage] | None,
) -> None:
    st.subheader("Jogos em destaque para avaliar")
    if not games:
        st.info("Nenhum jogo em destaque disponível no momento.")
        return

    columns = st.columns(4)
    for index, game in enumerate(games):
        with columns[index % len(columns)]:
            safe_game_id = re.sub(
                r"[^a-zA-Z0-9_-]+",
                "_",
                str(game.get("id") or game["name"]),
            )
            with st.container(
                border=True,
                height="stretch",
                key=f"featured-game-{safe_game_id}",
            ):
                _render_featured_game_card_cover(game)
                st.markdown(f"**{escape_html(game['name'])}**")
                st.caption(":material/computer: PC")
                _render_xray_badge(
                    game["name"],
                    key=f"featured_xray_{safe_game_id}",
                    origin="inicio",
                )
                average = (
                    rating_averages.get(game["name"].strip().casefold())
                    if rating_averages is not None
                    else None
                )
                if average is None:
                    st.caption("☆ Sem avaliações da comunidade")
                else:
                    formatted_average = f"{average.average:.1f}".replace(".", ",")
                    review_label = (
                        "avaliação" if average.total == 1 else "avaliações"
                    )
                    st.caption(
                        f"★ {formatted_average} / 5 · "
                        f"{average.total} {review_label}"
                    )
                cheapest = game.get("cheapest")
                if isinstance(cheapest, Decimal) and rate is not None:
                    st.caption("Menor preço encontrado")
                    st.markdown(
                        f"**{_format_brl_price(cheapest, rate)}**"
                    )

                deal_id = game.get("cheapest_deal_id")
                action_columns = st.columns(2)
                if isinstance(deal_id, str) and deal_id:
                    action_columns[0].link_button(
                        "Oferta",
                        promotion_url(deal_id),
                        key=f"featured_deal_{safe_game_id}",
                        width="stretch",
                    )
                if action_columns[1].button(
                    "Fazer avaliação",
                    key=f"btn_avaliar_{safe_game_id}",
                    width="stretch",
                ):
                    st.session_state["jogo_selecionado"] = game
                    st.rerun()


def _render_my_reviews(
    api: AuthAPI, token: str
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

        try:
            cover_url = buscar_capa_jogo_igdb(game_name.strip())
        except (requests.RequestException, ValueError):
            st.warning(f"Não foi possível carregar a capa de {game_name}.")
            cover_url = None
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
    api: AuthAPI,
    token: str,
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
    compatibility_owner = str(user.get("id") or user.get("email") or token)
    if st.session_state.get("compatibility_owner") != compatibility_owner:
        for key in (
            "compatibility_catalog",
            "compatibility_preferences",
            "compatibility_preferences_error",
            "compatibility_preferences_error_code",
            "compatibility_results",
            "compatibility_genres",
            "compatibility_styles",
            "compatibility_narrative",
            "compatibility_exploration",
            "compatibility_difficulty",
            "compatibility_modes",
            "compatibility_platforms",
        ):
            st.session_state.pop(key, None)
        st.session_state["compatibility_owner"] = compatibility_owner

    with st.sidebar:
        avatar = _url_imagem_perfil(user.get("img_perfil"), api)
        with st.container(key="sidebar-profile"):
            avatar_columns = st.columns([1, 1, 1])
            with avatar_columns[1]:
                st.image(
                    avatar,
                    alt=f"Foto de perfil de {nome_utilizador}",
                    width=76,
                )
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
        if st.button("🏷️ Promoções", width="stretch"):
            st.session_state["pagina"] = "promocoes"
            st.session_state.pop("jogo_selecionado", None)
            st.rerun()
        if st.button("🎯 Inteligência de Compatibilidade", width="stretch"):
            st.session_state["pagina"] = "compatibilidade"
            st.session_state.pop("jogo_selecionado", None)
            st.rerun()
        if st.button("🔍 Raio-X", width="stretch"):
            st.session_state["pagina"] = "raiox"
            st.session_state["raiox_origem"] = "inicio"
            st.session_state.pop("raiox_jogo", None)
            st.session_state.pop("jogo_selecionado", None)
            st.rerun()
        if st.button("⚙️ Configurações", width="stretch"):
            st.session_state["pagina"] = "configuracoes"
            st.rerun()
        with st.container(key="sidebar-logout"):
            if st.button("Sair", width="stretch", type="primary"):
                st.session_state.pop("auth_token", None)
                st.session_state.pop("user_profile", None)
                st.session_state.pop("compatibility_owner", None)
                for key in (
                    "compatibility_catalog",
                    "compatibility_preferences",
                    "compatibility_preferences_error",
                    "compatibility_preferences_error_code",
                    "compatibility_results",
                ):
                    st.session_state.pop(key, None)
                st.rerun()

    jogo_selecionado = st.session_state.get("jogo_selecionado")
    if st.session_state.get("pagina") == "configuracoes":
        _render_profile_settings(api, token, user)
        return
    if st.session_state.get("pagina") == "minhas_reviews":
        _render_my_reviews(api, token)
        return
    if st.session_state.get("pagina") == "promocoes":
        _render_promotions(api, token)
        return
    if st.session_state.get("pagina") == "compatibilidade":
        _render_compatibility(api, token)
        return
    if st.session_state.get("pagina") == "raiox":
        _render_xray_page()
        return
    if isinstance(jogo_selecionado, dict):
        _render_game_review(api, token, jogo_selecionado)
        game_name = jogo_selecionado.get("name")
        if isinstance(game_name, str) and game_name:
            _render_game_comments(api, token, game_name)
        return

    promotions: list[dict[str, Any]] = []
    rate: Decimal | None = None
    rating_averages: dict[str, GameRatingAverage] | None = None
    try:
        with st.spinner("Carregando ofertas em destaque..."):
            promotions = buscar_ofertas_cheapshark()
            rate, rate_date = buscar_cotacao_usd_brl()
            try:
                stores = buscar_lojas_cheapshark()
            except (requests.RequestException, ValueError):
                st.warning("Não foi possível carregar os nomes das lojas.")
                stores = {}
    except (requests.RequestException, ValueError):
        st.error("Não foi possível carregar as ofertas em destaque.")
    else:
        rating_averages = _load_game_rating_averages(
            api,
            token,
            [deal["title"] for deal in promotions],
        )
        _render_exchange_rate(rate, rate_date)
        _render_home_promotion_grid(
            promotions,
            rate,
            stores,
            rating_averages,
        )

    st.divider()
    # --- Catálogo de jogos (IGDB) ---
    st.write("### Catálogo de Jogos")
    pesquisa = st.text_input(
        "Procure um jogo para avaliar",
        placeholder="Ex.: The Last of Us, FIFA, Mario...",
    )

    if not pesquisa.strip():
        _render_featured_games(
            _featured_games_from_promotions(promotions),
            rate,
            rating_averages,
        )
    else:
        try:
            lista_de_jogos = buscar_jogos_igdb(pesquisa)
        except (requests.RequestException, ValueError):
            st.error(
                "Não foi possível buscar jogos na IGDB. "
                "Verifique a configuração da Twitch."
            )
            lista_de_jogos = []

        if pesquisa.strip() and not lista_de_jogos:
            st.warning("Nenhum jogo encontrado com esse nome.")

        rate: Decimal | None = None
        rate_date: date | None = None
        if any(isinstance(game.get("cheapest"), Decimal) for game in lista_de_jogos):
            try:
                rate, rate_date = buscar_cotacao_usd_brl()
                _render_exchange_rate(rate, rate_date)
            except (requests.RequestException, ValueError):
                st.error("Não foi possível converter os preços encontrados para reais.")

        rating_averages = _load_game_rating_averages(
            api,
            token,
            [game["name"] for game in lista_de_jogos],
        )
        col_esquerda, col_direita = st.columns(2)
        for index, jogo in enumerate(lista_de_jogos):
            coluna_atual = col_esquerda if index % 2 == 0 else col_direita

            with coluna_atual:
                with st.container(border=True):
                    _render_game_card_cover(jogo)
                    st.subheader(jogo["name"])
                    _render_game_platforms(jogo)
                    _render_game_rating(jogo["name"], rating_averages)
                    cheapest = jogo.get("cheapest")
                    if isinstance(cheapest, Decimal) and rate is not None:
                        st.metric(
                            "Menor preço encontrado",
                            _format_brl_price(cheapest, rate),
                        )
                    elif isinstance(cheapest, Decimal):
                        st.caption("Menor preço disponível; cotação indisponível.")

                    deal_id = jogo.get("cheapest_deal_id")
                    if isinstance(deal_id, str) and deal_id:
                        st.link_button(
                            "Ver menor oferta",
                            promotion_url(deal_id),
                            width="stretch",
                        )

                    if st.button(
                        "Fazer avaliação",
                        key=f"btn_avaliar_{jogo['id']}",
                        width="stretch",
                    ):
                        st.session_state["jogo_selecionado"] = jogo
                        st.rerun()

    st.divider()
    st.write("### Últimas Avaliações")
    st.info("Nenhuma avaliação encontrada. Seja o primeiro a avaliar um jogo!")


def main() -> None:
    st.set_page_config(
        page_title="GGReviews",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_dotenv(Path(__file__).resolve().with_name(".env"))
    _apply_gamer_background()
    _capture_password_reset_link()

    try:
        secrets = dict(st.secrets)
    except StreamlitSecretNotFoundError:
        secrets = {}
    try:
        config = load_auth_config(secrets=secrets)
    except ConfigurationError as error:
        st.error(str(error))
        st.stop()

    api = AuthAPI(
        config.api_base_url,
        rating_averages_url=config.rating_averages_url,
    )
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
    if isinstance(token, str) and token:
        _render_authenticated(api, token)
    else:
        st.session_state.pop("auth_token", None)
        _render_auth_forms(api)


if __name__ == "__main__":
    main()