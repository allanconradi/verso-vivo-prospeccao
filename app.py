
import streamlit as st
import pandas as pd
import requests
import re
import time
import unicodedata
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
.stSelectbox>div>div>div,.stMultiSelect>div>div{border-radius:14px!important;border:1px solid var(--border)!important;background:var(--card)!important;font-size:14px!important;box-shadow:none!important;}
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
.vv-source-badge{display:inline-flex;align-items:center;border-radius:999px;padding:3px 8px;font-size:10px;font-weight:700;background:#f0fdf4;color:#166534;border:1px solid #86efac;}
div[data-testid="stDataFrame"]{border-radius:var(--radius);overflow:hidden;border:1px solid var(--border);}
</style>
""", unsafe_allow_html=True)

# ── Secrets ───────────────────────────────────────────────────────────────────
def secret(k): 
    try: return st.secrets.get(k)
    except: return None

ANTHROPIC_KEY   = secret("ANTHROPIC_API_KEY")
META_TOKEN      = secret("META_USER_TOKEN_LONG")
GOOGLE_KEY      = secret("GOOGLE_PLACES_KEY")
IG_USER_ID      = secret("IG_USER_ID") or "17841473844567187"

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
    return sum(1 for k in ["Instagram","Telefone","Endereço","IG Seguidores","Website"] if row.get(k,"N/A") != "N/A")

def quality_dots_html(score: int) -> str:
    color = "#22c55e" if score >= 4 else "#f59e0b" if score >= 2 else "#ef4444"
    dots = "".join(f'<div class="vv-dot" style="background:{color if i < score else "#e5e7eb"}"></div>' for i in range(5))
    return f'<div class="vv-dots">{dots}<span style="font-size:11px;color:#9ca3af;margin-left:4px">{score}/5</span></div>'

def source_badge(source: str) -> str:
    colors = {"OSM":"#dbeafe|#1d4ed8","Google Places":"#fef9c3|#92400e","Claude Search":"#f3e8ff|#7e22ce","N/A":"#f3f4f6|#9ca3af"}
    bg, fg = colors.get(source, "#f3f4f6|#9ca3af").split("|")
    return f'<span style="display:inline-flex;border-radius:999px;padding:2px 8px;font-size:10px;font-weight:700;background:{bg};color:{fg};border:1px solid {fg}33">{source}</span>'

# ── Filtros OSM ───────────────────────────────────────────────────────────────
EXCLUDE_BRANDS = {"renner","c&a","cea","zara","riachuelo","marisa","pernambucanas","havan","hering","colcci","hope","intimissimi","calzedonia","nike","adidas","puma","arezzo","schutz","anacapri","loungerie","lacoste","tommy","tommy hilfiger","le lis","lelis","animale","farm","dress to","dressto","john john","ellus"}
FOOD_WORDS = {"restaurante","pizza","pizzaria","hamburguer","hamburgueria","burger","bar","pub","café","cafe","cafeteria","padaria","confeitaria","açaí","acai","sorveteria","sushi","japa","yakisoba","churrascaria","lanchonete","bistrô","bistro"}

def is_food(name, tags):
    n = norm(name)
    if any(w in n for w in FOOD_WORDS): return True
    return norm(str(tags.get("amenity",""))) in {"restaurant","cafe","bar","fast_food","pub","ice_cream"}

def is_excluded(name, tags):
    n = norm(name)
    brand = norm(str(tags.get("brand","")))
    return any(b in n or b in brand for b in EXCLUDE_BRANDS)

def is_valid_store(name, tags):
    if not name or is_food(name, tags) or is_excluded(name, tags): return False
    n = norm(name)
    if any(k in n for k in ["multimarca","boutique","moda","fashion","vestuario","feminina","looks","vestuário"]): return True
    return norm(str(tags.get("shop",""))) in {"boutique","clothes","apparel","fashion","clothing"}

# ── OSM ───────────────────────────────────────────────────────────────────────
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
    parts = [f"{road} {a.get('house_number','')}".strip(), a.get("suburb") or a.get("neighbourhood",""), a.get("city") or a.get("town") or a.get("village",""), a.get("state","")]
    return ", ".join(p for p in parts if p).strip() or data.get("display_name")

# ── Google Places API ─────────────────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def google_places_search(name: str, city: str) -> Optional[dict]:
    """Retorna telefone, site, endereço e place_id via Google Places Text Search."""
    if not GOOGLE_KEY: return None
    try:
        time.sleep(0.3)
        # Text Search
        r = SESSION.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": f"{name} {city} loja de roupa", "language": "pt-BR", "key": GOOGLE_KEY},
            timeout=15
        )
        if not r.ok: return None
        results = r.json().get("results", [])
        if not results: return None

        place_id = results[0].get("place_id")
        if not place_id: return None

        # Place Details — pega telefone + site
        r2 = SESSION.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={"place_id": place_id, "fields": "name,formatted_phone_number,website,formatted_address,url", "language": "pt-BR", "key": GOOGLE_KEY},
            timeout=15
        )
        if not r2.ok: return None
        return r2.json().get("result") or None
    except: return None

def extract_ig_from_website(website: str) -> Optional[str]:
    """Tenta extrair @ do Instagram a partir da URL do site da loja."""
    if not website or website == "N/A": return None
    # Caso o site seja direto do Instagram
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", website)
    if m:
        h = m.group(1)
        if h.lower() not in {"p","reel","stories","explore"}: return h
    # Caso seja um site normal — faz fetch e procura links do Instagram
    try:
        time.sleep(0.5)
        r = SESSION.get(website, headers=HEADERS, timeout=10)
        if not r.ok: return None
        matches = re.findall(r"instagram\.com/([A-Za-z0-9._]+)", r.text)
        skip = {"p","reel","reels","stories","explore","accounts","about","sharer"}
        for h in matches:
            if h.lower() not in skip and len(h) > 2:
                return h
    except: pass
    return None

# ── Claude Search ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=43200, show_spinner=False)
def claude_search_instagram(store_name: str, city: str, website: str = "") -> Optional[str]:
    if not ANTHROPIC_KEY: return None
    context = f"O site da loja é {website}. " if website and website != "N/A" else ""
    try:
        r = SESSION.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 200,
                "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                "messages": [{"role": "user", "content":
                    f'{context}Pesquise o perfil do Instagram da loja "{store_name}" em {city}, Brasil. '
                    f'Retorne APENAS o handle (sem @ e sem URL), ex: minhaloja. '
                    f'Se não encontrar com certeza, retorne: null'}]
            }, timeout=30
        )
        if not r.ok: return None
        text = " ".join(b.get("text","") for b in r.json().get("content",[]) if b.get("type")=="text").strip()
        if not text or text.lower() == "null" or len(text) > 50: return None
        clean = re.sub(r"https?://(www\.)?instagram\.com/","", text).strip("/@\n ")
        return clean if re.match(r"^[A-Za-z0-9._]+$", clean) else None
    except: return None

@st.cache_data(ttl=43200, show_spinner=False)
def claude_search_cnpj(store_name: str, city: str) -> Optional[str]:
    if not ANTHROPIC_KEY: return None
    try:
        r = SESSION.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 200,
                "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                "messages": [{"role": "user", "content":
                    f'Pesquise o CNPJ da empresa "{store_name}" em {city}, Brasil. '
                    f'Retorne APENAS os 14 dígitos, ex: 12345678000190. '
                    f'Se não encontrar com certeza, retorne: null'}]
            }, timeout=30
        )
        if not r.ok: return None
        text = " ".join(b.get("text","") for b in r.json().get("content",[]) if b.get("type")=="text").strip()
        digits = re.sub(r"\D","", text)
        return digits if len(digits) == 14 else None
    except: return None

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
    out = {"username": bd.get("username") or u, "followers_count": bd.get("followers_count","N/A"),
           "media_count": bd.get("media_count","N/A"), "biography": bd.get("biography","N/A"),
           "website": bd.get("website","N/A")}
    cache[u] = out
    return out

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

def cnpj_to_row(data: dict, loja: str, cidade: str, cnpj: str, status: str) -> dict:
    cnaes_str = "; ".join(f"{x.get('codigo','')} {x.get('descricao','')}".strip()
        for x in (data.get("cnaes_secundarios") or []) if isinstance(x, dict)) or "N/A"
    return {"Loja":loja,"Cidade":cidade,"CNPJ":data.get("cnpj") or cnpj or "N/A",
        "Razão Social":data.get("razao_social","N/A"),"Nome Fantasia":data.get("nome_fantasia","N/A"),
        "Abertura":data.get("data_inicio_atividade","N/A"),"Porte":data.get("porte","N/A"),
        "MEI":str(data.get("opcao_pelo_mei","N/A")),"Simples":str(data.get("opcao_pelo_simples","N/A")),
        "Capital Social":data.get("capital_social","N/A"),"Situação":data.get("descricao_situacao_cadastral","N/A"),
        "Email":data.get("email","N/A"),"Telefone":data.get("ddd_telefone_1","N/A"),
        "UF":data.get("uf","N/A"),"Município":data.get("municipio","N/A"),
        "CEP":data.get("cep","N/A"),"Logradouro":data.get("logradouro","N/A"),
        "Número":data.get("numero","N/A"),"Bairro":data.get("bairro","N/A"),
        "CNAE Principal":data.get("cnae_fiscal","N/A"),"CNAE Desc":data.get("cnae_fiscal_descricao","N/A"),
        "CNAEs Secundários":cnaes_str,"Sócios (QSA)":socios_str(data),"Status":status}

# ── Topbar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vv-topbar"><div class="vv-topbar-inner">
  <div class="vv-brand"><h1>Verso Sourcing Pro</h1><p>Prospecção · CNPJ · Meta API · Google Places</p></div>
  <div style="display:flex;gap:8px">
    <span class="vv-pill">✨ v2</span>
    <span class="vv-pill">3 fontes</span>
  </div>
</div></div>
""", unsafe_allow_html=True)

# ── API Status banner ─────────────────────────────────────────────────────────
apis = {"Google Places": bool(GOOGLE_KEY), "Claude Search": bool(ANTHROPIC_KEY), "Meta API": bool(META_TOKEN)}
badges = " &nbsp; ".join(
    f'<span style="display:inline-flex;border-radius:999px;padding:4px 10px;font-size:11px;font-weight:700;background:{"#f0fdf4" if v else "#fef2f2"};color:{"#166534" if v else "#991b1b"};border:1px solid {"#86efac" if v else "#fca5a5"}">{"✅" if v else "❌"} {k}</span>'
    for k, v in apis.items()
)
st.markdown(f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">{badges}</div>', unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("leads_rows",[]),("leads_df",None),("cnpj_rows",[]),("cnpj_df",None),
    ("prospect",{"running":False,"stop":False,"cities":[],"limit":40,"city_idx":0,"store_idx":0,
                 "valid":[],"current_city":"","current_name":"","city_total":0,"done":0,
                 "target_est":0,"enrich_address":True,"enrich_instagram":True,"enrich_meta":False,
                 "last_error":"","stopped_reason":""}),
    ("cnpj_job",{"running":False,"stop":False,"items":[],"idx":0,"ok_total":0,"attempt_total":0,
                 "target_est":0,"current":"","last_error":"","stopped_reason":""}),
]:
    if key not in st.session_state: st.session_state[key] = default

# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["🔍 Prospecção", "🏢 CNPJ", "📸 Meta API"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PROSPECÇÃO
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_panel, col_main = st.columns([0.28, 0.72], gap="large")

    with col_panel:
        cities_input = st.text_area("Cidades ou bairros", placeholder="São Paulo\nCuritiba\nLapa, São Paulo", height=120, key="p_cities")
        st.caption("Uma por linha. Pode usar bairros: 'Lapa, São Paulo'")
        limit = st.slider("Limite por cidade", 10, 200, 40, step=10, key="p_limit")

        st.markdown("**Enriquecimento**")

        # Mostra de forma visual quais fontes estão ativas
        st.markdown(f"""
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:14px;padding:12px;font-size:12px;line-height:2">
  <b>Estratégia em camadas:</b><br>
  1️⃣ OSM tags (sempre)<br>
  2️⃣ {"✅" if GOOGLE_KEY else "❌"} Google Places (telefone, site, endereço)<br>
  3️⃣ {"✅" if GOOGLE_KEY else "❌"} Site da loja → Instagram<br>
  4️⃣ {"✅" if ANTHROPIC_KEY else "❌"} Claude Search → Instagram<br>
  5️⃣ {"✅" if META_TOKEN else "❌"} Meta API (seguidores, bio)<br>
</div>
""", unsafe_allow_html=True)

        enrich_meta = st.checkbox("Enriquecer via Meta API", value=bool(META_TOKEN), key="p_meta")

        p = st.session_state.prospect
        c1, c2 = st.columns(2)
        with c1: start_p = st.button("🚀 Iniciar", key="p_start", disabled=p["running"])
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
                valid = [el for el in elements if el.get("tags",{}).get("name") and is_valid_store(el["tags"]["name"], el["tags"])][:p["limit"]]
                p["valid"] = valid; p["store_idx"] = 0; p["city_total"] = len(valid)
                if not valid: p["city_idx"] += 1; return

            if p["store_idx"] >= p["city_total"]:
                p["city_idx"] += 1; p["valid"] = []; return

            el = p["valid"][p["store_idx"]]
            tags = el.get("tags", {}); name = tags.get("name","N/A")
            lat, lon = extract_coords(el)
            p["current_name"] = name

            # ── CAMADA 1: OSM tags ────────────────────────────────────────────
            addr   = addr_from_tags(tags)
            phone  = tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile") or None
            insta  = ig_from_tags(tags)
            ig_src = "OSM" if insta else None
            website = tags.get("website") or tags.get("contact:website") or None
            site_src = "OSM" if website else None

            # ── CAMADA 2: Google Places ───────────────────────────────────────
            gplace = google_places_search(name, p["current_city"]) if GOOGLE_KEY else None
            if gplace:
                if not phone:   phone    = gplace.get("formatted_phone_number")
                if not website: website  = gplace.get("website"); site_src = "Google Places"
                if not addr:    addr     = gplace.get("formatted_address")

            # ── CAMADA 3: Nominatim (endereço fallback) ───────────────────────
            if not addr and lat and lon:
                nom = nominatim_reverse(lat, lon)
                addr = addr_from_nominatim(nom)

            # ── CAMADA 4: Site da loja → Instagram ────────────────────────────
            if not insta and website:
                insta = extract_ig_from_website(website)
                if insta: ig_src = "Site da loja"

            # ── CAMADA 5: Claude Search → Instagram ───────────────────────────
            if not insta and ANTHROPIC_KEY:
                insta = claude_search_instagram(name, p["current_city"], website or "")
                if insta: ig_src = "Claude Search"

            # ── CAMADA 6: Meta API ─────────────────────────────────────────────
            ig_followers = ig_bio = ig_meta_website = "N/A"
            if p.get("enrich_meta") and insta and META_TOKEN:
                md = meta_business_discovery(insta)
                ig_followers    = str(md.get("followers_count","N/A"))
                ig_bio          = md.get("biography","N/A")
                ig_meta_website = md.get("website","N/A")
                if ig_meta_website != "N/A" and (not website or website == "N/A"):
                    website = ig_meta_website; site_src = "Meta API"

            row = {
                "Loja": name, "Cidade": p["current_city"],
                "Instagram": f"@{insta}" if insta else "N/A",
                "Fonte Instagram": ig_src or "N/A",
                "IG Seguidores": ig_followers, "IG Bio": ig_bio,
                "Website": website or "N/A", "Fonte Website": site_src or "N/A",
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
            st.caption(f"**[{p['current_city']}]** {p['current_name']}  ({min(p['store_idx'], p['city_total'])}/{p['city_total']})")
        elif p.get("stopped_reason") and p.get("cities"):
            st.success("✅ Concluída!") if p["stopped_reason"] == "Concluída" else st.warning(f"⏹ {p['stopped_reason']}")

        df = st.session_state.leads_df
        if df is None or (hasattr(df,"empty") and df.empty):
            if not p["running"]: st.info("Configure as cidades no painel e clique em **🚀 Iniciar**.")
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
    <div class="vv-chip"><span>Site</span> {"✅" if row.get("Website","N/A") != "N/A" else "N/A"} {source_badge(row.get("Fonte Website","N/A")) if row.get("Website","N/A") != "N/A" else ""}</div>
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
                with pd.ExcelWriter(out, engine="openpyxl") as w: df.to_excel(w, index=False, sheet_name="Leads")
                st.download_button("📥 Baixar Excel", out.getvalue(), "leads_verso_vivo.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.caption(f"Mostrando os 15 mais recentes. Total: {total}")

        if p["running"]: time.sleep(0.15); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CNPJ
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    col_panel2, col_main2 = st.columns([0.28, 0.72], gap="large")

    with col_panel2:
        cnpj_source = st.radio("Fonte", ["Cidade/Bairro (OSM)", "Lista manual", "Usar leads da prospecção"], key="cnpj_src")
        if cnpj_source == "Cidade/Bairro (OSM)":
            cnpj_cities = st.text_area("Cidades ou bairros", placeholder="São Paulo\nCuritiba", height=100, key="cnpj_cities")
        elif cnpj_source == "Lista manual":
            cnpj_lista = st.text_area("Lista (Loja, Cidade)", placeholder="Boutique Rosa, São Paulo\nLoja Sol, Curitiba", height=120, key="cnpj_lista")
        else:
            st.caption("Usa os leads coletados na aba Prospecção.")
        cnpj_max = st.slider("Máximo de lojas", 10, 300, 80, step=10, key="cnpj_max")

        j = st.session_state.cnpj_job
        c1, c2 = st.columns(2)
        with c1: start_cnpj = st.button("🚀 Iniciar", key="cnpj_start", disabled=j["running"])
        with c2:
            if st.button("⏹ Parar", key="cnpj_stop", disabled=not j["running"]): j["stop"] = True

    if start_cnpj:
        items: List[Dict[str,str]] = []
        if cnpj_source == "Cidade/Bairro (OSM)":
            for city in [c.strip() for c in re.split(r"[,\n;]+", cnpj_cities) if c.strip()]:
                for el in overpass_query(city):
                    tags = el.get("tags",{}); name = tags.get("name")
                    if name and is_valid_store(name, tags): items.append({"Loja":name,"Cidade":city})
        elif cnpj_source == "Lista manual":
            for line in cnpj_lista.splitlines():
                parts = [p.strip() for p in re.split(r"[,;|]", line) if p.strip()]
                if len(parts) >= 2: items.append({"Loja":parts[0],"Cidade":parts[1]})
        else:
            df_leads = st.session_state.leads_df
            if df_leads is not None and not df_leads.empty:
                for _, row in df_leads[["Loja","Cidade"]].dropna().iterrows():
                    items.append({"Loja":str(row["Loja"]),"Cidade":str(row["Cidade"])})

        items = items[:cnpj_max]
        if items:
            st.session_state.cnpj_rows = []; st.session_state.cnpj_df = pd.DataFrame()
            j.update({"running":True,"stop":False,"items":items,"idx":0,"ok_total":0,
                      "attempt_total":0,"target_est":len(items),"current":"","last_error":"","stopped_reason":""})
            st.rerun()
        else:
            st.warning("Nenhum item para processar.")

    with col_main2:
        j = st.session_state.cnpj_job

        def cnpj_step():
            if not j["running"] or j.get("stop"):
                j["running"] = False
                if not j.get("stopped_reason"): j["stopped_reason"] = "Interrompido"
                return
            items = j.get("items",[]); idx = j["idx"]
            if idx >= len(items): j["running"] = False; j["stopped_reason"] = "Concluída"; return

            item = items[idx]; loja, cidade = item.get("Loja",""), item.get("Cidade","")
            j["current"] = f"{loja} • {cidade}"; j["idx"] = idx+1; j["attempt_total"] = j.get("attempt_total",0)+1

            cnpj = claude_search_cnpj(loja, cidade)
            if not cnpj:
                st.session_state.cnpj_rows.append(cnpj_to_row({},loja,cidade,"N/A","CNPJ não encontrado"))
            else:
                data = brasilapi_cnpj(cnpj)
                if not data:
                    st.session_state.cnpj_rows.append(cnpj_to_row({},loja,cidade,cnpj,"Erro BrasilAPI"))
                else:
                    st.session_state.cnpj_rows.append(cnpj_to_row(data,loja,cidade,cnpj,"OK"))
                    j["ok_total"] = j.get("ok_total",0)+1
            if st.session_state.cnpj_rows:
                st.session_state.cnpj_df = pd.DataFrame(st.session_state.cnpj_rows)

        if j["running"]: cnpj_step()

        if j["running"]:
            st.progress(min(1.0, j["idx"]/max(1,j["target_est"])))
            st.caption(f"**Processando:** {j['current']}  ({j['idx']}/{j['target_est']})")
        elif j.get("stopped_reason") and j.get("items"):
            st.success("✅ Concluído!") if j["stopped_reason"] == "Concluída" else st.warning(f"⏹ {j['stopped_reason']}")

        dfc = st.session_state.cnpj_df
        if dfc is None or (hasattr(dfc,"empty") and dfc.empty):
            if not j["running"]: st.info("Escolha a fonte e clique em **🚀 Iniciar**.")
        else:
            ok    = int((dfc.get("Status", pd.Series(dtype=str)) == "OK").sum())
            found = int((dfc.get("CNPJ", pd.Series(dtype=str)).astype(str) != "N/A").sum())
            st.markdown(f"""
<div class="vv-chip-row">
  <div class="vv-chip"><span>Total</span> {len(dfc)}</div>
  <div class="vv-chip"><span>CNPJ encontrado</span> {found}</div>
  <div class="vv-chip"><span>OK (BrasilAPI)</span> {ok}</div>
</div><hr class="vv-hr"/>""", unsafe_allow_html=True)
            st.dataframe(dfc.tail(80) if j["running"] else dfc, use_container_width=True, hide_index=True)
            if not j["running"]:
                out = BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w: dfc.to_excel(w, index=False, sheet_name="Empresas")
                st.download_button("📥 Baixar Excel", out.getvalue(), "empresas_verso_vivo.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if j["running"]: time.sleep(0.15); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — META API
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Meta API — Business Discovery")
    st.caption(f"IG User ID: **{IG_USER_ID}** (Verso Vivo)")
    if META_TOKEN: st.success("✅ META_USER_TOKEN_LONG detectado nos Secrets.")
    else: st.warning("⚠️ Configure META_USER_TOKEN_LONG nos Secrets.")

    tmp_token = st.text_input("Token temporário (opcional, sobrescreve o Secret):", type="password", key="meta_tmp")
    test_user = st.text_input("Username para teste (sem @)", value="oficialversovivo", key="meta_test")

    if st.button("🧪 Testar Business Discovery"):
        token = tmp_token or META_TOKEN
        if not token: st.error("Token não configurado.")
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
