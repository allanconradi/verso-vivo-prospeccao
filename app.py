import streamlit as st
import pandas as pd
import requests
import re
import time
import unicodedata
from io import BytesIO
from urllib.parse import quote_plus
from typing import Optional, Tuple, Dict, Any, List

st.set_page_config(page_title="Verso Sourcing Pro", page_icon="✨", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
  --bg:#fafafa; --card:#fff; --text:#111; --muted:#6b7280;
  --border:#e5e7eb; --accent:#111; --radius:18px;
  --shadow:0 8px 24px rgba(17,17,17,0.06);
  --shadow-soft:0 1px 0 rgba(0,0,0,0.03);
}
html,body,[class*="st-"]{
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",Arial,sans-serif!important;
  color:var(--text);
}
.stApp{background:var(--bg);}
.main .block-container{max-width:1280px;padding-top:1rem;padding-bottom:2rem;}
#MainMenu,footer,header{visibility:hidden;}

/* Topbar */
.vv-topbar{
  position:sticky;top:0;z-index:999;
  background:rgba(250,250,250,0.92);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border);
  margin:-1rem -1rem 1.5rem -1rem;padding:14px 0;
}
.vv-topbar-inner{
  max-width:1280px;margin:0 auto;padding:0 1rem;
  display:flex;align-items:center;justify-content:space-between;
}
.vv-brand h1{font-size:18px;margin:0;font-weight:900;letter-spacing:-.3px;}
.vv-brand p{margin:0;font-size:12px;color:var(--muted);}
.vv-pill{
  display:inline-flex;align-items:center;border-radius:999px;
  padding:8px 14px;border:1px solid var(--border);background:var(--card);
  font-size:11px;font-weight:800;
}

/* Inputs */
.stTextInput>div>div>input,.stTextArea textarea{
  border-radius:14px!important;border:1px solid var(--border)!important;
  background:var(--card)!important;padding:11px 12px!important;
  font-size:14px!important;box-shadow:none!important;
}
.stSelectbox>div>div>div,.stMultiSelect>div>div{
  border-radius:14px!important;border:1px solid var(--border)!important;
  background:var(--card)!important;font-size:14px!important;box-shadow:none!important;
}

/* Buttons */
.stButton>button{
  width:100%;border-radius:999px!important;border:1px solid transparent!important;
  background:var(--accent)!important;color:#fff!important;
  font-weight:900!important;height:44px!important;
  box-shadow:none!important;font-size:14px!important;
  transition:filter .12s,transform .12s;
}
.stButton>button:hover{filter:brightness(.95);transform:translateY(-1px);}
.stButton>button:disabled{opacity:.55!important;}

/* Cards */
.vv-card{
  background:var(--card);border:1px solid var(--border);
  border-radius:var(--radius);padding:18px;
  box-shadow:var(--shadow-soft);margin-bottom:14px;
}
.vv-card:hover{box-shadow:var(--shadow);}

/* Lead */
.vv-lead-name{font-size:15px;font-weight:950;margin:0;}
.vv-lead-city{font-size:12px;color:var(--muted);margin:0;}
.vv-chip-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
.vv-chip{
  display:inline-flex;align-items:center;gap:6px;
  border-radius:999px;padding:6px 10px;
  background:#f3f4f6;border:1px solid #f3f4f6;
  font-size:12px;font-weight:700;
}
.vv-chip span{color:#9ca3af;}
.vv-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;}
.vv-link-pill{
  display:inline-flex;align-items:center;border-radius:999px;
  padding:8px 14px;font-size:12px;font-weight:950;
  border:1px solid var(--border);background:#fff;
  color:var(--text)!important;text-decoration:none!important;
}
.vv-link-pill:hover{filter:brightness(.97);}
.vv-link-primary{background:#111;border-color:#111;color:#fff!important;}
.vv-link-muted{background:#f3f4f6;border-color:#f3f4f6;}
.vv-hr{border:none;border-top:1px solid #f1f1f1;margin:14px 0;}

/* Quality dots */
.vv-dots{display:flex;gap:3px;align-items:center;}
.vv-dot{width:7px;height:7px;border-radius:50%;}

/* Avatar */
.vv-avatar{
  width:44px;height:44px;border-radius:50%;flex-shrink:0;
  background:radial-gradient(circle at 30% 30%,#feda75 0%,#fa7e1e 30%,#d62976 55%,#962fbf 75%,#4f5bd5 100%);
  display:flex;align-items:center;justify-content:center;
}
.vv-avatar-inner{
  width:40px;height:40px;border-radius:50%;background:#fff;
  display:flex;align-items:center;justify-content:center;
  font-weight:950;font-size:13px;color:#111;
}

div[data-testid="stDataFrame"]{border-radius:var(--radius);overflow:hidden;border:1px solid var(--border);}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
SESSION = requests.Session()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}

def norm(s): 
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).strip().lower()

def initials(name):
    p = [x for x in re.split(r"\s+", (name or "").strip()) if x]
    if not p: return "VV"
    if len(p) == 1: return p[0][:2].upper()
    return (p[0][0] + p[-1][0]).upper()

def maps_link(q): return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"
def ig_link(h): return f"https://instagram.com/{h.lstrip('@')}" if h and h != "N/A" else ""

def quality_score(row: dict) -> int:
    score = 0
    for k in ["Instagram", "Telefone", "Endereço", "IG Seguidores", "Website"]:
        if row.get(k) and row.get(k) != "N/A":
            score += 1
    return score

def quality_dots_html(score: int, max_score: int = 5) -> str:
    colors = {0:"#ef4444", 1:"#ef4444", 2:"#f59e0b", 3:"#f59e0b", 4:"#22c55e", 5:"#22c55e"}
    color = colors.get(score, "#9ca3af")
    dots = ""
    for i in range(max_score):
        bg = color if i < score else "#e5e7eb"
        dots += f'<div class="vv-dot" style="background:{bg}"></div>'
    return f'<div class="vv-dots">{dots}<span style="font-size:11px;color:#9ca3af;margin-left:4px">{score}/{max_score}</span></div>'

# ── Filtros OSM ───────────────────────────────────────────────────────────────
EXCLUDE_BRANDS = {
    "renner","c&a","cea","zara","riachuelo","marisa","pernambucanas","havan",
    "hering","colcci","hope","intimissimi","calzedonia","nike","adidas","puma",
    "arezzo","schutz","anacapri","loungerie","lacoste","tommy","tommy hilfiger",
    "le lis","lelis","animale","farm","dress to","dressto","john john","ellus",
}
FOOD_WORDS = {
    "restaurante","pizza","pizzaria","hamburguer","hamburgueria","burger","bar","pub",
    "café","cafe","cafeteria","padaria","confeitaria","açaí","acai","sorveteria",
    "sushi","japa","yakisoba","churrascaria","lanchonete","bistrô","bistro",
}

def is_food(name, tags):
    n = norm(name)
    if any(w in n for w in FOOD_WORDS): return True
    amenity = norm(str(tags.get("amenity", "")))
    return amenity in {"restaurant","cafe","bar","fast_food","pub","ice_cream"}

def is_excluded(name, tags):
    n = norm(name)
    brand = norm(str(tags.get("brand", "")))
    return any(b in n or b in brand for b in EXCLUDE_BRANDS)

def is_valid_store(name, tags):
    if not name: return False
    if is_food(name, tags): return False
    if is_excluded(name, tags): return False
    n = norm(name)
    positives = ["multimarca","boutique","moda","fashion","vestuario","feminina","looks","vestuário"]
    if any(k in n for k in positives): return True
    shop = norm(str(tags.get("shop", "")))
    return shop in {"boutique","clothes","apparel","fashion","clothing"}

# ── OSM / Nominatim ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def overpass_query(city: str) -> list:
    q = f"""
    [out:json][timeout:90];
    area["name"="{city}"]["boundary"="administrative"]->.s;
    (nwr["shop"~"clothes|boutique|apparel|fashion|clothing"](area.s););
    out tags center;
    """
    try:
        r = SESSION.post("https://overpass-api.de/api/interpreter",
                         data={"data": q}, headers=HEADERS, timeout=90)
        return r.json().get("elements", []) if r.ok else []
    except:
        return []

def extract_coords(el):
    if el.get("type") == "node": return el.get("lat"), el.get("lon")
    c = el.get("center") or {}
    return c.get("lat"), c.get("lon")

def addr_from_tags(tags):
    parts = [
        f"{tags.get('addr:street','')} {tags.get('addr:housenumber','')}".strip(),
        tags.get("addr:suburb",""), tags.get("addr:city",""), tags.get("addr:state","")
    ]
    return ", ".join(p for p in parts if p).strip() or None

@st.cache_data(ttl=86400, show_spinner=False)
def nominatim_reverse(lat: float, lon: float) -> Optional[dict]:
    time.sleep(1.1)
    try:
        r = SESSION.get("https://nominatim.openstreetmap.org/reverse",
            params={"format":"jsonv2","lat":lat,"lon":lon,"addressdetails":1,"accept-language":"pt-BR"},
            headers=HEADERS, timeout=20)
        return r.json() if r.ok else None
    except:
        return None

def addr_from_nominatim(data):
    if not data: return None
    a = data.get("address") or {}
    road = a.get("road") or a.get("pedestrian") or ""
    house = a.get("house_number","")
    sub = a.get("suburb") or a.get("neighbourhood","")
    city = a.get("city") or a.get("town") or a.get("village","")
    state = a.get("state","")
    parts = [f"{road} {house}".strip(), sub, city, state]
    return ", ".join(p for p in parts if p).strip() or data.get("display_name")

def ig_from_tags(tags):
    for k in ("contact:instagram","instagram","contact:insta","insta"):
        v = tags.get(k)
        if v:
            v = re.sub(r"https?://(www\.)?instagram\.com/","", str(v)).strip("/").strip()
            if v: return v
    return None

# ── Claude Search (Anthropic API) ─────────────────────────────────────────────
def get_anthropic_key() -> Optional[str]:
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except:
        return None

@st.cache_data(ttl=43200, show_spinner=False)
def claude_search_instagram(store_name: str, city: str) -> Optional[str]:
    key = get_anthropic_key()
    if not key: return None
    try:
        r = SESSION.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 200,
                "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                "messages": [{
                    "role": "user",
                    "content": (
                        f'Pesquise o Instagram da loja "{store_name}" localizada em {city}, Brasil. '
                        f'Retorne APENAS o handle do Instagram (sem @ e sem URL), exemplo: minhaloja. '
                        f'Se não encontrar com certeza absoluta, retorne exatamente: null'
                    )
                }]
            },
            timeout=30
        )
        if not r.ok: return None
        data = r.json()
        text = " ".join(b.get("text","") for b in data.get("content",[]) if b.get("type")=="text").strip()
        if not text or text.lower() == "null" or len(text) > 50: return None
        clean = re.sub(r"https?://(www\.)?instagram\.com/","", text).strip("/@\n ")
        return clean if re.match(r"^[A-Za-z0-9._]+$", clean) else None
    except:
        return None

@st.cache_data(ttl=43200, show_spinner=False)
def claude_search_cnpj(store_name: str, city: str) -> Optional[str]:
    key = get_anthropic_key()
    if not key: return None
    try:
        r = SESSION.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 200,
                "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                "messages": [{
                    "role": "user",
                    "content": (
                        f'Pesquise o CNPJ da empresa "{store_name}" localizada em {city}, Brasil. '
                        f'Retorne APENAS os 14 dígitos numéricos do CNPJ, sem pontuação, exemplo: 12345678000190. '
                        f'Se não encontrar com certeza absoluta, retorne exatamente: null'
                    )
                }]
            },
            timeout=30
        )
        if not r.ok: return None
        data = r.json()
        text = " ".join(b.get("text","") for b in data.get("content",[]) if b.get("type")=="text").strip()
        digits = re.sub(r"\D","", text)
        return digits if len(digits) == 14 else None
    except:
        return None

# ── Meta API ──────────────────────────────────────────────────────────────────
IG_USER_ID = "17841473844567187"

def get_meta_token() -> Optional[str]:
    try:
        return st.secrets.get("META_USER_TOKEN_LONG")
    except:
        return None

def meta_business_discovery(username: str, token: Optional[str] = None) -> dict:
    token = token or get_meta_token()
    if not token: return {}
    u = username.lstrip("@").strip()
    if not u: return {}

    cache = st.session_state.setdefault("meta_cache", {})
    if u in cache: return cache[u]

    fields = f"business_discovery.username({u}){{username,followers_count,media_count,biography,website}}"
    try:
        time.sleep(0.3)
        r = SESSION.get(
            f"https://graph.facebook.com/v25.0/{IG_USER_ID}",
            params={"fields": fields, "access_token": token},
            timeout=25
        )
        data = r.json() if r.ok else {}
    except:
        data = {}

    bd = data.get("business_discovery") or {}
    out = {
        "username": bd.get("username") or u,
        "followers_count": bd.get("followers_count", "N/A"),
        "media_count": bd.get("media_count", "N/A"),
        "biography": bd.get("biography") or "N/A",
        "website": bd.get("website") or "N/A",
    }
    cache[u] = out
    return out

# ── BrasilAPI ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def brasilapi_cnpj(cnpj: str) -> Optional[dict]:
    time.sleep(0.6)
    try:
        r = SESSION.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", headers=HEADERS, timeout=30)
        return r.json() if r.ok else None
    except:
        return None

def socios_str(data: dict) -> str:
    socios = data.get("qsa") or []
    items = []
    for s in socios:
        nome = s.get("nome_socio","").strip()
        qual = s.get("qualificacao_socio","").strip()
        if nome: items.append(f"{nome} ({qual})" if qual else nome)
    return "; ".join(items) or "N/A"

def cnpj_to_row(data: dict, loja: str, cidade: str, cnpj: str, status: str) -> dict:
    cnaes_sec = data.get("cnaes_secundarios") or []
    cnaes_str = "; ".join(
        f"{x.get('codigo','')} {x.get('descricao','')}".strip()
        for x in cnaes_sec if isinstance(x, dict)
    ) or "N/A"
    return {
        "Loja": loja, "Cidade": cidade,
        "CNPJ": data.get("cnpj") or cnpj or "N/A",
        "Razão Social": data.get("razao_social","N/A"),
        "Nome Fantasia": data.get("nome_fantasia","N/A"),
        "Abertura": data.get("data_inicio_atividade","N/A"),
        "Porte": data.get("porte","N/A"),
        "MEI": str(data.get("opcao_pelo_mei","N/A")),
        "Simples": str(data.get("opcao_pelo_simples","N/A")),
        "Capital Social": data.get("capital_social","N/A"),
        "Situação": data.get("descricao_situacao_cadastral","N/A"),
        "Email": data.get("email","N/A"),
        "Telefone": data.get("ddd_telefone_1","N/A"),
        "UF": data.get("uf","N/A"),
        "Município": data.get("municipio","N/A"),
        "CEP": data.get("cep","N/A"),
        "Logradouro": data.get("logradouro","N/A"),
        "Número": data.get("numero","N/A"),
        "Bairro": data.get("bairro","N/A"),
        "CNAE Principal": data.get("cnae_fiscal","N/A"),
        "CNAE Desc": data.get("cnae_fiscal_descricao","N/A"),
        "CNAEs Secundários": cnaes_str,
        "Sócios (QSA)": socios_str(data),
        "Status": status,
    }

# ── Topbar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vv-topbar">
  <div class="vv-topbar-inner">
    <div class="vv-brand">
      <h1>Verso Sourcing Pro</h1>
      <p>Encontre lojistas multimarcas · Prospecção · CNPJ · Meta API</p>
    </div>
    <div style="display:flex;gap:8px">
      <span class="vv-pill">✨ Premium</span>
      <span class="vv-pill">Streamlit</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("leads_rows", []), ("leads_df", None),
    ("cnpj_rows", []), ("cnpj_df", None),
    ("prospect", {"running":False,"stop":False,"cities":[],"limit":40,"city_idx":0,
                  "store_idx":0,"valid":[],"current_city":"","current_name":"",
                  "city_total":0,"done":0,"target_est":0,"started_at":0.0,
                  "enrich_address":True,"enrich_instagram":True,"enrich_meta":False,
                  "batch_size":1,"last_error":"","stopped_reason":""}),
    ("cnpj_job", {"running":False,"stop":False,"items":[],"idx":0,"batch_size":1,
                  "ok_total":0,"attempt_total":0,"target_est":0,"current":"",
                  "last_error":"","stopped_reason":"","started_at":0.0}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔍 Prospecção", "🏢 CNPJ", "📸 Meta API"])

# ═══════════════════════════════════════════════════════════════
# TAB 1 — PROSPECÇÃO
# ═══════════════════════════════════════════════════════════════
with tab1:
    col_panel, col_main = st.columns([0.28, 0.72], gap="large")

    with col_panel:
        with st.container():
            st.markdown("**Cidades ou bairros**")
            cities_input = st.text_area("", placeholder="São Paulo\nCuritiba\nLapa, São Paulo", height=120, key="p_cities", label_visibility="collapsed")
            st.caption("Uma por linha. Pode usar bairros: 'Lapa, São Paulo'")

            limit = st.slider("Limite por cidade/bairro", 10, 200, 40, step=10, key="p_limit")

            st.markdown("**Enriquecimento**")
            enrich_addr = st.checkbox("Endereço via OSM/Nominatim", value=True, key="p_addr")
            enrich_ig   = st.checkbox("Instagram (OSM + Claude Search)", value=True, key="p_ig")
            enrich_meta = st.checkbox("Meta API (seguidores/bio/site)", value=bool(get_meta_token()), key="p_meta")

            if not get_anthropic_key():
                st.warning("⚠️ ANTHROPIC_API_KEY não configurada. O Instagram vai usar apenas tags do OSM.")
            if enrich_meta and not get_meta_token():
                st.warning("⚠️ META_USER_TOKEN_LONG não configurada. Configure nos Secrets.")

            c1, c2 = st.columns(2)
            p = st.session_state.prospect
            with c1:
                start_p = st.button("🚀 Iniciar", key="p_start", disabled=p["running"])
            with c2:
                if st.button("⏹ Parar", key="p_stop", disabled=not p["running"]):
                    p["stop"] = True

    # Iniciar
    if start_p:
        city_list = [c.strip() for c in re.split(r"[,\n;]+", cities_input) if c.strip()]
        if not city_list:
            st.warning("Digite pelo menos uma cidade ou bairro.")
        else:
            st.session_state.leads_rows = []
            st.session_state.leads_df = pd.DataFrame()
            p.update({
                "running":True,"stop":False,"cities":city_list,"limit":limit,
                "city_idx":0,"store_idx":0,"valid":[],"current_city":"","current_name":"",
                "city_total":0,"done":0,"target_est":len(city_list)*limit,
                "enrich_address":enrich_addr,"enrich_instagram":enrich_ig,"enrich_meta":enrich_meta,
                "last_error":"","stopped_reason":"",
            })
            st.rerun()

    with col_main:
        p = st.session_state.prospect

        # ── Stepper ───────────────────────────────────────────────────────────
        def prospect_step():
            if not p["running"] or p.get("stop"):
                p["running"] = False
                if not p.get("stopped_reason"): p["stopped_reason"] = "Interrompido"
                return

            if p["city_idx"] >= len(p["cities"]):
                p["running"] = False
                p["stopped_reason"] = "Concluída"
                return

            # inicializa cidade se necessário
            if not p.get("valid"):
                city = p["cities"][p["city_idx"]]
                p["current_city"] = city
                elements = overpass_query(city)
                valid = [el for el in elements
                         if el.get("tags",{}).get("name")
                         and is_valid_store(el["tags"]["name"], el["tags"])][:p["limit"]]
                p["valid"] = valid
                p["store_idx"] = 0
                p["city_total"] = len(valid)
                if not valid:
                    p["city_idx"] += 1
                    return

            if p["store_idx"] >= p["city_total"]:
                p["city_idx"] += 1
                p["valid"] = []
                return

            el = p["valid"][p["store_idx"]]
            tags = el.get("tags", {})
            name = tags.get("name","N/A")
            lat, lon = extract_coords(el)
            p["current_name"] = name

            # endereço
            addr = addr_from_tags(tags) or "N/A"
            if addr == "N/A" and p["enrich_address"] and lat and lon:
                nom = nominatim_reverse(lat, lon)
                addr = addr_from_nominatim(nom) or "N/A"

            # telefone
            phone = (tags.get("phone") or tags.get("contact:phone") or
                     tags.get("contact:mobile") or tags.get("mobile") or "N/A")

            # instagram
            insta, ig_source = "N/A", "N/A"
            if p["enrich_instagram"]:
                h = ig_from_tags(tags)
                if h:
                    insta, ig_source = f"@{h}", "OSM"
                elif get_anthropic_key():
                    h = claude_search_instagram(name, p["current_city"])
                    if h: insta, ig_source = f"@{h}", "Claude Search"

            # meta
            ig_followers = ig_bio = ig_website = "N/A"
            if p["enrich_meta"] and insta != "N/A":
                md = meta_business_discovery(insta)
                ig_followers = md.get("followers_count","N/A")
                ig_bio       = md.get("biography","N/A")
                ig_website   = md.get("website","N/A")

            row = {
                "Loja": name, "Cidade": p["current_city"],
                "Instagram": insta, "Fonte Instagram": ig_source,
                "IG Seguidores": str(ig_followers),
                "IG Bio": ig_bio, "Website": ig_website,
                "Telefone": phone, "Endereço": addr,
                "Latitude": lat, "Longitude": lon,
            }
            st.session_state.leads_rows.append(row)
            p["store_idx"] += 1
            p["done"] += 1

            if st.session_state.leads_rows:
                st.session_state.leads_df = pd.DataFrame(st.session_state.leads_rows)

        if p["running"]:
            prospect_step()

        # ── Progress ──────────────────────────────────────────────────────────
        if p["running"]:
            prog = min(1.0, p["done"] / max(1, p["target_est"]))
            st.progress(prog)
            st.caption(f"**[{p['current_city']}]** {p['current_name']}  ({min(p['store_idx'], p['city_total'])}/{p['city_total']})")
        elif p.get("stopped_reason") and p.get("cities"):
            if p["stopped_reason"] == "Concluída":
                st.success("✅ Prospecção concluída!")
            else:
                st.warning(f"⏹ {p['stopped_reason']}")

        # ── Resultados ────────────────────────────────────────────────────────
        df = st.session_state.leads_df

        if df is None or (hasattr(df, "empty") and df.empty):
            if not p["running"]:
                st.info("Configure as cidades no painel e clique em **🚀 Iniciar**.")
        else:
            total  = len(df)
            w_ig   = int((df["Instagram"] != "N/A").sum())
            w_addr = int((df["Endereço"] != "N/A").sum())
            w_ph   = int((df["Telefone"] != "N/A").sum())
            scores = [quality_score(r) for r in st.session_state.leads_rows]
            avg_sc = f"{sum(scores)/len(scores):.1f}" if scores else "0"

            st.markdown(f"""
<div class="vv-chip-row">
  <div class="vv-chip"><span>Total</span> {total}</div>
  <div class="vv-chip"><span>Instagram</span> {w_ig}</div>
  <div class="vv-chip"><span>Endereço</span> {w_addr}</div>
  <div class="vv-chip"><span>Telefone</span> {w_ph}</div>
  <div class="vv-chip"><span>Score médio</span> {avg_sc}/5</div>
</div><hr class="vv-hr"/>
""", unsafe_allow_html=True)

            # cards (últimos 15 durante execução, todos ao final)
            render_rows = st.session_state.leads_rows[-15:] if p["running"] else st.session_state.leads_rows
            for row in render_rows:
                score = quality_score(row)
                insta  = row["Instagram"]
                ig_url = ig_link(insta)
                map_url = maps_link(row["Endereço"] if row["Endereço"] != "N/A" else f"{row['Loja']} {row['Cidade']}")
                site_btn = f"<a class='vv-link-pill vv-link-muted' href='{row['Website']}' target='_blank'>Ver Site</a>" if row.get("Website","N/A") != "N/A" else ""
                bio_html = ""
                if row.get("IG Bio","N/A") != "N/A":
                    bio = row["IG Bio"][:160] + ("…" if len(row["IG Bio"])>160 else "")
                    bio_html = f"<div style='margin-top:8px;font-size:12px;color:#6b7280;font-style:italic'>\"{bio}\"</div>"

                st.markdown(f"""
<div class="vv-card">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
    <div style="display:flex;align-items:center;gap:12px;min-width:0">
      <div class="vv-avatar"><div class="vv-avatar-inner">{initials(row['Loja'])}</div></div>
      <div>
        <p class="vv-lead-name">{row['Loja']}</p>
        <p class="vv-lead-city">{row['Cidade']}</p>
      </div>
    </div>
    {quality_dots_html(score)}
  </div>
  <div class="vv-chip-row">
    <div class="vv-chip"><span>Instagram</span> {insta}</div>
    {"<div class='vv-chip'><span>Seguidores</span> "+str(row.get('IG Seguidores','N/A'))+"</div>" if row.get('IG Seguidores','N/A') != 'N/A' else ""}
    <div class="vv-chip"><span>Telefone</span> {row['Telefone']}</div>
  </div>
  <div style="margin-top:10px;font-size:13px"><b>Endereço:</b> {row['Endereço']}</div>
  {bio_html}
  <div class="vv-actions">
    {"<a class='vv-link-pill vv-link-primary' href='"+ig_url+"' target='_blank'>Ver Instagram</a>" if ig_url else "<span class='vv-link-pill vv-link-muted'>Sem Instagram</span>"}
    {site_btn}
    <a class="vv-link-pill vv-link-muted" href="{map_url}" target="_blank">Ver no Maps</a>
  </div>
</div>
""", unsafe_allow_html=True)

            if not p["running"]:
                out = BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w:
                    df.to_excel(w, index=False, sheet_name="Leads")
                st.download_button("📥 Baixar Excel", out.getvalue(),
                    "leads_verso_vivo.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.caption(f"Mostrando os 15 mais recentes. Total: {total}")

        if p["running"]:
            time.sleep(0.15)
            st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 2 — CNPJ (independente)
# ═══════════════════════════════════════════════════════════════
with tab2:
    col_panel2, col_main2 = st.columns([0.28, 0.72], gap="large")

    with col_panel2:
        st.markdown("**Fonte dos leads**")
        cnpj_source = st.radio("", ["Cidade/Bairro (OSM)", "Lista manual", "Usar leads da prospecção"],
                               key="cnpj_src", label_visibility="collapsed")

        if cnpj_source == "Cidade/Bairro (OSM)":
            cnpj_cities = st.text_area("Cidades ou bairros", placeholder="São Paulo\nCuritiba", height=100, key="cnpj_cities")
        elif cnpj_source == "Lista manual":
            cnpj_lista = st.text_area("Lista (Loja, Cidade — uma por linha)",
                placeholder="Boutique Rosa, São Paulo\nLoja Sol, Curitiba", height=120, key="cnpj_lista")
        else:
            st.caption("Vai usar os leads já coletados na aba Prospecção.")

        cnpj_max = st.slider("Máximo de lojas", 10, 300, 80, step=10, key="cnpj_max")

        if not get_anthropic_key():
            st.warning("⚠️ ANTHROPIC_API_KEY não configurada. A busca de CNPJ não vai funcionar.")

        j = st.session_state.cnpj_job
        c1, c2 = st.columns(2)
        with c1:
            start_cnpj = st.button("🚀 Iniciar", key="cnpj_start", disabled=j["running"])
        with c2:
            if st.button("⏹ Parar", key="cnpj_stop", disabled=not j["running"]):
                j["stop"] = True

    # Montar lista de itens
    if start_cnpj:
        items: List[Dict[str,str]] = []
        if cnpj_source == "Cidade/Bairro (OSM)":
            city_list = [c.strip() for c in re.split(r"[,\n;]+", cnpj_cities) if c.strip()]
            for city in city_list:
                els = overpass_query(city)
                for el in els:
                    tags = el.get("tags",{})
                    name = tags.get("name")
                    if name and is_valid_store(name, tags):
                        items.append({"Loja": name, "Cidade": city})
        elif cnpj_source == "Lista manual":
            for line in cnpj_lista.splitlines():
                parts = [p.strip() for p in re.split(r"[,;|]", line) if p.strip()]
                if len(parts) >= 2: items.append({"Loja": parts[0], "Cidade": parts[1]})
                elif len(parts) == 1: items.append({"Loja": parts[0], "Cidade": ""})
        else:
            df_leads = st.session_state.leads_df
            if df_leads is not None and not df_leads.empty:
                for _, row in df_leads[["Loja","Cidade"]].dropna().iterrows():
                    items.append({"Loja": str(row["Loja"]), "Cidade": str(row["Cidade"])})

        items = items[:cnpj_max]
        if items:
            st.session_state.cnpj_rows = []
            st.session_state.cnpj_df = pd.DataFrame()
            j.update({
                "running":True,"stop":False,"items":items,"idx":0,
                "ok_total":0,"attempt_total":0,"target_est":len(items),
                "current":"","last_error":"","stopped_reason":"","started_at":time.time()
            })
            st.rerun()
        else:
            st.warning("Nenhum item para processar. Verifique a fonte selecionada.")

    with col_main2:
        j = st.session_state.cnpj_job

        def cnpj_step():
            if not j["running"] or j.get("stop"):
                j["running"] = False
                if not j.get("stopped_reason"): j["stopped_reason"] = "Interrompido"
                return

            items = j.get("items",[])
            idx = j["idx"]
            if idx >= len(items):
                j["running"] = False
                j["stopped_reason"] = "Concluída"
                return

            item = items[idx]
            loja, cidade = item.get("Loja",""), item.get("Cidade","")
            j["current"] = f"{loja} • {cidade}"
            j["idx"] = idx + 1
            j["attempt_total"] = j.get("attempt_total",0) + 1

            cnpj = claude_search_cnpj(loja, cidade)

            if not cnpj:
                st.session_state.cnpj_rows.append(cnpj_to_row({}, loja, cidade, "N/A", "CNPJ não encontrado"))
            else:
                data = brasilapi_cnpj(cnpj)
                if not data:
                    st.session_state.cnpj_rows.append(cnpj_to_row({}, loja, cidade, cnpj, "Erro BrasilAPI"))
                else:
                    st.session_state.cnpj_rows.append(cnpj_to_row(data, loja, cidade, cnpj, "OK"))
                    j["ok_total"] = j.get("ok_total",0) + 1

            if st.session_state.cnpj_rows:
                st.session_state.cnpj_df = pd.DataFrame(st.session_state.cnpj_rows)

        if j["running"]:
            cnpj_step()

        if j["running"]:
            done, total = j["idx"], max(1, j["target_est"])
            st.progress(min(1.0, done/total))
            st.caption(f"**Processando:** {j['current']}  ({done}/{total})")
        elif j.get("stopped_reason") and j.get("items"):
            if j["stopped_reason"] == "Concluída":
                st.success("✅ Enriquecimento de CNPJ concluído!")
            else:
                st.warning(f"⏹ {j['stopped_reason']}")

        dfc = st.session_state.cnpj_df
        if dfc is None or (hasattr(dfc,"empty") and dfc.empty):
            if not j["running"]:
                st.info("Escolha a fonte no painel e clique em **🚀 Iniciar**.")
        else:
            ok   = int((dfc.get("Status", pd.Series(dtype=str)) == "OK").sum())
            found = int((dfc.get("CNPJ", pd.Series(dtype=str)).astype(str) != "N/A").sum())
            st.markdown(f"""
<div class="vv-chip-row">
  <div class="vv-chip"><span>Total</span> {len(dfc)}</div>
  <div class="vv-chip"><span>CNPJ encontrado</span> {found}</div>
  <div class="vv-chip"><span>OK (BrasilAPI)</span> {ok}</div>
</div><hr class="vv-hr"/>
""", unsafe_allow_html=True)

            st.dataframe(dfc.tail(80) if j["running"] else dfc, use_container_width=True, hide_index=True)

            if not j["running"]:
                out = BytesIO()
                with pd.ExcelWriter(out, engine="openpyxl") as w:
                    dfc.to_excel(w, index=False, sheet_name="Empresas")
                st.download_button("📥 Baixar Excel", out.getvalue(),
                    "empresas_verso_vivo.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if j["running"]:
            time.sleep(0.15)
            st.rerun()

# ═══════════════════════════════════════════════════════════════
# TAB 3 — META API
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Meta API — Business Discovery")
    st.caption(f"IG User ID configurado: **{IG_USER_ID}** (Verso Vivo)")

    token = get_meta_token()
    if token:
        st.success("✅ META_USER_TOKEN_LONG detectado nos Secrets.")
    else:
        st.warning("⚠️ Configure META_USER_TOKEN_LONG nos Secrets do Streamlit Cloud.")
        token = st.text_input("Ou cole o token temporariamente aqui:", type="password", key="meta_tmp_token")

    st.markdown("---")
    test_user = st.text_input("Username para teste (sem @)", value="oficialversovivo", key="meta_test_user")
    if st.button("🧪 Testar Business Discovery"):
        if not token:
            st.error("Token não configurado.")
        else:
            with st.spinner("Consultando Meta API…"):
                res = meta_business_discovery(test_user, token)
            if res and res.get("followers_count","N/A") != "N/A":
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Seguidores", f"{res['followers_count']:,}".replace(",","."))
                    st.metric("Posts", res.get("media_count","N/A"))
                with col_b:
                    st.info(f"**Bio:** {res.get('biography','N/A')}")
                    if res.get("website","N/A") != "N/A":
                        st.markdown(f"**Site:** [{res['website']}]({res['website']})")
                st.success("✅ Meta API funcionando corretamente!")
            else:
                st.error("Sem retorno. Verifique o token e se o username é uma conta Business/Creator.")
                st.json(res)
