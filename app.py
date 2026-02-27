import streamlit as st
import pandas as pd
import requests
import re
import time
import random
import unicodedata
from bs4 import BeautifulSoup
from io import BytesIO
from urllib.parse import quote_plus
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# ============================================================
# Verso Sourcing Pro — Premium MVP (Desktop-first)
# - Prospecção via OpenStreetMap (Overpass)
# - Enriquecimento de endereço via Nominatim (OSM) quando faltante
# - Instagram handle via OSM tags + buscadores alternativos (DDG/Bing)
# - Enriquecimento de CNPJ via BrasilAPI (entrada por lista/arquivo)
# ============================================================

st.set_page_config(page_title="Verso Sourcing Pro", page_icon="✨", layout="wide")

# -------------------------
# THEME (Instagramável + Verso Vivo site-like)
# -------------------------
st.markdown(
    """
<style>
:root{
  --vv-bg:#fafafa;
  --vv-card:#ffffff;
  --vv-text:#111111;
  --vv-muted:#6b7280;
  --vv-border:#e6e6e6;

  /* Verso Vivo vibe: preto clean + detalhe rosado discreto */
  --vv-accent:#111111;
  --vv-accent2:#f02d71; /* detalhe */
  --vv-link:#00376b;

  --vv-radius:18px;
  --vv-shadow:0 8px 24px rgba(17,17,17,0.06);
  --vv-shadow-soft:0 1px 0 rgba(0,0,0,0.03);
}

/* SF on Apple, decent fallback elsewhere */
html, body, [class*="st-"]{
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
               "Helvetica Neue", Helvetica, Arial, "Segoe UI", Roboto, sans-serif !important;
  color: var(--vv-text);
}

.stApp{ background: var(--vv-bg); }

.main .block-container{
  max-width: 1280px;
  padding-top: 1.0rem;
  padding-bottom: 2.2rem;
}

/* Hide Streamlit chrome */
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
header{visibility:hidden;}

/* Topbar */
.vv-topbar{
  position: sticky;
  top: 0;
  z-index: 999;
  background: rgba(250,250,250,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--vv-border);
  margin: -1rem -1rem 1rem -1rem;
  padding: 14px 0;
}
.vv-topbar-inner{
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1rem;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 14px;
}
.vv-brand{
  display:flex;
  align-items:center;
  gap: 12px;
  min-width: 320px;
}
.vv-brand h1{
  font-size: 18px;
  margin: 0;
  font-weight: 900;
  letter-spacing: -0.3px;
}
.vv-brand p{
  margin: 0;
  font-size: 12px;
  color: var(--vv-muted);
}
.vv-pill{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  border-radius: 999px;
  padding: 10px 14px;
  border: 1px solid var(--vv-border);
  background: var(--vv-card);
  font-size: 12px;
  font-weight: 800;
  color: var(--vv-text);
}

/* Inputs */
.stTextInput>div>div>input, .stTextArea textarea{
  border-radius: 14px !important;
  border: 1px solid var(--vv-border) !important;
  background: var(--vv-card) !important;
  padding: 12px 12px !important;
  box-shadow: none !important;
  font-size: 15px !important;
}
.stSelectbox>div>div>div, .stMultiSelect>div>div{
  border-radius: 14px !important;
  border: 1px solid var(--vv-border) !important;
  background: var(--vv-card) !important;
  box-shadow: none !important;
  font-size: 15px !important;
}

/* Primary button */
.stButton>button{
  width:100%;
  border-radius: 999px !important;
  border: 1px solid transparent !important;
  background: var(--vv-accent) !important;
  color: #fff !important;
  font-weight: 900 !important;
  height: 46px !important;
  box-shadow: none !important;
  transition: transform .12s ease, filter .12s ease;
  font-size: 14px !important;
}
.stButton>button:hover{
  filter: brightness(0.95);
  transform: translateY(-1px);
}

/* garantir contraste mesmo em estados especiais */
.stButton>button *{ color: inherit !important; opacity: 1 !important; }
.stButton>button:disabled{
  background: var(--vv-accent) !important;
  color: #fff !important;
  opacity: 0.70 !important;
}

/* Cards */
.vv-card{
  background: var(--vv-card);
  border: 1px solid var(--vv-border);
  border-radius: var(--vv-radius);
  padding: 16px;
  box-shadow: var(--vv-shadow-soft);
}
.vv-card:hover{
  box-shadow: var(--vv-shadow);
}
.vv-card-title{
  font-size: 14px;
  font-weight: 900;
  margin: 0 0 10px 0;
}
.vv-note{
  font-size: 12px;
  color: var(--vv-muted);
  line-height: 1.35;
}

/* Fixed panel (never “sumir”) */
.vv-panel-sticky{
  position: sticky;
  top: 84px;
  max-height: calc(100vh - 110px);
  overflow: auto;
}

/* Lead item */
.vv-lead{
  background: var(--vv-card);
  border: 1px solid var(--vv-border);
  border-radius: var(--vv-radius);
  padding: 16px;
  margin-bottom: 14px;
  box-shadow: var(--vv-shadow-soft);
}
.vv-lead-header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 12px;
}
.vv-lead-left{
  display:flex;
  align-items:center;
  gap: 12px;
  min-width: 0;
}
.vv-avatar{
  width: 44px;
  height: 44px;
  border-radius: 999px;
  background: radial-gradient(circle at 30% 30%, #feda75 0%, #fa7e1e 30%, #d62976 55%, #962fbf 75%, #4f5bd5 100%);
  display:flex;
  align-items:center;
  justify-content:center;
  flex: 0 0 auto;
}
.vv-avatar-inner{
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: #fff;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight: 950;
  font-size: 13px;
  color: var(--vv-text);
}
.vv-lead-name{
  font-size: 15px;
  font-weight: 950;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vv-lead-city{
  font-size: 12px;
  color: var(--vv-muted);
  margin: 0;
}

.vv-chip-row{
  display:flex;
  flex-wrap:wrap;
  gap: 8px;
  margin-top: 10px;
}
.vv-chip{
  display:inline-flex;
  align-items:center;
  gap: 8px;
  border-radius: 999px;
  padding: 7px 10px;
  background: #f1f3f5;
  border: 1px solid #f1f3f5;
  font-size: 12px;
  font-weight: 800;
  color: var(--vv-text);
}
.vv-chip span{
  color: var(--vv-muted);
  font-weight: 900;
}
.vv-actions{
  display:flex;
  flex-wrap:wrap;
  gap: 10px;
  margin-top: 12px;
}
.vv-link-pill{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  border-radius: 999px;
  padding: 9px 12px;
  font-size: 12px;
  font-weight: 950;
  border: 1px solid var(--vv-border);
  background: #fff;
  color: var(--vv-text) !important;
  text-decoration: none !important;
}
.vv-link-pill:hover{
  filter: brightness(0.98);
  text-decoration: none !important;
}
.vv-link-primary{
  background: #111;
  border-color: #111;
  color: #fff !important;
}
.vv-link-muted{
  background: #f1f3f5;
  border-color: #f1f3f5;
}
.vv-hr{
  border: none;
  border-top: 1px solid #f1f1f1;
  margin: 14px 0;
}

/* Tables */
div[data-testid="stDataFrame"]{
  border-radius: var(--vv-radius);
  overflow: hidden;
  border: 1px solid var(--vv-border);
}

</style>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Helpers
# -------------------------
SESSION = requests.Session()

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0 Safari/537.36"
)

HEADERS = {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"}


def safe_digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", (name or "").strip()) if p]
    if not parts:
        return "VV"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def maps_link(query: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def normalize_text(s: str) -> str:
    s = (s or "")
    # remove acentos para melhorar match de palavras (café -> cafe, etc.)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).strip().lower()


# -------------------------
# Overpass (OSM)
# -------------------------
@st.cache_data(ttl=60 * 60, show_spinner=False)
def overpass_query(city_name: str) -> List[Dict[str, Any]]:
    overpass_url = "https://overpass-api.de/api/interpreter"
    # Lojas de roupa/boutique (OSM)
    query = f"""
    [out:json][timeout:90];
    area["name"="{city_name}"]["boundary"="administrative"]->.searchArea;
    (
      nwr["shop"~"clothes|boutique|apparel|fashion|clothing"](area.searchArea);
    );
    out tags center;
    """
    try:
        r = SESSION.get(overpass_url, params={"data": query}, headers=HEADERS, timeout=90)
        if r.status_code == 200:
            return r.json().get("elements", [])
        return []
    except Exception:
        return []


def extract_lat_lon(el: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    if el.get("type") == "node":
        return el.get("lat"), el.get("lon")
    c = el.get("center") or {}
    return c.get("lat"), c.get("lon")


# -------------------------
# Reverse geocoding (Nominatim)
# -------------------------
@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def nominatim_reverse(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "jsonv2",
        "lat": str(lat),
        "lon": str(lon),
        "addressdetails": "1",
        "accept-language": "pt-BR",
    }
    try:
        # Nominatim pede rate-limit baixo. Cache + sleep curto.
        time.sleep(1.05)
        r = SESSION.get(url, params=params, headers={**HEADERS, "Referer": "https://www.oficialversovivo.com.br/"}, timeout=20)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def format_address_from_tags(tags: Dict[str, Any]) -> str:
    street = tags.get("addr:street") or ""
    hn = tags.get("addr:housenumber") or ""
    neigh = tags.get("addr:suburb") or ""
    city = tags.get("addr:city") or ""
    state = tags.get("addr:state") or ""
    parts = [p for p in [f"{street} {hn}".strip(), neigh, city, state] if p]
    return ", ".join(parts).strip() or "N/A"


def format_address_from_nominatim(data: Dict[str, Any]) -> str:
    if not data:
        return "N/A"
    addr = data.get("address") or {}
    road = addr.get("road") or addr.get("pedestrian") or addr.get("path") or ""
    house = addr.get("house_number") or ""
    suburb = addr.get("suburb") or addr.get("neighbourhood") or ""
    city = addr.get("city") or addr.get("town") or addr.get("village") or ""
    state = addr.get("state") or ""
    parts = [p for p in [f"{road} {house}".strip(), suburb, city, state] if p]
    return ", ".join(parts).strip() or (data.get("display_name") or "N/A")


# -------------------------
# Filters: excluir redes/marcas e evitar alimentação
# -------------------------
EXCLUDE_BRANDS = {
    "renner", "c&a", "cea", "zara", "riachuelo", "marisa", "pernambucanas", "havan",
    "hering", "colcci", "hope", "intimissimi", "calzedonia",
    "nike", "adidas", "puma",
    "arezzo", "schutz", "anacapri",
    "loungerie",
    "lacoste", "tommy", "tommy hilfiger",
    "le lis", "lelis", "animale", "farm", "dress to", "dressto",
    "john john", "ellus",
}

FOOD_WORDS = {
    "restaurante", "pizza", "pizzaria", "hamburguer", "hamburgueria", "burger", "bar", "pub",
    "café", "cafe", "cafeteria", "padaria", "confeitaria", "açaí", "acai", "sorveteria",
    "sushi", "japa", "yakisoba", "churrascaria", "lanchonete", "bistrô", "bistro",
}

POSITIVE_KEYWORDS = {
    "multimarca", "multi marca", "boutique", "moda", "fashion", "loja de roupa",
    "loja de roupas", "moda feminina", "feminina", "vestuário", "vestuario", "looks",
}

def is_food_business(name: str, tags: Dict[str, Any]) -> bool:
    n = normalize_text(name)
    if any(w in n for w in FOOD_WORDS):
        return True
    amenity = normalize_text(str(tags.get("amenity", "")))
    cuisine = normalize_text(str(tags.get("cuisine", "")))
    if amenity in {"restaurant", "cafe", "bar", "fast_food", "pub", "ice_cream"}:
        return True
    if cuisine:
        return True
    return False


def is_excluded_brand(name: str, tags: Dict[str, Any]) -> bool:
    n = normalize_text(name)
    brand = normalize_text(str(tags.get("brand", "")))
    operator = normalize_text(str(tags.get("operator", "")))
    # pega também em campos comuns do OSM
    for needle in EXCLUDE_BRANDS:
        if needle in n or (brand and needle in brand) or (operator and needle in operator):
            return True
    return False


def is_valid_store(name: str, tags: Dict[str, Any]) -> bool:
    n = normalize_text(name)
    if not n:
        return False

    if is_food_business(name, tags):
        return False

    if is_excluded_brand(name, tags):
        return False

    # Se tiver palavras-chave “fortes”, ótimo
    if any(k in n for k in POSITIVE_KEYWORDS):
        return True

    # Senão, mantém se OSM já diz que é boutique/clothes (mas ainda passou pelos filtros)
    shop_type = normalize_text(str(tags.get("shop", "")))
    if shop_type in {"boutique", "clothes"}:
        return True

    return False


# -------------------------
# Instagram handle enrichment (sem entrar no Instagram)
# - Preferência: OSM tags (contact:instagram / instagram)
# - Fallback: DuckDuckGo HTML, depois Bing
# -------------------------
def extract_instagram_from_tags(tags: Dict[str, Any]) -> Optional[str]:
    for k in ("contact:instagram", "instagram", "contact:insta", "insta"):
        v = tags.get(k)
        if v:
            v = str(v).strip()
            v = v.replace("https://www.instagram.com/", "").replace("http://www.instagram.com/", "")
            v = v.replace("https://instagram.com/", "").replace("http://instagram.com/", "")
            v = v.strip("/")
            if v:
                return v
    return None


def parse_instagram_handles_from_html(html: str) -> List[str]:
    # Pega qualquer ocorrência de instagram.com/<handle>
    handles = []
    for m in re.finditer(r"instagram\.com/([A-Za-z0-9._]+)/?", html):
        h = m.group(1)
        if h.lower() not in {"reels", "stories", "explore", "p", "tags"}:
            handles.append(h)
    # Dedup preservando ordem
    seen = set()
    out = []
    for h in handles:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def ddg_search_html(query: str) -> Tuple[int, str]:
    url = "https://duckduckgo.com/html/"
    try:
        time.sleep(random.uniform(1.1, 2.1))
        r = SESSION.get(url, params={"q": query}, headers=HEADERS, timeout=20)
        return r.status_code, r.text or ""
    except Exception:
        return 0, ""


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def bing_search_html(query: str) -> Tuple[int, str]:
    url = "https://www.bing.com/search"
    try:
        time.sleep(random.uniform(1.1, 2.1))
        r = SESSION.get(url, params={"q": query}, headers=HEADERS, timeout=20)
        return r.status_code, r.text or ""
    except Exception:
        return 0, ""


def choose_best_handle(handles: List[str], city: str, html: str) -> Optional[str]:
    if not handles:
        return None
    # Heurística simples: se a página contém o nome da cidade próximo, considera melhor
    city_l = normalize_text(city)
    if city_l and city_l in normalize_text(html):
        return handles[0]
    # fallback: primeiro
    return handles[0]


def search_instagram_handle(store_name: str, city: str, enable_ddg=True, enable_bing=True) -> Optional[str]:
    base = store_name.strip()
    city = city.strip()

    # queries inspiradas no “manual”
    queries = [
        f"{base} instagram",
        f"{base} {city} instagram",
        f"{base} loja de roupa instagram",
        f"{base} {city} loja de roupa instagram",
        f"{base} loja de moda feminina instagram",
        f"{base} {city} loja de moda feminina instagram",
    ]

    # DuckDuckGo primeiro
    if enable_ddg:
        for q in queries:
            status, html = ddg_search_html(q)
            if status == 429:
                time.sleep(4.0)
            if status != 200 or not html:
                continue
            handles = parse_instagram_handles_from_html(html)
            h = choose_best_handle(handles, city, html)
            if h:
                return h

    # Bing fallback
    if enable_bing:
        for q in queries:
            status, html = bing_search_html(q)
            if status == 429:
                time.sleep(4.0)
            if status != 200 or not html:
                continue
            handles = parse_instagram_handles_from_html(html)
            h = choose_best_handle(handles, city, html)
            if h:
                return h

    return None



# -------------------------
# Meta API (Instagram Graph) — Enriquecimento oficial (followers/bio/website)
# - Funciona melhor quando você já tem o @ (handle).
# - Requer IG User ID + User Access Token (guardados em st.secrets).
# -------------------------
def get_meta_credentials() -> Tuple[Optional[str], Optional[str]]:
    ig_user_id = None
    token = None
    try:
        if "IG_USER_ID" in st.secrets:
            ig_user_id = str(st.secrets["IG_USER_ID"]).strip()
        # compat: nomes alternativos
        if not ig_user_id and "META_IG_USER_ID" in st.secrets:
            ig_user_id = str(st.secrets["META_IG_USER_ID"]).strip()

        if "META_USER_TOKEN_LONG" in st.secrets:
            token = str(st.secrets["META_USER_TOKEN_LONG"]).strip()
        elif "META_ACCESS_TOKEN" in st.secrets:
            token = str(st.secrets["META_ACCESS_TOKEN"]).strip()
    except Exception:
        pass

    if ig_user_id and not ig_user_id.isdigit():
        ig_user_id = None
    if token and len(token) < 20:
        token = None
    return ig_user_id, token


def meta_available() -> bool:
    ig, tok = get_meta_credentials()
    return bool(ig and tok)


def meta_business_discovery(username: str) -> Dict[str, Any]:
    """Retorna dict com followers_count/biography/website via Business Discovery.
    Cache em memória por sessão (não persiste token).
    """
    u = (username or "").strip().lstrip("@")
    if not u:
        return {}

    if "meta_cache" not in st.session_state:
        st.session_state.meta_cache = {}
    cache: Dict[str, Any] = st.session_state.meta_cache

    if u in cache:
        return cache[u]

    ig_user_id, token = get_meta_credentials()
    if not ig_user_id or not token:
        cache[u] = {}
        return {}

    url = f"https://graph.facebook.com/v25.0/{ig_user_id}"
    fields = f"business_discovery.username({u}){{username,followers_count,media_count,biography,website}}"
    params = {"fields": fields, "access_token": token}

    try:
        # pequeno delay para não estourar rate-limit
        time.sleep(0.25)
        r = SESSION.get(url, params=params, timeout=25)
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    except Exception:
        data = {}

    bd = (data or {}).get("business_discovery") or {}
    out = {
        "username": bd.get("username") or u,
        "followers_count": bd.get("followers_count"),
        "media_count": bd.get("media_count"),
        "biography": bd.get("biography"),
        "website": bd.get("website"),
        "raw": data if isinstance(data, dict) else {},
    }

    # normaliza N/A
    if out.get("followers_count") is None:
        out["followers_count"] = "N/A"
    if not out.get("biography"):
        out["biography"] = "N/A"
    if not out.get("website"):
        out["website"] = "N/A"

    cache[u] = out
    return out

# -------------------------
# CNPJ enrichment (BrasilAPI)
# -------------------------
@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def brasilapi_cnpj(cnpj_digits: str) -> Optional[Dict[str, Any]]:
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_digits}"
    try:
        time.sleep(0.55)  # seja gentil (evita rate-limit)
        r = SESSION.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None




# -------------------------
# (LEGACY REMOVIDO) — A busca por CNPJ via serviços pagos foi removida.
# O app agora usa: (1) descoberta de CNPJ por busca pública (DDG/Bing) + (2) consulta via BrasilAPI.
# -------------------------

def parse_cnpjs_from_html(html: str) -> List[str]:
    # Procura padrões comuns de CNPJ (com ou sem pontuação)
    cnpjs = []
    # Formato com pontuação: 12.345.678/0001-90
    for m in re.finditer(r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", html):
        d = safe_digits(m.group(1))
        if len(d) == 14:
            cnpjs.append(d)
    # Apenas 14 dígitos (mais raro por estar misturado no HTML)
    for m in re.finditer(r"(?<!\d)(\d{14})(?!\d)", html):
        d = m.group(1)
        if len(d) == 14:
            cnpjs.append(d)
    # Dedup preservando ordem
    seen = set()
    out = []
    for c in cnpjs:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def search_cnpj_for_store(store_name: str, city: str, enable_ddg: bool = True, enable_bing: bool = True) -> Optional[str]:
    """Descobre CNPJ por busca pública (DDG/Bing). Não requer token.
    Obs.: pode falhar dependendo do volume / rate-limit / ausência de CNPJ nos resultados.
    """
    base = (store_name or "").strip()
    city = (city or "").strip()
    if not base:
        return None

    queries = [
        f'"{base}" {city} CNPJ',
        f'{base} {city} CNPJ',
        f'{base} CNPJ {city}',
        f'{base} CNPJ',
        f'{base} {city} razão social CNPJ',
        f'{base} {city} "cnpj"',
    ]

    def pick_best(candidates: List[str]) -> Optional[str]:
        # Heurística simples: primeiro candidato
        return candidates[0] if candidates else None

    # DuckDuckGo
    if enable_ddg:
        for q in queries:
            status, html = ddg_search_html(q)
            if status == 429:
                time.sleep(4.0)
            if status != 200 or not html:
                continue
            cands = parse_cnpjs_from_html(html)
            best = pick_best(cands)
            if best:
                return best

    # Bing fallback
    if enable_bing:
        for q in queries:
            status, html = bing_search_html(q)
            if status == 429:
                time.sleep(4.0)
            if status != 200 or not html:
                continue
            cands = parse_cnpjs_from_html(html)
            best = pick_best(cands)
            if best:
                return best

    return None


def socios_from_brasilapi(data: Dict[str, Any]) -> Tuple[str, str]:
    """Retorna (todos_socios, socios_administradores) com base no campo 'qsa' (quando existir)."""
    socios = data.get("qsa") or data.get("socios") or []
    if not isinstance(socios, list) or not socios:
        return "N/A", "N/A"

    all_items = []
    admins = []
    for s in socios:
        if not isinstance(s, dict):
            continue
        nome = (s.get("nome_socio") or s.get("nome") or "").strip()
        qual = (s.get("qualificacao_socio") or s.get("qualificacao") or "").strip()
        item = nome if not qual else f"{nome} ({qual})"
        if item.strip():
            all_items.append(item)

        ql = (qual or "").lower()
        if any(k in ql for k in ["administr", "diretor", "gestor", "president", "socio administrador", "sócio administrador"]):
            if nome:
                admins.append(nome)

    return ("; ".join(all_items) or "N/A"), ("; ".join(admins) or "N/A")


def brasilapi_to_row(data: Dict[str, Any], loja: str, cidade: str, cnpj: str, status: str) -> Dict[str, Any]:
    # Mapeamento tolerante (campos podem variar)
    all_socios, admin_socios = socios_from_brasilapi(data or {})
    cnaes_sec = data.get("cnaes_secundarios") or []
    cnaes_sec_str = "; ".join(
        [f"{x.get('codigo','')} {x.get('descricao','')}".strip() for x in cnaes_sec if isinstance(x, dict)]
    ) or "N/A"

    return {
        "Loja": loja,
        "Cidade (Lead)": cidade,
        "CNPJ": (data.get("cnpj") or cnpj or "N/A"),
        "Razão Social": data.get("razao_social") or data.get("razaoSocial") or "N/A",
        "Nome Fantasia": data.get("nome_fantasia") or data.get("nomeFantasia") or "N/A",
        "Abertura": data.get("data_inicio_atividade") or data.get("abertura") or "N/A",
        "Porte": data.get("porte") or data.get("descricao_porte") or "N/A",
        "MEI": data.get("opcao_pelo_mei", data.get("mei", "N/A")),
        "Simples": data.get("opcao_pelo_simples", data.get("simples", "N/A")),
        "Capital Social": data.get("capital_social") or "N/A",
        "Situação": data.get("descricao_situacao_cadastral") or data.get("situacao_cadastral") or "N/A",
        "Email": data.get("email") or "N/A",
        "Telefone": data.get("ddd_telefone_1") or data.get("telefone") or "N/A",
        "UF": data.get("uf") or "N/A",
        "Município": data.get("municipio") or data.get("cidade") or "N/A",
        "CEP": data.get("cep") or "N/A",
        "Logradouro": data.get("logradouro") or "N/A",
        "Número": data.get("numero") or "N/A",
        "Bairro": data.get("bairro") or "N/A",
        "CNAE Principal": data.get("cnae_fiscal") or "N/A",
        "CNAE Principal Desc": data.get("cnae_fiscal_descricao") or "N/A",
        "CNAEs Secundários": cnaes_sec_str,
        "Sócios (QSA)": all_socios,
        "Sócios Administradores": admin_socios,
        "Status": status,
    }


def start_cnpj_run(items: List[Dict[str, str]], batch_size: int = 2, use_ddg: bool = True, use_bing: bool = True) -> None:
    """Inicia job de CNPJ gratuito usando lista de (Loja, Cidade)."""
    st.session_state.cnpj_rows = []
    st.session_state.cnpj_df = pd.DataFrame()

    j = st.session_state.cnpj_job
    j.update(
        {
            "running": True,
            "stop": False,
            "items": items or [],
            "idx": 0,
            "batch_size": int(batch_size),
            "ok_total": 0,
            "attempt_total": 0,
            "target_est": len(items or []),
            "current": "",
            "last_error": "",
            "stopped_reason": "",
            "use_ddg": bool(use_ddg),
            "use_bing": bool(use_bing),
            "started_at": time.time(),
        }
    )


def cnpj_step() -> None:
    """Processa 1–N itens por passo para mostrar resultados em tempo real + permitir parar."""
    j = st.session_state.cnpj_job
    if not j.get("running"):
        return

    if j.get("stop"):
        j["running"] = False
        j["stopped_reason"] = j.get("stopped_reason") or "Interrompido manualmente"
        return

    items = j.get("items") or []
    if not items:
        j["running"] = False
        j["stopped_reason"] = "Nada para processar"
        return

    batch = int(j.get("batch_size", 2))
    use_ddg = bool(j.get("use_ddg", True))
    use_bing = bool(j.get("use_bing", True))
    allow = DEFAULT_CNAE_ALLOW

    try:
        for _ in range(batch):
            idx = int(j.get("idx", 0))
            if idx >= len(items):
                j["running"] = False
                j["stopped_reason"] = "Concluída"
                break

            item = items[idx]
            loja = str(item.get("Loja") or "").strip()
            cidade = str(item.get("Cidade") or item.get("Cidade (Lead)") or "").strip()

            j["current"] = f"{loja} • {cidade}"
            j["idx"] = idx + 1
            j["attempt_total"] = int(j.get("attempt_total", 0)) + 1

            # 1) Descobrir CNPJ (busca pública)
            cnpj = search_cnpj_for_store(loja, cidade, enable_ddg=use_ddg, enable_bing=use_bing)

            if not cnpj:
                st.session_state.cnpj_rows.append(brasilapi_to_row({}, loja, cidade, "N/A", "CNPJ não encontrado"))
                continue

            # 2) Consultar dados completos (BrasilAPI) — inclui sócios/atividades conforme docs
            data = brasilapi_cnpj(cnpj)
            if not data:
                st.session_state.cnpj_rows.append(brasilapi_to_row({}, loja, cidade, cnpj, "Erro na consulta BrasilAPI"))
                continue

            # 3) Filtro CNAE (4781400) — mantém coerência com seu público alvo
            if not cnae_allowed(data, allow):
                st.session_state.cnpj_rows.append(brasilapi_to_row(data, loja, cidade, cnpj, "Ignorado (CNAE fora do alvo)"))
                continue

            st.session_state.cnpj_rows.append(brasilapi_to_row(data, loja, cidade, cnpj, "OK"))
            j["ok_total"] = int(j.get("ok_total", 0)) + 1

        # atualiza DF
        if st.session_state.cnpj_rows:
            st.session_state.cnpj_df = pd.DataFrame(st.session_state.cnpj_rows)

    except Exception as e:
        j["last_error"] = str(e)
        j["running"] = False
        j["stopped_reason"] = "Erro durante execução"


def flatten_cnaes(data: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    # BrasilAPI costuma trazer cnae_fiscal e lista cnaes_secundarios com código/descricao
    cnae_main = None
    cnaes_all = []
    if not data:
        return None, []

    cnae_main = str(data.get("cnae_fiscal") or data.get("cnae_fiscal") or "").strip() or None
    if cnae_main:
        cnaes_all.append(cnae_main)

    secs = data.get("cnaes_secundarios") or []
    for item in secs:
        if isinstance(item, dict):
            code = str(item.get("codigo") or item.get("code") or "").strip()
            if code:
                cnaes_all.append(code)
        elif isinstance(item, str):
            cnaes_all.append(item.strip())

    # dedup
    seen = set()
    out = []
    for c in cnaes_all:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return cnae_main, out


# Default CNAE allowlist (loja de roupas / vestuário)
# 4781400 = "Comércio varejista de artigos do vestuário e acessórios" (IBGE/CONCLA)
DEFAULT_CNAE_ALLOW = {"4781400"}

def cnae_allowed(data: Dict[str, Any], allow: set) -> bool:
    _, all_codes = flatten_cnaes(data)
    if not all_codes:
        return False
    return any(code in allow for code in all_codes)


# -------------------------
# UI — Header
# -------------------------
st.markdown(
    """
<div class="vv-topbar">
  <div class="vv-topbar-inner">
    <div class="vv-brand">
      <div>
        <h1>Verso Sourcing Pro</h1>
        <p>Encontre lojistas multimarcas • Prospecção + Enriquecimento por CNPJ</p>
      </div>
    </div>
    <div style="display:flex; gap:10px; align-items:center;">
      <span class="vv-pill">✨ Premium MVP</span>
      <span class="vv-pill">Desktop</span>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Layout: main + fixed panel
# -------------------------
col_main, col_panel = st.columns([0.70, 0.30], gap="large")

# session state
if "leads_df" not in st.session_state:
    st.session_state.leads_df = None
if "cnpj_df" not in st.session_state:
    st.session_state.cnpj_df = None

# --- Streaming / controle de execução (para mostrar resultados em tempo real + permitir parar) ---
if "leads_rows" not in st.session_state:
    st.session_state.leads_rows = []

if "prospect" not in st.session_state:
    st.session_state.prospect = {
        "running": False,
        "stop": False,
        "cities": [],
        "limit": 0,
        "city_idx": 0,
        "store_idx": 0,
        "valid": [],
        "current_city": "",
        "current_name": "",
        "city_total": 0,
        "done": 0,
        "target_est": 0,
        "started_at": 0.0,
        "enrich_address": True,
        "enrich_instagram": True,
        "use_ddg": True,
        "use_bing": True,
        "batch_size": 2,
        "last_error": "",
        "stopped_reason": "",
    }


# --- Streaming / controle de execução (CNPJ por cidade/CNAE) ---
if "cnpj_rows" not in st.session_state:
    st.session_state.cnpj_rows = []

if "cnpj_job" not in st.session_state:
    # Job de CNPJ (GRÁTIS): tenta descobrir CNPJ a partir de (Loja + Cidade) e consulta dados completos via BrasilAPI.
    # Observação: não existe um endpoint público e 100% gratuito que liste CNPJs por cidade + CNAE em escala.
    # Aqui a lógica é: (1) gerar/usar lista de lojas (OSM/prospecção) e (2) descobrir CNPJ por busca pública (DDG/Bing).
    st.session_state.cnpj_job = {
        "running": False,
        "stop": False,
        "items": [],  # lista de dicts: {"Loja":..., "Cidade":...}
        "idx": 0,
        "batch_size": 2,
        "ok_total": 0,
        "attempt_total": 0,
        "target_est": 0,
        "current": "",
        "last_error": "",
        "stopped_reason": "",
        "use_ddg": True,
        "use_bing": True,
        "cnae": "4781400",
        "started_at": 0.0,
    }


with col_panel:
    st.markdown('<div class="vv-panel-sticky">', unsafe_allow_html=True)

    # Logo (não quebra se não existir)
    logo_path = Path(__file__).parent / "LOGOOFICIALBRANCA.png"
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
    else:
        st.caption("Logo não encontrada (LOGOOFICIALBRANCA.png).")

    st.markdown('<div class="vv-card">', unsafe_allow_html=True)
    st.markdown('<div class="vv-card-title">Configurações</div>', unsafe_allow_html=True)

    tab = st.radio("Seção", ["Prospecção (Lojas)", "CNPJ (Grátis)", "Meta API (Instagram)"], horizontal=False)

    st.markdown('<hr class="vv-hr"/>', unsafe_allow_html=True)

    if tab == "Prospecção (Lojas)":
        cities_input = st.text_area(
            "Cidades (uma por linha ou separadas por vírgula)",
            placeholder="Ex:\nSão Paulo\nCuritiba\nFlorianópolis",
            height=110,
        )
        limit = st.slider("Limite de lojas por cidade", 10, 500, 80, step=10)

        st.markdown('<div class="vv-note">Dica: comece com 30–80 por cidade. Quanto maior, maior a chance de bloqueio em buscadores.</div>', unsafe_allow_html=True)

        st.markdown('<hr class="vv-hr"/>', unsafe_allow_html=True)

        enrich_address = st.checkbox("Completar endereço via OpenStreetMap (Nominatim)", value=True)
        enrich_instagram = st.checkbox("Buscar Instagram (OSM + buscadores)", value=True)

        meta_ok = meta_available()
        enrich_meta = st.checkbox("Enriquecer Instagram via Meta API (seguidores/bio/website)", value=meta_ok, disabled=not meta_ok)
        if not meta_ok:
            st.caption("Meta API desativada: configure os secrets IG_USER_ID e META_USER_TOKEN_LONG para liberar o enriquecimento.")

        col_a, col_b = st.columns(2)
        with col_a:
            use_ddg = st.checkbox("DuckDuckGo", value=True, disabled=not enrich_instagram)
        with col_b:
            use_bing = st.checkbox("Bing", value=True, disabled=not enrich_instagram)

        st.markdown('<hr class="vv-hr"/>', unsafe_allow_html=True)

        # Execução em tempo real: mostra resultados conforme coleta e permite interromper
        is_running = st.session_state.prospect.get("running", False)
        batch_size = st.slider("Atualização em tempo real (itens por passo)", 1, 5, int(st.session_state.prospect.get("batch_size", 2)))
        st.session_state.prospect["batch_size"] = int(batch_size)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            start = st.button("🚀 Iniciar", disabled=is_running)
        with col_btn2:
            stop = st.button("⏹ Parar", disabled=not is_running)

        if stop:
            st.session_state.prospect["stop"] = True
            st.session_state.prospect["running"] = False
            st.session_state.prospect["stopped_reason"] = "Interrompido manualmente"

        st.markdown('</div>', unsafe_allow_html=True)

    elif tab == "CNPJ (Grátis)":
        st.markdown(
            '<div class="vv-note"><b>Enriquecimento de CNPJ (GRÁTIS)</b><br>'
            '<span class="vv-muted">Sem token. O app tenta descobrir o CNPJ por <b>busca pública</b> (DuckDuckGo/Bing) usando <b>Loja + Cidade</b>, e depois consulta dados completos na <b>BrasilAPI</b> (inclui sócios/QSA).</span><br>'
            '<span class="vv-muted">Como não existe um endpoint público gratuito para listar <i>todos</i> os CNPJs por cidade+CNAE em escala, este modo trabalha a partir de uma lista de lojas (da prospecção ou planilha).</span></div>',
            unsafe_allow_html=True,
        )

        cnpj_source = st.radio(
            "Fonte dos leads",
            ["Usar leads da prospecção", "Enviar planilha (Loja + Cidade)"],
            key="cnpj_source_mode",
        )

        cnpj_upload = None
        if cnpj_source == "Enviar planilha (Loja + Cidade)":
            cnpj_upload = st.file_uploader(
                "Envie um CSV/XLSX com colunas: Loja, Cidade",
                type=["csv", "xlsx"],
                key="cnpj_leads_upload",
            )

        cnpj_max = st.slider("Máximo de lojas para tentar", 10, 500, 120, step=10, key="cnpj_max_items")

        st.markdown('<hr class="vv-hr"/>', unsafe_allow_html=True)

        use_ddg_cnpj = st.checkbox("DuckDuckGo (CNPJ)", value=True, key="cnpj_use_ddg")
        use_bing_cnpj = st.checkbox("Bing (CNPJ)", value=True, key="cnpj_use_bing")

        st.markdown('<hr class="vv-hr"/>', unsafe_allow_html=True)

        j = st.session_state.cnpj_job
        is_cnpj_running = bool(j.get("running"))
        batch_size_cnpj = st.slider("Atualização em tempo real (CNPJ por passo)", 1, 5, int(j.get("batch_size", 2)), key="cnpj_batch_size")
        st.session_state.cnpj_job["batch_size"] = int(batch_size_cnpj)
        st.session_state.cnpj_job["use_ddg"] = bool(use_ddg_cnpj)
        st.session_state.cnpj_job["use_bing"] = bool(use_bing_cnpj)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            start_cnpj = st.button("🚀 Iniciar CNPJ", disabled=is_cnpj_running)
        with col_btn2:
            stop_cnpj = st.button("⏹ Parar CNPJ", disabled=not is_cnpj_running)

        if stop_cnpj:
            st.session_state.cnpj_job["stop"] = True
            st.session_state.cnpj_job["running"] = False
            st.session_state.cnpj_job["stopped_reason"] = "Interrompido manualmente"

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown(
            '<div class="vv-note"><b>Meta API (Instagram)</b><br>'
            '<span class="vv-muted">Este app enriquece automaticamente <b>seguidores/bio/website</b> quando o @ já foi encontrado. '
            'Para ativar, configure os secrets: <b>IG_USER_ID</b> e <b>META_USER_TOKEN_LONG</b>.</span></div>',
            unsafe_allow_html=True,
        )

        if meta_available():
            st.success("Meta API pronta ✅ (secrets detectados)")
        else:
            st.warning("Meta API ainda não configurada (secrets ausentes).")

        meta_test_username = st.text_input("Testar username (sem @)", value="oficialversovivo", key="meta_test_username")
        start_meta_test = st.button("🧪 Testar Business Discovery")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Core: Prospecção
# -------------------------
def parse_cities(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r"[,\n;]+", text)
    return [p.strip() for p in parts if p.strip()]



def build_lead_row(
    city: str,
    name: str,
    tags: Dict[str, Any],
    lat: Optional[float],
    lon: Optional[float],
    enrich_address: bool,
    enrich_instagram: bool,
    use_ddg: bool,
    use_bing: bool,
    enrich_meta: bool,
) -> Dict[str, Any]:
    # telefone (OSM)
    phone = tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile") or tags.get("mobile") or "N/A"

    # endereço (OSM tags -> fallback Nominatim)
    addr = format_address_from_tags(tags)
    addr_source = "OSM tags"
    if (not addr or addr == "N/A") and enrich_address and lat is not None and lon is not None:
        nom = nominatim_reverse(lat, lon)
        addr2 = format_address_from_nominatim(nom) if nom else "N/A"
        if addr2 and addr2 != "N/A":
            addr = addr2
            addr_source = "OSM reverse"

    # instagram (handle)
    insta = "N/A"
    insta_source = "N/A"
    if enrich_instagram:
        h = extract_instagram_from_tags(tags)
        if h:
            insta_source = "OSM"
        else:
            h = search_instagram_handle(name, city, enable_ddg=use_ddg, enable_bing=use_bing)
            if h:
                insta_source = "Buscador"
        if h:
            insta = f"@{h}"

    # Meta enrichment (followers/bio/website) — só quando já tem @
    ig_followers = "N/A"
    ig_bio = "N/A"
    ig_website = "N/A"
    ig_meta_status = "N/A"

    if enrich_meta and insta.startswith("@") and meta_available():
        meta = meta_business_discovery(insta[1:])
        if meta:
            ig_followers = meta.get("followers_count", "N/A")
            ig_bio = meta.get("biography", "N/A")
            ig_website = meta.get("website", "N/A")
            ig_meta_status = "OK" if ig_followers != "N/A" or ig_bio != "N/A" or ig_website != "N/A" else "Sem dados"
        else:
            ig_meta_status = "Sem retorno"

    return {
        "Loja": name,
        "Cidade": city,
        "Instagram": insta,
        "Fonte Instagram": insta_source if insta != "N/A" else "N/A",
        "IG Seguidores (Meta)": ig_followers,
        "IG Website (Meta)": ig_website,
        "IG Bio (Meta)": ig_bio,
        "IG Status (Meta)": ig_meta_status if enrich_meta else "Desativado",
        "Telefone": phone,
        "Endereço": addr,
        "Fonte Endereço": addr_source if addr != "N/A" else "N/A",
        "Latitude": lat,
        "Longitude": lon,
    }




# -------------------------
# Execução incremental (streaming) — mostra resultados enquanto coleta
# -------------------------
def start_prospect_run(
    cities: List[str],
    limit: int,
    enrich_address: bool,
    enrich_instagram: bool,
    use_ddg: bool,
    use_bing: bool,
    enrich_meta: bool,
    batch_size: int,
):
    # limpa resultados anteriores
    st.session_state.leads_rows = []
    st.session_state.leads_df = pd.DataFrame()

    p = st.session_state.prospect
    p.update({
        "running": True,
        "stop": False,
        "cities": cities,
        "limit": int(limit),
        "city_idx": 0,
        "store_idx": 0,
        "valid": [],
        "current_city": "",
        "current_name": "",
        "city_total": 0,
        "done": 0,
        "target_est": max(1, len(cities) * int(limit)),
        "started_at": time.time(),
        "enrich_address": bool(enrich_address),
        "enrich_instagram": bool(enrich_instagram),
        "enrich_meta": bool(enrich_meta),
        "use_ddg": bool(use_ddg),
        "use_bing": bool(use_bing),
        "batch_size": int(batch_size) if batch_size else 1,
        "last_error": "",
        "stopped_reason": "",
    })


def _init_city_in_state(p: Dict[str, Any]) -> None:
    # prepara lista de lojas válidas para a cidade atual
    city = p["cities"][p["city_idx"]]
    p["current_city"] = city
    p["current_name"] = "carregando..."
    elements = overpass_query(city)

    valid = []
    for el in elements:
        tags = el.get("tags") or {}
        name = tags.get("name")
        if not name:
            continue
        if is_valid_store(name, tags):
            valid.append(el)

    valid = valid[: p["limit"]]
    p["valid"] = valid
    p["store_idx"] = 0
    p["city_total"] = len(valid)


def prospect_step() -> None:
    """Processa poucos itens por execução para permitir:
    - renderizar resultados em tempo real
    - clicar em Parar sem travar
    """
    p = st.session_state.prospect
    if not p.get("running"):
        return
    if p.get("stop"):
        p["running"] = False
        if not p.get("stopped_reason"):
            p["stopped_reason"] = "Interrompido"
        return

    try:
        batch = max(1, int(p.get("batch_size", 1)))
        for _ in range(batch):
            if p.get("stop"):
                break

            # acabou tudo
            if p["city_idx"] >= len(p["cities"]):
                p["running"] = False
                p["stopped_reason"] = p.get("stopped_reason") or "Concluída"
                return

            # iniciar cidade se necessário
            if not p.get("valid"):
                _init_city_in_state(p)
                # se não achou nada, pula cidade
                if p.get("city_total", 0) == 0:
                    p["city_idx"] += 1
                    p["valid"] = []
                    continue

            # terminou cidade
            if p["store_idx"] >= p["city_total"]:
                p["city_idx"] += 1
                p["valid"] = []
                continue

            el = p["valid"][p["store_idx"]]
            tags = el.get("tags") or {}
            name = tags.get("name") or "N/A"
            lat, lon = extract_lat_lon(el)

            p["current_name"] = name

            row = build_lead_row(
                city=p["current_city"],
                name=name,
                tags=tags,
                lat=lat,
                lon=lon,
                enrich_address=p["enrich_address"],
                enrich_instagram=p["enrich_instagram"],
                use_ddg=p["use_ddg"],
                use_bing=p["use_bing"],
                enrich_meta=p.get("enrich_meta", False),
            )
            st.session_state.leads_rows.append(row)

            p["store_idx"] += 1
            p["done"] += 1

        # atualiza DF parcial
        if st.session_state.leads_rows:
            st.session_state.leads_df = pd.DataFrame(st.session_state.leads_rows)

    except Exception as e:
        p["last_error"] = str(e)
        p["running"] = False
        p["stopped_reason"] = "Erro durante execução"


def run_prospect(cities: List[str], limit: int, enrich_address: bool, enrich_instagram: bool, use_ddg: bool, use_bing: bool) -> pd.DataFrame:
    all_rows = []
    progress = st.progress(0)
    status = st.empty()

    for idx, city in enumerate(cities):
        status.markdown(f"**Buscando em {city}...**")
        elements = overpass_query(city)

        # filtra + limita
        valid = []
        for el in elements:
            tags = el.get("tags") or {}
            name = tags.get("name")
            if not name:
                continue
            if is_valid_store(name, tags):
                valid.append(el)

        valid = valid[:limit]

        for i, el in enumerate(valid, start=1):
            tags = el.get("tags") or {}
            name = tags.get("name") or "N/A"
            lat, lon = extract_lat_lon(el)

            status.markdown(f"**[{city}]** {name}  \n<span class='vv-note'>({i}/{len(valid)})</span>", unsafe_allow_html=True)

            row = build_lead_row(
                city=city,
                name=name,
                tags=tags,
                lat=lat,
                lon=lon,
                enrich_address=enrich_address,
                enrich_instagram=enrich_instagram,
                use_ddg=use_ddg,
                use_bing=use_bing,
                enrich_meta=False,
            )
            all_rows.append(row)

        progress.progress((idx + 1) / max(1, len(cities)))

    status.markdown("✅ **Prospecção concluída!**")
    return pd.DataFrame(all_rows)


# -------------------------
# Core: Enriquecimento CNPJ
# -------------------------
def load_cnpj_from_upload(upload) -> List[str]:
    if upload is None:
        return []
    try:
        if upload.name.lower().endswith(".csv"):
            dfu = pd.read_csv(upload)
        else:
            dfu = pd.read_excel(upload)
    except Exception:
        return []

    # tenta achar coluna
    cols = {c.lower(): c for c in dfu.columns}
    c_col = None
    for cand in ["cnpj", "cnpj_basico", "documento", "document"]:
        if cand in cols:
            c_col = cols[cand]
            break
    if c_col is None:
        # pega primeira coluna
        c_col = dfu.columns[0]

    cnpjs = []
    for v in dfu[c_col].astype(str).tolist():
        d = safe_digits(v)
        if len(d) == 14:
            cnpjs.append(d)
    # dedup
    out = []
    seen = set()
    for c in cnpjs:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def enrich_cnpjs(cnpjs: List[str], allow_set: set) -> pd.DataFrame:
    rows = []
    prog = st.progress(0)
    stat = st.empty()
    for i, c in enumerate(cnpjs, start=1):
        stat.markdown(f"**Consultando CNPJ:** {c} ({i}/{len(cnpjs)})")
        data = brasilapi_cnpj(c)
        if not data:
            rows.append({"CNPJ": c, "Status": "N/A / erro na consulta"})
        else:
            # filtro CNAE
            if not cnae_allowed(data, allow_set):
                rows.append({"CNPJ": c, "Status": "Ignorado (CNAE fora do alvo)"})
            else:
                # Campos principais (mapeamento tolerante)
                rows.append({
                    "CNPJ": data.get("cnpj") or c,
                    "Razão Social": data.get("razao_social") or data.get("razaoSocial") or "N/A",
                    "Nome Fantasia": data.get("nome_fantasia") or data.get("nomeFantasia") or "N/A",
                    "Abertura": data.get("data_inicio_atividade") or data.get("abertura") or "N/A",
                    "Porte": data.get("porte") or data.get("descricao_porte") or "N/A",
                    "MEI": data.get("opcao_pelo_mei") if "opcao_pelo_mei" in data else data.get("mei") or "N/A",
                    "Simples": data.get("opcao_pelo_simples") if "opcao_pelo_simples" in data else data.get("simples") or "N/A",
                    "Capital Social": data.get("capital_social") or "N/A",
                    "Situação": data.get("descricao_situacao_cadastral") or data.get("situacao_cadastral") or "N/A",
                    "UF": data.get("uf") or "N/A",
                    "Município": data.get("municipio") or data.get("cidade") or "N/A",
                    "CEP": data.get("cep") or "N/A",
                    "Logradouro": data.get("logradouro") or "N/A",
                    "Número": data.get("numero") or "N/A",
                    "Bairro": data.get("bairro") or "N/A",
                    "Email": data.get("email") or "N/A",
                    "Telefone": data.get("ddd_telefone_1") or data.get("telefone") or "N/A",
                    "CNAE Principal": data.get("cnae_fiscal") or "N/A",
                    "CNAE Principal Desc": data.get("cnae_fiscal_descricao") or "N/A",
                    "CNAEs Secundários": "; ".join(
                        [f"{x.get('codigo','')} {x.get('descricao','')}".strip() for x in (data.get("cnaes_secundarios") or []) if isinstance(x, dict)]
                    ) or "N/A",
                    "Status": "OK",
                })
        prog.progress(i / max(1, len(cnpjs)))
    stat.markdown("✅ **Consulta concluída!**")
    return pd.DataFrame(rows)


# -------------------------
# Main render
# -------------------------
with col_main:
    if tab == "Prospecção (Lojas)":
        st.markdown("## Sua ferramenta para encontrar lojistas multimarcas")

        # Rodar (streaming + possibilidade de parar)
        p = st.session_state.prospect

        if "start" in locals() and start:
            cities = parse_cities(cities_input)
            if not cities:
                st.warning("Digite pelo menos uma cidade.")
            else:
                # inicia execução incremental
                start_prospect_run(
                    cities=cities,
                    limit=limit,
                    enrich_address=enrich_address,
                    enrich_instagram=enrich_instagram,
                    use_ddg=use_ddg,
                    use_bing=use_bing,
                    enrich_meta=enrich_meta,
                    batch_size=batch_size if "batch_size" in locals() else 2,
                )
                st.rerun()

        # processa um passo por execução (para exibir resultados antes de terminar tudo)
        if p.get("running"):
            prospect_step()

        df = st.session_state.leads_df
        running = bool(p.get("running"))

        # Status em tempo real (para você decidir parar cedo se estiver vindo muito N/A)
        if running:
            prog = min(1.0, float(p.get("done", 0)) / max(1.0, float(p.get("target_est", 1))))
            st.progress(prog)
            city_total = int(p.get("city_total") or 0)
            city_total = city_total if city_total > 0 else 1
            st.markdown(f"**[{p.get('current_city','')}]** {p.get('current_name','')}  \\n({min(int(p.get('store_idx',0)), city_total)}/{city_total})")
            st.caption("Se você notar muitos campos N/A, clique em **Parar** no painel para interromper e ajustar.")
            if p.get("last_error"):
                st.error(p.get("last_error"))
        else:
            # Mensagem pós-execução
            if p.get("stopped_reason") and p.get("cities"):
                if p.get("stopped_reason") == "Concluída":
                    st.success("✅ Prospecção concluída!")
                else:
                    st.warning(f"⏹ {p.get('stopped_reason')}")


        if df is None:
            st.info("Configure as cidades no painel à direita e clique em **Iniciar prospecção**.")
        elif df.empty:
            if running:
                st.info("Coletando resultados… assim que entrar o primeiro lead ele aparece aqui.")
            else:
                st.warning("Nenhuma loja encontrada com os filtros atuais.")
        else:
            total = len(df)
            with_insta = int((df["Instagram"] != "N/A").sum())
            with_addr = int((df["Endereço"] != "N/A").sum())
            with_phone = int((df["Telefone"] != "N/A").sum())
            with_meta = int((df.get("IG Status (Meta)", pd.Series([], dtype=str)) == "OK").sum()) if "IG Status (Meta)" in df else 0

            st.markdown(
                f"""
<div class="vv-chip-row">
  <div class="vv-chip"><span>Total</span> {total}</div>
  <div class="vv-chip"><span>Instagram</span> {with_insta}</div>
  <div class="vv-chip"><span>Meta</span> {with_meta}</div>
  <div class="vv-chip"><span>Endereço</span> {with_addr}</div>
  <div class="vv-chip"><span>Telefone</span> {with_phone}</div>
</div>
<hr class="vv-hr"/>
""",
                unsafe_allow_html=True,
            )
            # Visão rápida durante execução (para você notar N/A cedo)
            if running:
                st.dataframe(df.tail(50), use_container_width=True, hide_index=True)
                st.caption("Mostrando os 50 últimos resultados coletados (atualiza em tempo real).")
                st.markdown("<hr class='vv-hr'/>", unsafe_allow_html=True)



            # Render cards
            # Durante a execução, renderiza só os últimos itens (evita ficar pesado e garante atualização rápida).
            iter_df = df.tail(12) if running else df

            for _, r in iter_df.iterrows():
                loja = str(r["Loja"])
                cidade = str(r["Cidade"])
                insta = str(r["Instagram"])
                ig_followers = str(r.get("IG Seguidores (Meta)", "N/A"))
                ig_website = str(r.get("IG Website (Meta)", "N/A"))
                ig_bio = str(r.get("IG Bio (Meta)", "N/A"))
                phone = str(r["Telefone"])
                addr = str(r["Endereço"])
                lat = r.get("Latitude")
                lon = r.get("Longitude")

                avatar = initials(loja)

                insta_url = f"https://instagram.com/{insta[1:]}" if insta.startswith("@") else ""
                maps_q = addr if addr != "N/A" else f"{loja} {cidade}"
                maps_url = maps_link(maps_q)

                site_btn = f"<a class='vv-link-pill vv-link-muted' href='{ig_website}' target='_blank'>Ver Site</a>" if ig_website != "N/A" else ""
                bio_snip = ig_bio
                if bio_snip and bio_snip != "N/A" and len(bio_snip) > 180:
                    bio_snip = bio_snip[:180] + "…"
                bio_html = f"<div style='margin-top:10px; font-size:13px; color:#444;'><b>Bio:</b> {bio_snip}</div>" if bio_snip and bio_snip != "N/A" else ""

                st.markdown(
                    f"""
<div class="vv-lead">
  <div class="vv-lead-header">
    <div class="vv-lead-left">
      <div class="vv-avatar"><div class="vv-avatar-inner">{avatar}</div></div>
      <div style="min-width:0;">
        <p class="vv-lead-name">{loja}</p>
        <p class="vv-lead-city">{cidade}</p>
      </div>
    </div>
  </div>

  <div class="vv-chip-row">
    <div class="vv-chip"><span>Instagram</span> {insta}</div>
    <div class="vv-chip"><span>Seguidores</span> {ig_followers}</div>
    <div class="vv-chip"><span>Telefone</span> {phone}</div>
  </div>

  <div style="margin-top:10px; font-size:13px;">
    <b>Endereço:</b> {addr}
  </div>

  {bio_html}

  <div class="vv-actions">
    {"<a class='vv-link-pill vv-link-primary' href='"+insta_url+"' target='_blank'>Ver Instagram</a>" if insta_url else "<span class='vv-link-pill vv-link-muted'>Sem Instagram</span>"}
    {site_btn}
        <a class="vv-link-pill vv-link-muted" href="{maps_url}" target="_blank">Ver no Maps</a>
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )

            if not running:
                # Download
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Leads")

                st.download_button(
                    "📥 Baixar Planilha Excel (.xlsx)",
                    data=output.getvalue(),
                    file_name="leads_verso_vivo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.caption("Download será liberado ao concluir ou ao parar a prospecção.")


        # Continua rodando automaticamente (1–5 itens por passo) para atualizar o feed em tempo real.
        # Assim você consegue interromper cedo se perceber muitos N/A.
        if st.session_state.prospect.get("running"):
            time.sleep(0.25)
            st.rerun()

    
    elif tab == "CNPJ (Grátis)":
        st.markdown("## Enriquecimento de CNPJ (GRÁTIS) — por lista de lojas")
        st.caption("O app tenta descobrir o CNPJ por busca pública (DDG/Bing) e consulta dados completos via BrasilAPI (inclui sócios/QSA).")

        j = st.session_state.cnpj_job

        # Iniciar
        if "start_cnpj" in locals() and start_cnpj:
            items: List[Dict[str, str]] = []

            if "cnpj_source" in locals() and cnpj_source == "Usar leads da prospecção":
                df_leads = st.session_state.leads_df
                if df_leads is None or df_leads.empty:
                    st.warning("Você ainda não tem leads. Rode a **Prospecção (Lojas)** primeiro.")
                else:
                    tmp = df_leads[["Loja", "Cidade"]].dropna()
                    for _, rr in tmp.iterrows():
                        items.append({"Loja": str(rr["Loja"]), "Cidade": str(rr["Cidade"])})
            else:
                # upload de planilha com Loja/Cidade
                up = cnpj_upload if "cnpj_upload" in locals() else None
                if up is None:
                    st.warning("Envie uma planilha com as colunas **Loja** e **Cidade**.")
                else:
                    try:
                        if up.name.lower().endswith(".csv"):
                            dfu = pd.read_csv(up)
                        else:
                            dfu = pd.read_excel(up)
                    except Exception:
                        dfu = pd.DataFrame()

                    if dfu.empty:
                        st.warning("Não consegui ler o arquivo. Confirme se é CSV/XLSX válido.")
                    else:
                        cols = {c.lower(): c for c in dfu.columns}
                        loja_col = cols.get("loja") or cols.get("nome") or cols.get("store") or None
                        cidade_col = cols.get("cidade") or cols.get("city") or None
                        if not loja_col or not cidade_col:
                            st.warning("A planilha precisa ter colunas chamadas **Loja** e **Cidade** (ou equivalentes).")
                        else:
                            for _, rr in dfu[[loja_col, cidade_col]].dropna().iterrows():
                                items.append({"Loja": str(rr[loja_col]), "Cidade": str(rr[cidade_col])})

            max_items = int(cnpj_max) if "cnpj_max" in locals() else 120
            items = items[:max_items]

            if items:
                start_cnpj_run(
                    items=items,
                    batch_size=int(j.get("batch_size", 2)),
                    use_ddg=bool(j.get("use_ddg", True)),
                    use_bing=bool(j.get("use_bing", True)),
                )
                st.rerun()

        # processa um passo (streaming)
        if j.get("running"):
            cnpj_step()

        dfc = st.session_state.cnpj_df
        running = bool(j.get("running"))

        if running:
            done = int(j.get("idx", 0))
            total = int(j.get("target_est", 1)) or 1
            st.progress(min(1.0, done / total))
            st.markdown(f"**Processando:** {j.get('current','')}  \n({done}/{total})")
            st.caption("Se começar a vir muito 'CNPJ não encontrado', clique em **Parar CNPJ** no painel e ajuste o volume/termos.")
            if j.get("last_error"):
                st.error(j.get("last_error"))
        else:
            if j.get("stopped_reason"):
                if j.get("stopped_reason") == "Concluída":
                    st.success("✅ Enriquecimento de CNPJ concluído!")
                else:
                    st.warning(f"⏹ {j.get('stopped_reason')}")

        if dfc is None or dfc.empty:
            st.info("Escolha a fonte no painel e clique em **Iniciar CNPJ**.")
        else:
            total = len(dfc)
            ok = int((dfc.get("Status", pd.Series([], dtype=str)) == "OK").sum()) if "Status" in dfc else 0
            found = int((dfc.get("CNPJ", pd.Series([], dtype=str)).astype(str) != "N/A").sum()) if "CNPJ" in dfc else 0

            st.markdown(
                f"""
<div class="vv-chip-row">
  <div class="vv-chip"><span>Total</span> {total}</div>
  <div class="vv-chip"><span>CNPJ</span> {found}</div>
  <div class="vv-chip"><span>OK</span> {ok}</div>
</div>
<hr class="vv-hr"/>
""",
                unsafe_allow_html=True,
            )

            st.dataframe(dfc.tail(80) if running else dfc, use_container_width=True, hide_index=True)

            if not running:
                out = BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as writer:
                    dfc.to_excel(writer, index=False, sheet_name="Empresas")
                st.download_button(
                    "📥 Baixar Planilha Empresas (.xlsx)",
                    data=out.getvalue(),
                    file_name="empresas_cnae_4781400.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.caption("Download será liberado ao concluir ou ao parar o enriquecimento.")

        if running:
            time.sleep(0.25)
            st.rerun()

    else:
        st.markdown("## Meta API (Instagram) — teste e diagnóstico")
        ig_id, token = get_meta_credentials()
        if ig_id and token:
            st.success("Secrets detectados ✅")
            st.caption(f"IG_USER_ID: {ig_id}")
        else:
            st.warning("Configure os secrets IG_USER_ID e META_USER_TOKEN_LONG para usar a Meta API.")

        u = meta_test_username if "meta_test_username" in locals() else "oficialversovivo"
        if "start_meta_test" in locals() and start_meta_test:
            res = meta_business_discovery(u)
            raw = res.get("raw") if isinstance(res, dict) else res
            st.json(raw if raw else res)
        else:
            st.info("Use o painel para testar um username e validar se o Business Discovery está respondendo.")
