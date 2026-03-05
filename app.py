
import streamlit as st
import pandas as pd
import requests
import re
import time
import unicodedata
import zipfile
import io
from io import BytesIO
from urllib.parse import quote_plus
from typing import Optional, Dict, Any, List

st.set_page_config(page_title="Verso Sourcing Pro", page_icon="✨", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root{--bg:#fafafa;--card:#fff;--text:#111;--muted:#6b7280;--border:#e5e7eb;--accent:#111;--radius:18px;--shadow:0 8px 24px rgba(17,17,17,0.06);--shadow-soft:0 1px 0 rgba(0,0,0,0.03);}
html,body,[class*="st-"]{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",Arial,sans-serif!important;color:var(--text);}
.stApp{background:var(--bg);}
.main .block-container{max-width:1280px;padding-top:1rem;padding-bottom:2rem;}
#MainMenu,footer,header{visibility:hidden;}
.vv-topbar{position:sticky;top:0;z-index:999;background:rgba(250,250,250,0.92);backdrop-filter:blur(12px);border-bottom:1px solid var(--border);margin:-1rem -1rem 1.5rem -1rem;padding:14px 0;}
.vv-topbar-inner{max-width:1280px;margin:0 auto;padding:0 1rem;display:flex;align-items:center;justify-content:space-between;}
.vv-brand h1{font-size:18px;margin:0;font-weight:900;letter-spacing:-.3px;}
.vv-brand p{margin:0;font-size:12px;color:var(--muted);}
.vv-pill{display:inline-flex;align-items:center;border-radius:999px;padding:8px 14px;border:1px solid var(--border);background:var(--card);font-size:11px;font-weight:800;}
.stTextInput>div>div>input,.stTextArea textarea{border-radius:14px!important;border:1px solid var(--border)!important;background:var(--card)!important;padding:11px 12px!important;font-size:14px!important;box-shadow:none!important;}
.stSelectbox>div>div>div{border-radius:14px!important;border:1px solid var(--border)!important;background:var(--card)!important;font-size:14px!important;box-shadow:none!important;}
.stButton>button{width:100%;border-radius:999px!important;border:1px solid transparent!important;background:var(--accent)!important;color:#fff!important;font-weight:900!important;height:44px!important;box-shadow:none!important;font-size:14px!important;transition:filter .12s,transform .12s;}
.stButton>button:hover{filter:brightness(.95);transform:translateY(-1px);}
.stButton>button:disabled{opacity:.55!important;}
.vv-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:18px;box-shadow:var(--shadow-soft);margin-bottom:14px;}
.vv-card:hover{box-shadow:var(--shadow);}
.vv-lead-name{font-size:15px;font-weight:950;margin:0;}
.vv-lead-city{font-size:12px;color:var(--muted);margin:0;}
.vv-chip-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
.vv-chip{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:6px 10px;background:#f3f4f6;border:1px solid #f3f4f6;font-size:12px;font-weight:700;}
.vv-chip span{color:#9ca3af;}
.vv-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;}
.vv-link-pill{display:inline-flex;align-items:center;border-radius:999px;padding:8px 14px;font-size:12px;font-weight:950;border:1px solid var(--border);background:#fff;color:var(--text)!important;text-decoration:none!important;}
.vv-link-pill:hover{filter:brightness(.97);}
.vv-link-primary{background:#111;border-color:#111;color:#fff!important;}
.vv-link-muted{background:#f3f4f6;border-color:#f3f4f6;}
.vv-hr{border:none;border-top:1px solid #f1f1f1;margin:14px 0;}
.vv-dots{display:flex;gap:3px;align-items:center;}
.vv-dot{width:7px;height:7px;border-radius:50%;}
.vv-avatar{width:44px;height:44px;border-radius:50%;flex-shrink:0;background:radial-gradient(circle at 30% 30%,#feda75 0%,#fa7e1e 30%,#d62976 55%,#962fbf 75%,#4f5bd5 100%);display:flex;align-items:center;justify-content:center;}
.vv-avatar-inner{width:40px;height:40px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;font-weight:950;font-size:13px;color:#111;}
div[data-testid="stDataFrame"]{border-radius:var(--radius);overflow:hidden;border:1px solid var(--border);}
</style>
""", unsafe_allow_html=True)

# ── Secrets ───────────────────────────────────────────────────────────────────
def secret(k):
    try: return st.secrets.get(k)
    except: return None

ANTHROPIC_KEY = secret("ANTHROPIC_API_KEY")
META_TOKEN    = secret("META_USER_TOKEN_LONG")
GOOGLE_KEY    = secret("GOOGLE_PLACES_KEY")
IG_USER_ID    = secret("IG_USER_ID") or "17841473844567187"

# ── Helpers ───────────────────────────────────────────────────────────────────
SESSION = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/123.0", "Accept-Language": "pt-BR,pt;q=0.9"}

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).strip().lower()

def initials(name):
    p = [x for x in re.split(r"\s+", (name or "").strip()) if x]
    if not p: return "VV"
    if len(p) == 1: return p[0][:2].upper()
    return (p[0][0] + p[-1][0]).upper()

def maps_link(q): return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"
def ig_link(h): return f"https://instagram.com/{h.lstrip('@')}" if h and h not in ("N/A","") else ""

def quality_score(row: dict) -> int:
    return sum(1 for k in ["Instagram","Telefone","Endereço","IG Seguidores","Website"] if row.get(k,"N/A") not in ("N/A",""))

def quality_dots_html(score: int) -> str:
    color = "#22c55e" if score >= 4 else "#f59e0b" if score >= 2 else "#ef4444"
    dots = "".join(f'<div class="vv-dot" style="background:{color if i < score else "#e5e7eb"}"></div>' for i in range(5))
    return f'<div class="vv-dots">{dots}<span style="font-size:11px;color:#9ca3af;margin-left:4px">{score}/5</span></div>'

def source_badge(source: str) -> str:
    colors = {
        "OSM": "#dbeafe|#1d4ed8",
        "Google Places": "#fef9c3|#92400e",
        "Claude Search": "#f3e8ff|#7e22ce",
        "Site da loja": "#dcfce7|#166534",
        "Receita Federal": "#fee2e2|#991b1b",
        "N/A": "#f3f4f6|#9ca3af"
    }
    bg, fg = colors.get(source, "#f3f4f6|#9ca3af").split("|")
    return f'<span style="border-radius:999px;padding:2px 8px;font-size:10px;font-weight:700;background:{bg};color:{fg};border:1px solid {fg}33">{source}</span>'

# ── Filtros OSM ───────────────────────────────────────────────────────────────
EXCLUDE_BRANDS = {"renner","c&a","cea","zara","riachuelo","marisa","pernambucanas","havan","hering","colcci","hope","intimissimi","calzedonia","nike","adidas","puma","arezzo","schutz","anacapri","loungerie","lacoste","tommy","tommy hilfiger","le lis","lelis","animale","farm","dress to","dressto","john john","ellus"}
FOOD_WORDS = {"restaurante","pizza","pizzaria","hamburguer","hamburgueria","burger","bar","pub","café","cafe","cafeteria","padaria","confeitaria","açaí","acai","sorveteria","sushi","japa","yakisoba","churrascaria","lanchonete","bistrô","bistro"}

def is_food(name, tags):
    n = norm(name)
    if any(w in n for w in FOOD_WORDS): return True
    return norm(str(tags.get("amenity",""))) in {"restaurant","cafe","bar","fast_food","pub","ice_cream"}

def is_excluded(name, tags):
    n = norm(name); brand = norm(str(tags.get("brand","")))
    return any(b in n or b in brand for b in EXCLUDE_BRANDS)

def is_valid_store(name, tags):
    if not name or is_food(name, tags) or is_excluded(name, tags): return False
    n = norm(name)
    if any(k in n for k in ["multimarca","boutique","moda","fashion","vestuario","feminina","looks","vestuário"]): return True
    return norm(str(tags.get("shop",""))) in {"boutique","clothes","apparel","fashion","clothing"}

# ── OSM / Nominatim ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def overpass_query(city: str) -> list:
    q = f'[out:json][timeout:90];area["name"="{city}"]["boundary"="administrative"]->.s;(nwr["shop"~"clothes|boutique|apparel|fashion|clothing"](area.s););out tags center;'
    try:
        r = SESSION.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=HEADERS, timeout=90)
        return r.json().get("elements", []) if r.ok else []
    except: return []

def extract_coords(el):
    if el.get("type") == "node": return el.get("lat"), el.get("lon")
    c = el.get("center") or {}
    return c.get("lat"), c.get("lon")

def addr_from_tags(tags):
    parts = [f"{tags.get('addr:street','')} {tags.get('addr:housenumber','')}".strip(),
             tags.get("addr:suburb",""), tags.get("addr:city",""), tags.get("addr:state","")]
    return ", ".join(p for p in parts if p).strip() or None

def ig_from_tags(tags):
    for k in ("contact:instagram","instagram","contact:insta","insta"):
        v = tags.get(k)
        if v:
            v = re.sub(r"https?://(www\.)?instagram\.com/","", str(v)).strip("/").strip()
            if v: return v
    return None

@st.cache_data(ttl=86400, show_spinner=False)
def nominatim_reverse(lat: float, lon: float) -> Optional[dict]:
    time.sleep(1.1)
    try:
        r = SESSION.get("https://nominatim.openstreetmap.org/reverse",
            params={"format":"jsonv2","lat":lat,"lon":lon,"addressdetails":1,"accept-language":"pt-BR"},
            headers=HEADERS, timeout=20)
        return r.json() if r.ok else None
    except: return None

def addr_from_nominatim(data):
    if not data: return None
    a = data.get("address") or {}
    road = a.get("road") or a.get("pedestrian") or ""
    parts = [f"{road} {a.get('house_number','')}".strip(),
             a.get("suburb") or a.get("neighbourhood",""),
             a.get("city") or a.get("town") or a.get("village",""),
             a.get("state","")]
    return ", ".join(p for p in parts if p).strip() or data.get("display_name")

# ── Receita Federal — Dados Abertos ──────────────────────────────────────────
# Layout do arquivo Estabelecimentos (separado por ";"):
# 0:cnpj_basico 1:cnpj_ordem 2:cnpj_dv 3:identificador_matriz_filial
# 4:nome_fantasia 5:situacao_cadastral 6:data_situacao 7:motivo_situacao
# 8:nome_cidade_exterior 9:pais 10:data_inicio_atividade
# 11:cnae_fiscal_principal 12:cnae_fiscal_secundaria
# 13:tipo_logradouro 14:logradouro 15:numero 16:complemento
# 17:bairro 18:cep 19:uf 20:municipio(cod) 21:ddd1 22:telefone1
# 23:ddd2 24:telefone2 25:ddd_fax 26:fax 27:email 28:situacao_especial 29:data_situacao_especial

RF_BASE_URL = "https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj"

@st.cache_data(ttl=3600, show_spinner=False)
def get_rf_latest_folder() -> str:
    """Descobre a pasta mais recente nos dados abertos da Receita Federal."""
    try:
        r = SESSION.get(RF_BASE_URL + "/", headers=HEADERS, timeout=20)
        folders = re.findall(r'href="(\d{4}-\d{2})/"', r.text)
        return sorted(folders)[-1] if folders else "2025-01"
    except:
        return "2025-01"

@st.cache_data(ttl=3600, show_spinner=False)
def get_municipios_rf() -> Dict[str, str]:
    """Baixa tabela de municípios da RF (código IBGE → nome) para resolver filtro."""
    try:
        folder = get_rf_latest_folder()
        url = f"{RF_BASE_URL}/{folder}/Municipios.zip"
        r = SESSION.get(url, headers=HEADERS, timeout=60)
        if not r.ok: return {}
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            fname = z.namelist()[0]
            with z.open(fname) as f:
                df = pd.read_csv(f, sep=";", header=None, dtype=str, encoding="latin-1")
        # colunas: codigo, descricao
        return {row[0].strip(): norm(row[1].strip()) for _, row in df.iterrows() if len(row) >= 2}
    except:
        return {}

def find_municipio_code(cidade: str, municipios: Dict[str, str]) -> Optional[str]:
    """Acha o código do município pelo nome (normalizado)."""
    cidade_norm = norm(cidade.split(",")[0].strip())
    for code, nome in municipios.items():
        if nome == cidade_norm:
            return code
    # tentativa parcial
    for code, nome in municipios.items():
        if cidade_norm in nome:
            return code
    return None

def buscar_cnpjs_receita_federal(
    cidade: str,
    cnae: str = "4781400",
    limite: int = 200,
    progress_cb=None
) -> List[Dict]:
    """
    Baixa os arquivos de Estabelecimentos da RF em chunks,
    filtrando por CNAE + município sem carregar tudo na memória.
    Retorna lista de dicts com dados básicos.
    """
    folder = get_rf_latest_folder()

    # resolve código do município
    if progress_cb: progress_cb(0.02, "Carregando tabela de municípios…")
    municipios = get_municipios_rf()
    cod_municipio = find_municipio_code(cidade, municipios)
    if not cod_municipio:
        return []

    resultados = []
    # São 10 arquivos: Estabelecimentos0.zip … Estabelecimentos9.zip
    for i in range(10):
        if len(resultados) >= limite: break
        if progress_cb: progress_cb(0.05 + i * 0.09, f"Lendo arquivo {i+1}/10 da Receita Federal…")

        url = f"{RF_BASE_URL}/{folder}/Estabelecimentos{i}.zip"
        try:
            r = SESSION.get(url, headers=HEADERS, timeout=120, stream=True)
            if not r.ok: continue

            raw = BytesIO()
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                raw.write(chunk)
            raw.seek(0)

            with zipfile.ZipFile(raw) as z:
                fname = z.namelist()[0]
                with z.open(fname) as f:
                    # lê em chunks para economizar memória
                    for chunk_df in pd.read_csv(
                        f, sep=";", header=None, dtype=str,
                        encoding="latin-1", chunksize=50_000
                    ):
                        # filtros: CNAE principal (col 11) + município (col 20) + situação ativa "02" (col 5)
                        mask = (
                            (chunk_df[11].str.strip() == cnae) &
                            (chunk_df[20].str.strip() == cod_municipio) &
                            (chunk_df[5].str.strip() == "02")
                        )
                        filtered = chunk_df[mask]
                        for _, row in filtered.iterrows():
                            cnpj_full = f"{str(row[0]).zfill(8)}{str(row[1]).zfill(4)}{str(row[2]).zfill(2)}"
                            ddd1 = str(row[21]).strip() if pd.notna(row[21]) else ""
                            tel1 = str(row[22]).strip() if pd.notna(row[22]) else ""
                            telefone = f"({ddd1}) {tel1}".strip("() ") if ddd1 and tel1 else "N/A"
                            logradouro = str(row[13]).strip() + " " + str(row[14]).strip()
                            numero = str(row[15]).strip() if pd.notna(row[15]) else ""
                            bairro = str(row[17]).strip() if pd.notna(row[17]) else ""
                            uf = str(row[19]).strip() if pd.notna(row[19]) else ""
                            cep = str(row[18]).strip() if pd.notna(row[18]) else ""
                            nome_fantasia = str(row[4]).strip() if pd.notna(row[4]) else ""
                            email = str(row[27]).strip() if pd.notna(row[27]) else "N/A"

                            resultados.append({
                                "CNPJ": cnpj_full,
                                "Nome Fantasia": nome_fantasia or "N/A",
                                "Abertura": str(row[10]).strip() if pd.notna(row[10]) else "N/A",
                                "Situação": "ATIVA",
                                "Telefone": telefone,
                                "Email": email if email and email != "nan" else "N/A",
                                "UF": uf,
                                "Logradouro": logradouro.strip() or "N/A",
                                "Número": numero or "N/A",
                                "Bairro": bairro or "N/A",
                                "CEP": cep or "N/A",
                                "CNAE Principal": cnae,
                                "Instagram": "N/A",
                                "Website": "N/A",
                                "Razão Social": "N/A",
                                "Sócios (QSA)": "N/A",
                                "Status": "RF",
                            })
                            if len(resultados) >= limite: break
                        if len(resultados) >= limite: break
        except Exception as e:
            continue

    return resultados[:limite]

# ── Google Places ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def google_places_search(name: str, city: str) -> Optional[dict]:
    if not GOOGLE_KEY: return None
    try:
        time.sleep(0.3)
        r = SESSION.get("https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": f"{name} {city} loja de roupa", "language": "pt-BR", "key": GOOGLE_KEY}, timeout=15)
        if not r.ok: return None
        results = r.json().get("results", [])
        if not results: return None
        place_id = results[0].get("place_id")
        if not place_id: return None
        r2 = SESSION.get("https://maps.googleapis.com/maps/api/place/details/json",
            params={"place_id": place_id, "fields": "name,formatted_phone_number,website,formatted_address", "language": "pt-BR", "key": GOOGLE_KEY}, timeout=15)
        return r2.json().get("result") if r2.ok else None
    except: return None

def extract_ig_from_website(website: str) -> Optional[str]:
    if not website or website == "N/A": return None
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", website)
    if m:
        h = m.group(1)
        if h.lower() not in {"p","reel","stories","explore"}: return h
    try:
        time.sleep(0.5)
        r = SESSION.get(website, headers=HEADERS, timeout=10)
        if not r.ok: return None
        skip = {"p","reel","reels","stories","explore","accounts","about","sharer"}
        for h in re.findall(r"instagram\.com/([A-Za-z0-9._]+)", r.text):
            if h.lower() not in skip and len(h) > 2: return h
    except: pass
    return None

# ── Claude Search ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=43200, show_spinner=False)
def claude_search_instagram(store_name: str, city: str, website: str = "") -> Optional[str]:
    if not ANTHROPIC_KEY: return None
    context = f"O site da loja é {website}. " if website and website != "N/A" else ""
    try:
        r = SESSION.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-opus-4-5", "max_tokens": 200,
                  "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                  "messages": [{"role": "user", "content":
                      f'{context}Pesquise o Instagram da loja "{store_name}" em {city}, Brasil. '
                      f'Retorne APENAS o handle (sem @ e sem URL). Se não encontrar, retorne: null'}]},
            timeout=30)
        if not r.ok: return None
        text = " ".join(b.get("text","") for b in r.json().get("content",[]) if b.get("type")=="text").strip()
        if not text or text.lower() == "null" or len(text) > 50: return None
        clean = re.sub(r"https?://(www\.)?instagram\.com/","", text).strip("/@\n ")
        return clean if re.match(r"^[A-Za-z0-9._]+$", clean) else None
    except: return None

# ── BrasilAPI ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def brasilapi_cnpj(cnpj: str) -> Optional[dict]:
    time.sleep(0.6)
    try:
        r = SESSION.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", headers=HEADERS, timeout=30)
        return r.json() if r.ok else None
    except: return None

def socios_str(data: dict) -> str:
    items = [f"{s.get('nome_socio','').strip()} ({s.get('qualificacao_socio','').strip()})"
             for s in (data.get("qsa") or []) if s.get("nome_socio")]
    return "; ".join(items) or "N/A"

# ── Meta API ──────────────────────────────────────────────────────────────────
def meta_business_discovery(username: str, token: Optional[str] = None) -> dict:
    token = token or META_TOKEN
    if not token: return {}
    u = username.lstrip("@").strip()
    if not u: return {}
    cache = st.session_state.setdefault("meta_cache", {})
    if u in cache: return cache[u]
    fields = f"business_discovery.username({u}){{username,followers_count,media_count,biography,website}}"
    try:
        time.sleep(0.3)
        r = SESSION.get(f"https://graph.facebook.com/v25.0/{IG_USER_ID}",
            params={"fields": fields, "access_token": token}, timeout=25)
        bd = r.json().get("business_discovery") or {} if r.ok else {}
    except: bd = {}
    out = {"username": bd.get("username") or u,
           "followers_count": bd.get("followers_count","N/A"),
           "media_count": bd.get("media_count","N/A"),
           "biography": bd.get("biography","N/A"),
           "website": bd.get("website","N/A")}
    cache[u] = out
    return out

# ── Topbar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vv-topbar"><div class="vv-topbar-inner">
  <div class="vv-brand"><h1>Verso Sourcing Pro</h1><p>Prospecção · CNPJ via Receita Federal · Meta API · Google Places</p></div>
  <div style="display:flex;gap:8px">
    <span class="vv-pill">✨ v3</span>
    <span class="vv-pill">Receita Federal</span>
  </div>
</div></div>
""", unsafe_allow_html=True)

# API Status
apis = {"Google Places": bool(GOOGLE_KEY), "Claude Search": bool(ANTHROPIC_KEY), "Meta API": bool(META_TOKEN)}
badges = " &nbsp; ".join(
    f'<span style="border-radius:999px;padding:4px 10px;font-size:11px;font-weight:700;background:{"#f0fdf4" if v else "#fef2f2"};color:{"#166534" if v else "#991b1b"};border:1px solid {"#86efac" if v else "#fca5a5"}">{"✅" if v else "❌"} {k}</span>'
    for k, v in apis.items()
)
st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">{badges}</div>', unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("leads_rows",[]),("leads_df",None),
    ("cnpj_rows",[]),("cnpj_df",None),
    ("prospect",{"running":False,"stop":False,"cities":[],"limit":40,"city_idx":0,"store_idx":0,
                 "valid":[],"current_city":"","current_name":"","city_total":0,"done":0,
                 "target_est":0,"enrich_address":True,"enrich_instagram":True,"enrich_meta":False,
                 "last_error":"","stopped_reason":""}),
    ("cnpj_job",{"running":False,"stop":False,"items":[],"idx":0,"ok_total":0,"attempt_total":0,
                 "target_est":0,"current":"","last_error":"","stopped_reason":"",
                 "enrich_ig":True,"enrich_socios":True}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["🔍 Prospecção", "🏢 CNPJ (Receita Federal)", "📸 Meta API"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PROSPECÇÃO (OSM)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_panel, col_main = st.columns([0.28, 0.72], gap="large")

    with col_panel:
        cities_input = st.text_area("Cidades ou bairros",
            placeholder="São Paulo\nCuritiba\nLapa, São Paulo", height=120, key="p_cities")
        st.caption("Uma por linha. Pode usar bairros: 'Lapa, São Paulo'")
        limit = st.slider("Limite por cidade", 10, 200, 40, step=10, key="p_limit")

        st.markdown("**Enriquecimento**")
        st.markdown(f"""
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:12px;font-size:12px;line-height:2">
  <b>Estratégia em camadas:</b><br>
  1️⃣ OSM tags (sempre)<br>
  2️⃣ {"✅" if GOOGLE_KEY else "❌"} Google Places → telefone + site<br>
  3️⃣ {"✅" if GOOGLE_KEY else "❌"} Site da loja → Instagram<br>
  4️⃣ {"✅" if ANTHROPIC_KEY else "❌"} Claude Search → Instagram<br>
  5️⃣ {"✅" if META_TOKEN else "❌"} Meta API → seguidores + bio<br>
</div>
""", unsafe_allow_html=True)

        enrich_meta = st.checkbox("Enriquecer via Meta API", value=bool(META_TOKEN), key="p_meta")

        p = st.session_state.prospect
        c1, c2 = st.columns(2)
        with c1:
            start_p = st.button("🚀 Iniciar", key="p_start", disabled=p["running"])
        with c2:
            if st.button("⏹ Parar", key="p_stop", disabled=not p["running"]):
                p["stop"] = True

    if start_p:
        city_list = [c.strip() for c in re.split(r"[,\n;]+", cities_input) if c.strip()]
        if not city_list:
            st.warning("Digite pelo menos uma cidade ou bairro.")
        else:
            st.session_state.leads_rows = []
            st.session_state.leads_df = pd.DataFrame()
            p.update({"running":True,"stop":False,"cities":city_list,"limit":limit,
                      "city_idx":0,"store_idx":0,"valid":[],"current_city":"","current_name":"",
                      "city_total":0,"done":0,"target_est":len(city_list)*limit,
                      "enrich_meta":enrich_meta,"last_error":"","stopped_reason":""})
            st.rerun()

    with col_main:
        p = st.session_state.prospect

        def prospect_step():
            if not p["running"] or p.get("stop"):
                p["running"] = False
                if not p.get("stopped_reason"): p["stopped_reason"] = "Interrompido"
                return
            if p["city_idx"] >= len(p["cities"]):
                p["running"] = False; p["stopped_reason"] = "Concluída"; return
            if not p.get("valid"):
                city = p["cities"][p["city_idx"]]
                p["current_city"] = city
                elements = overpass_query(city)
                valid = [el for el in elements
                         if el.get("tags",{}).get("name")
                         and is_valid_store(el["tags"]["name"], el["tags"])][:p["limit"]]
                p["valid"] = valid; p["store_idx"] = 0; p["city_total"] = len(valid)
                if not valid: p["city_idx"] += 1; return
            if p["store_idx"] >= p["city_total"]:
                p["city_idx"] += 1; p["valid"] = []; return

            el = p["valid"][p["store_idx"]]
            tags = el.get("tags", {}); name = tags.get("name","N/A")
            lat, lon = extract_coords(el)
            p["current_name"] = name

            # Camada 1: OSM
            addr  = addr_from_tags(tags)
            phone = tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile") or None
            insta = ig_from_tags(tags); ig_src = "OSM" if insta else None
            website = tags.get("website") or tags.get("contact:website") or None

            # Camada 2: Google Places
            gplace = google_places_search(name, p["current_city"]) if GOOGLE_KEY else None
            if gplace:
                if not phone:   phone   = gplace.get("formatted_phone_number")
                if not website: website = gplace.get("website"); 
                if not addr:    addr    = gplace.get("formatted_address")

            # Camada 3: Nominatim
            if not addr and lat and lon:
                nom = nominatim_reverse(lat, lon)
                addr = addr_from_nominatim(nom)

            # Camada 4: Site → Instagram
            if not insta and website:
                insta = extract_ig_from_website(website)
                if insta: ig_src = "Site da loja"

            # Camada 5: Claude Search
            if not insta and ANTHROPIC_KEY:
                insta = claude_search_instagram(name, p["current_city"], website or "")
                if insta: ig_src = "Claude Search"

            # Camada 6: Meta API
            ig_followers = ig_bio = ig_meta_website = "N/A"
            if p.get("enrich_meta") and insta and META_TOKEN:
                md = meta_business_discovery(insta)
                ig_followers = str(md.get("followers_count","N/A"))
                ig_bio       = md.get("biography","N/A")
                ig_meta_website = md.get("website","N/A")

            row = {
                "Loja": name, "Cidade": p["current_city"],
                "Instagram": f"@{insta}" if insta else "N/A",
                "Fonte Instagram": ig_src or "N/A",
                "IG Seguidores": ig_followers, "IG Bio": ig_bio,
                "Website": website or "N/A",
                "Telefone": phone or "N/A",
                "Endereço": addr or "N/A",
                "Latitude": lat, "Longitude": lon,
            }
            st.session_state.leads_rows.append(row)
            p["store_idx"] += 1; p["done"] += 1
            st.session_state.leads_df = pd.DataFrame(st.session_state.leads_rows)

        if p["running"]: prospect_step()

        if p["running"]:
            st.progress(min(1.0, p["done"] / max(1, p["target_est"])))
            st.caption(f"**[{p['current_city']}]** {p['current_name']} ({min(p['store_idx'], p['city_total'])}/{p['city_total']})")
        elif p.get("stopped_reason") and p.get("cities"):
            if p["stopped_reason"] == "Concluída":
                st.success("✅ Prospecção concluída!")
            else:
                st.warning(f"⏹ {p['stopped_reason']}")

        df = st.session_state.leads_df
        if df is None or (hasattr(df,"empty") and df.empty):
            if not p["running"]:
                st.info("Configure as cidades no painel e clique em **🚀 Iniciar**.")
        else:
            total  = len(df)
            w_ig   = int((df["Instagram"] != "N/A").sum())
            w_addr = int((df["Endereço"] != "N/A").sum())
            w_ph   = int((df["Telefone"] != "N/A").sum())
            w_site = int((df["Website"] != "N/A").sum())
            rows   = st.session_state.leads_rows
            avg_sc = f"{sum(quality_score(r) for r in rows)/len(rows):.1f}" if rows else "0"

            st.markdown(f"""
<div class="vv-chip-row">
  <div class="vv-chip"><span>Total</span> {total}</div>
  <div class="vv-chip"><span>Instagram</span> {w_ig}</div>
  <div class="vv-chip"><span>Telefone</span> {w_ph}</div>
  <div class="vv-chip"><span>Site</span> {w_site}</div>
  <div class="vv-chip"><span>Endereço</span> {w_addr}</div>
  <div class="vv-chip"><span>Score médio</span> {avg_sc}/5</div>
</div><hr class="vv-hr"/>""", unsafe_allow_html=True)

            for row in (st.session_state.leads_rows[-15:] if p["running"] else st.session_state.leads_rows):
                score   = quality_score(row)
                ig_url  = ig_link(row["Instagram"])
                map_url = maps_link(row["Endereço"] if row["Endereço"] != "N/A" else f"{row['Loja']} {row['Cidade']}")
                site_btn = f"<a class='vv-link-pill vv-link-muted' href='{row['Website']}' target='_blank'>Ver Site</a>" if row.get("Website","N/A") != "N/A" else ""
                bio_html = f'<div style="margin-top:8px;font-size:12px;color:#6b7280;font-style:italic">"{row["IG Bio"][:160]}{"…" if len(row["IG Bio"])>160 else ""}"</div>' if row.get("IG Bio","N/A") != "N/A" else ""
                seg_chip = f"<div class='vv-chip'><span>Seguidores</span> {row['IG Seguidores']}</div>" if row.get("IG Seguidores","N/A") != "N/A" else ""

                st.markdown(f"""
<div class="vv-card">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
    <div style="display:flex;align-items:center;gap:12px;min-width:0">
      <div class="vv-avatar"><div class="vv-avatar-inner">{initials(row['Loja'])}</div></div>
      <div><p class="vv-lead-name">{row['Loja']}</p><p class="vv-lead-city">{row['Cidade']}</p></div>
    </div>
    {quality_dots_html(score)}
  </div>
  <div class="vv-chip-row">
    <div class="vv-chip"><span>Instagram</span> {row['Instagram']} {source_badge(row['Fonte Instagram'])}</div>
    {seg_chip}
    <div class="vv-chip"><span>Telefone</span> {row['Telefone']}</div>
    <div class="vv-chip"><span>Site</span> {"✅" if row.get("Website","N/A") != "N/A" else "N/A"}</div>
  </div>
  <div style="margin-top:10px;font-size:13px"><b>Endereço:</b> {row['Endereço']}</div>
  {bio_html}
  <div class="vv-actions">
    {"<a class='vv-link-pill vv-link-primary' href='"+ig_url+"' target='_blank'>Ver Instagram</a>" if ig_url else "<span class='vv-link-pill vv-link-muted'>Sem Instagram</span>"}
    {site_btn}
    <a class="vv-link-pill vv-link-muted" href="{map_url}" target="_blank">Ver no Maps</a>
  </div>
</div>""", unsafe_allow_html=True)

            if not p["running"]:
                out = BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w:
                    df.to_excel(w, index=False, sheet_name="Leads")
                st.download_button("📥 Baixar Excel", out.getvalue(), "leads_verso_vivo.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.caption(f"Mostrando os 15 mais recentes. Total: {total}")

        if p["running"]: time.sleep(0.15); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CNPJ (RECEITA FEDERAL)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    col_panel2, col_main2 = st.columns([0.28, 0.72], gap="large")

    with col_panel2:
        st.markdown("**Cidade**")
        cnpj_cidade = st.text_input("", placeholder="Ex: São Paulo", key="cnpj_cidade",
                                    label_visibility="collapsed")
        st.caption("O app baixa os dados diretamente da Receita Federal e filtra CNAE **4781400** + situação **ATIVA**.")

        cnpj_max = st.slider("Máximo de empresas", 50, 500, 200, step=50, key="cnpj_max")
        enrich_cnpj_socios = st.checkbox("Buscar sócios (BrasilAPI)", value=True, key="cnpj_socios")
        enrich_cnpj_ig = st.checkbox("Buscar Instagram (Google + Claude)", value=True, key="cnpj_ig")

        st.markdown(f"""
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:12px;font-size:12px;line-height:2;margin-top:8px">
  <b>Fluxo por empresa:</b><br>
  1️⃣ ✅ Receita Federal → CNPJ + dados fiscais<br>
  2️⃣ {"✅" if enrich_cnpj_socios else "⬜"} BrasilAPI → razão social + sócios<br>
  3️⃣ {"✅" if GOOGLE_KEY else "❌"} Google Places → telefone + site<br>
  4️⃣ {"✅" if GOOGLE_KEY else "❌"} Site → Instagram<br>
  5️⃣ {"✅" if ANTHROPIC_KEY else "❌"} Claude Search → Instagram<br>
</div>
""", unsafe_allow_html=True)

        j = st.session_state.cnpj_job
        c1, c2 = st.columns(2)
        with c1:
            start_cnpj = st.button("🚀 Iniciar", key="cnpj_start", disabled=j["running"])
        with c2:
            if st.button("⏹ Parar", key="cnpj_stop", disabled=not j["running"]):
                j["stop"] = True

    with col_main2:
        j = st.session_state.cnpj_job

        # ── Iniciar: busca RF ─────────────────────────────────────────────────
        if start_cnpj:
            if not cnpj_cidade.strip():
                st.warning("Digite o nome de uma cidade.")
            else:
                prog_placeholder = st.empty()
                status_placeholder = st.empty()

                def update_progress(pct, msg):
                    prog_placeholder.progress(pct)
                    status_placeholder.caption(msg)

                with st.spinner(f"Buscando empresas na Receita Federal para **{cnpj_cidade}**…"):
                    items = buscar_cnpjs_receita_federal(
                        cnpj_cidade.strip(),
                        cnae="4781400",
                        limite=cnpj_max,
                        progress_cb=update_progress
                    )

                prog_placeholder.empty()
                status_placeholder.empty()

                if not items:
                    # Debug: mostra o que aconteceu internamente
                    folder = get_rf_latest_folder()
                    st.error(f"Nenhuma empresa encontrada com CNAE 4781400 em **{cnpj_cidade}**.")
                    with st.expander("🔍 Diagnóstico"):
                        st.write(f"**Pasta RF detectada:** `{folder}`")
                        municipios = get_municipios_rf()
                        st.write(f"**Total de municípios carregados:** {len(municipios)}")
                        cod = find_municipio_code(cnpj_cidade.strip(), municipios)
                        st.write(f"**Código IBGE encontrado para '{cnpj_cidade}':** `{cod}`")
                        if not municipios:
                            st.warning("Falha ao baixar tabela de municípios da RF. O servidor pode estar lento.")
                        elif not cod:
                            cidade_norm = norm(cnpj_cidade.strip())
                            similares = [(c, n) for c, n in municipios.items() if cidade_norm[:4] in n][:10]
                            st.write("**Municípios similares encontrados:**")
                            for c, n in similares:
                                st.write(f"- `{c}` → {n}")
                        url_test = f"{RF_BASE_URL}/{folder}/Municipios.zip"
                        st.write(f"**URL testada:** `{url_test}`")
                else:
                    st.session_state.cnpj_rows = items
                    st.session_state.cnpj_df = pd.DataFrame(items)
                    j.update({
                        "running": True, "stop": False,
                        "items": items, "idx": 0,
                        "ok_total": 0, "attempt_total": 0,
                        "target_est": len(items),
                        "current": "", "last_error": "", "stopped_reason": "",
                        "enrich_ig": enrich_cnpj_ig,
                        "enrich_socios": enrich_cnpj_socios,
                        "cidade": cnpj_cidade.strip(),
                    })
                    st.rerun()

        # ── Enriquecimento incremental ────────────────────────────────────────
        def cnpj_enrich_step():
            if not j["running"] or j.get("stop"):
                j["running"] = False
                if not j.get("stopped_reason"): j["stopped_reason"] = "Interrompido"
                return
            items = st.session_state.cnpj_rows
            idx = j["idx"]
            if idx >= len(items):
                j["running"] = False; j["stopped_reason"] = "Concluída"; return

            row = items[idx]
            loja   = row.get("Nome Fantasia","") or row.get("Razão Social","")
            cidade = j.get("cidade","")
            cnpj   = re.sub(r"\D","", row.get("CNPJ",""))
            j["current"] = f"{loja} • {cnpj}"
            j["idx"] = idx + 1

            # BrasilAPI → razão social + sócios
            if j.get("enrich_socios") and cnpj:
                data = brasilapi_cnpj(cnpj)
                if data:
                    row["Razão Social"] = data.get("razao_social","N/A")
                    if row.get("Nome Fantasia","N/A") == "N/A":
                        row["Nome Fantasia"] = data.get("nome_fantasia","N/A")
                    row["Sócios (QSA)"] = socios_str(data)
                    row["MEI"]     = str(data.get("opcao_pelo_mei","N/A"))
                    row["Simples"] = str(data.get("opcao_pelo_simples","N/A"))
                    row["Porte"]   = data.get("porte","N/A")
                    if row.get("Email","N/A") == "N/A":
                        row["Email"] = data.get("email","N/A")
                    loja = row["Razão Social"] if loja in ("","N/A") else loja

            # Google Places → telefone + site
            if j.get("enrich_ig") and GOOGLE_KEY and loja and loja != "N/A":
                gplace = google_places_search(loja, cidade)
                if gplace:
                    if row.get("Telefone","N/A") == "N/A":
                        row["Telefone"] = gplace.get("formatted_phone_number","N/A")
                    if row.get("Website","N/A") == "N/A":
                        row["Website"] = gplace.get("website","N/A")

            # Site → Instagram
            if j.get("enrich_ig"):
                website = row.get("Website","N/A")
                insta = extract_ig_from_website(website) if website != "N/A" else None
                if not insta and ANTHROPIC_KEY and loja and loja != "N/A":
                    insta = claude_search_instagram(loja, cidade, website if website != "N/A" else "")
                if insta:
                    row["Instagram"] = f"@{insta}"

            row["Status"] = "OK"
            items[idx] = row
            st.session_state.cnpj_rows = items
            st.session_state.cnpj_df = pd.DataFrame(items)

        if j["running"]: cnpj_enrich_step()

        # ── Status ────────────────────────────────────────────────────────────
        if j["running"]:
            st.progress(min(1.0, j["idx"] / max(1, j["target_est"])))
            st.caption(f"**Enriquecendo:** {j['current']}  ({j['idx']}/{j['target_est']})")
        elif j.get("stopped_reason") and j.get("items"):
            if j["stopped_reason"] == "Concluída":
                st.success("✅ Concluído!")
            else:
                st.warning(f"⏹ {j['stopped_reason']}")

        # ── Resultados ────────────────────────────────────────────────────────
        dfc = st.session_state.cnpj_df
        if dfc is None or (hasattr(dfc,"empty") and dfc.empty):
            if not j["running"]:
                st.info("Digite a cidade e clique em **🚀 Iniciar** para buscar empresas com CNAE 4781400 diretamente na Receita Federal.")
        else:
            total  = len(dfc)
            w_ig   = int((dfc.get("Instagram", pd.Series(dtype=str)) != "N/A").sum())
            w_ph   = int((dfc.get("Telefone",  pd.Series(dtype=str)) != "N/A").sum())
            w_site = int((dfc.get("Website",   pd.Series(dtype=str)) != "N/A").sum())
            w_ok   = int((dfc.get("Status",    pd.Series(dtype=str)) == "OK").sum())

            st.markdown(f"""
<div class="vv-chip-row">
  <div class="vv-chip"><span>Total RF</span> {total}</div>
  <div class="vv-chip"><span>Enriquecidos</span> {w_ok}</div>
  <div class="vv-chip"><span>Instagram</span> {w_ig}</div>
  <div class="vv-chip"><span>Telefone</span> {w_ph}</div>
  <div class="vv-chip"><span>Site</span> {w_site}</div>
</div><hr class="vv-hr"/>""", unsafe_allow_html=True)

            cols_show = ["Nome Fantasia","Razão Social","CNPJ","Telefone","Email","Website",
                         "Instagram","Bairro","Logradouro","UF","CEP","Abertura","Porte",
                         "Sócios (QSA)","Status"]
            cols_show = [c for c in cols_show if c in dfc.columns]
            st.dataframe(dfc[cols_show].tail(80) if j["running"] else dfc[cols_show],
                         use_container_width=True, hide_index=True)

            if not j["running"]:
                out = BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w:
                    dfc.to_excel(w, index=False, sheet_name="Empresas")
                st.download_button("📥 Baixar Excel", out.getvalue(), "empresas_verso_vivo.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.caption(f"Mostrando os 80 mais recentes. Total: {total}")

        if j["running"]: time.sleep(0.15); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — META API
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Meta API — Business Discovery")
    st.caption(f"IG User ID: **{IG_USER_ID}** (Verso Vivo)")
    if META_TOKEN:
        st.success("✅ META_USER_TOKEN_LONG detectado nos Secrets.")
    else:
        st.warning("⚠️ Configure META_USER_TOKEN_LONG nos Secrets.")

    tmp_token = st.text_input("Token temporário (opcional):", type="password", key="meta_tmp")
    test_user = st.text_input("Username para teste (sem @)", value="oficialversovivo", key="meta_test")

    if st.button("🧪 Testar Business Discovery"):
        token = tmp_token or META_TOKEN
        if not token:
            st.error("Token não configurado.")
        else:
            with st.spinner("Consultando…"):
                res = meta_business_discovery(test_user, token)
            if res and res.get("followers_count","N/A") != "N/A":
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Seguidores", f"{res['followers_count']:,}".replace(",","."))
                    st.metric("Posts", res.get("media_count","N/A"))
                with c2:
                    st.info(f"**Bio:** {res.get('biography','N/A')}")
                    if res.get("website","N/A") != "N/A":
                        st.markdown(f"**Site:** [{res['website']}]({res['website']})")
                st.success("✅ Meta API funcionando!")
            else:
                st.error("Sem retorno. Verifique o token e se a conta é Business/Creator.")
