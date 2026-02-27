import streamlit as st
import pandas as pd
import requests
import re
import time
import random
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
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


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

    tab = st.radio("Seção", ["Prospecção (Lojas)", "Enriquecimento CNPJ"], horizontal=False)

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

        col_a, col_b = st.columns(2)
        with col_a:
            use_ddg = st.checkbox("DuckDuckGo", value=True, disabled=not enrich_instagram)
        with col_b:
            use_bing = st.checkbox("Bing", value=True, disabled=not enrich_instagram)

        st.markdown('<hr class="vv-hr"/>', unsafe_allow_html=True)

        start = st.button("🚀 Iniciar prospecção")

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown('<div class="vv-note">Aqui você gera planilhas de empresas a partir de <b>CNPJ</b>. Você pode colar CNPJs ou subir um CSV/XLSX exportado de plataformas que você tem acesso.</div>', unsafe_allow_html=True)

        cnpj_text = st.text_area(
            "Cole CNPJs (um por linha)",
            placeholder="Ex:\n12.345.678/0001-90\n00.394.460/0058-87",
            height=120,
        )

        up = st.file_uploader("Ou envie CSV/XLSX com uma coluna de CNPJ", type=["csv", "xlsx"])

        allow_cnae = st.text_input(
            "CNAEs permitidos (somente dígitos, separados por vírgula)",
            value="4781400",
            help="Padrão: 4781400 (Comércio varejista de artigos do vestuário e acessórios).",
        )

        run_cnpj = st.button("🔎 Enriquecer CNPJs")

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


def build_lead_row(city: str, name: str, tags: Dict[str, Any], lat: Optional[float], lon: Optional[float],
                   enrich_address: bool, enrich_instagram: bool, use_ddg: bool, use_bing: bool) -> Dict[str, Any]:
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

    # instagram
    insta = "N/A"
    if enrich_instagram:
        h = extract_instagram_from_tags(tags)
        if not h:
            h = search_instagram_handle(name, city, enable_ddg=use_ddg, enable_bing=use_bing)
        if h:
            insta = f"@{h}"

    return {
        "Loja": name,
        "Cidade": city,
        "Instagram": insta,
        "Telefone": phone,
        "Endereço": addr,
        "Fonte Endereço": addr_source if addr != "N/A" else "N/A",
        "Latitude": lat,
        "Longitude": lon,
    }


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

        # Rodar
        if "start" in locals() and start:
            cities = parse_cities(cities_input)
            if not cities:
                st.warning("Digite pelo menos uma cidade.")
            else:
                df = run_prospect(
                    cities=cities,
                    limit=limit,
                    enrich_address=enrich_address,
                    enrich_instagram=enrich_instagram,
                    use_ddg=use_ddg,
                    use_bing=use_bing,
                )
                st.session_state.leads_df = df

        df = st.session_state.leads_df
        if df is None:
            st.info("Configure as cidades no painel à direita e clique em **Iniciar prospecção**.")
        elif df.empty:
            st.warning("Nenhuma loja encontrada com os filtros atuais.")
        else:
            total = len(df)
            with_insta = int((df["Instagram"] != "N/A").sum())
            with_addr = int((df["Endereço"] != "N/A").sum())
            with_phone = int((df["Telefone"] != "N/A").sum())

            st.markdown(
                f"""
<div class="vv-chip-row">
  <div class="vv-chip"><span>Total</span> {total}</div>
  <div class="vv-chip"><span>Instagram</span> {with_insta}</div>
  <div class="vv-chip"><span>Endereço</span> {with_addr}</div>
  <div class="vv-chip"><span>Telefone</span> {with_phone}</div>
</div>
<hr class="vv-hr"/>
""",
                unsafe_allow_html=True,
            )

            # Render cards
            for _, r in df.iterrows():
                loja = str(r["Loja"])
                cidade = str(r["Cidade"])
                insta = str(r["Instagram"])
                phone = str(r["Telefone"])
                addr = str(r["Endereço"])
                lat = r.get("Latitude")
                lon = r.get("Longitude")

                avatar = initials(loja)

                insta_url = f"https://instagram.com/{insta[1:]}" if insta.startswith("@") else ""
                maps_q = addr if addr != "N/A" else f"{loja} {cidade}"
                maps_url = maps_link(maps_q)

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
    <div class="vv-chip"><span>Telefone</span> {phone}</div>
  </div>

  <div style="margin-top:10px; font-size:13px;">
    <b>Endereço:</b> {addr}
  </div>

  <div class="vv-actions">
    {"<a class='vv-link-pill vv-link-primary' href='"+insta_url+"' target='_blank'>Ver Instagram</a>" if insta_url else "<span class='vv-link-pill vv-link-muted'>Sem Instagram</span>"}
    <a class="vv-link-pill vv-link-muted" href="{maps_url}" target="_blank">Ver no Maps</a>
  </div>
</div>
""",
                    unsafe_allow_html=True,
                )

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
        st.markdown("## Enriquecimento de empresas por CNPJ")
        st.caption("Fonte: BrasilAPI (consulta por CNPJ). Você fornece os CNPJs (colando ou subindo um arquivo exportado).")

        if "run_cnpj" in locals() and run_cnpj:
            allow = {safe_digits(x) for x in allow_cnae.split(",") if safe_digits(x)}
            if not allow:
                allow = set(DEFAULT_CNAE_ALLOW)

            cnpjs = []
            if cnpj_text.strip():
                for line in re.split(r"[,\n;]+", cnpj_text):
                    d = safe_digits(line)
                    if len(d) == 14:
                        cnpjs.append(d)
            if up is not None:
                cnpjs.extend(load_cnpj_from_upload(up))

            # dedup
            seen = set()
            cnpjs = [c for c in cnpjs if not (c in seen or seen.add(c))]

            if not cnpjs:
                st.warning("Informe ao menos um CNPJ válido (14 dígitos).")
            else:
                dfc = enrich_cnpjs(cnpjs, allow)
                st.session_state.cnpj_df = dfc

        dfc = st.session_state.cnpj_df
        if dfc is None:
            st.info("Cole CNPJs ou envie um arquivo no painel à direita e clique em **Enriquecer CNPJs**.")
        else:
            st.dataframe(dfc, use_container_width=True, hide_index=True)

            out = BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                dfc.to_excel(writer, index=False, sheet_name="CNPJs")

            st.download_button(
                "📥 Baixar Planilha CNPJ (.xlsx)",
                data=out.getvalue(),
                file_name="cnpjs_verso_vivo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
