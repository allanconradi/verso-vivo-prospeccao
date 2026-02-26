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

# =========================
# CONFIGURAÇÕES DA PÁGINA
# =========================
st.set_page_config(page_title="Verso Sourcing Pro", page_icon="📸", layout="wide")

# =========================
# CSS (Instagram-like, desktop) + SIDEBAR FIXA
# =========================
st.markdown("""
<style>
/* ====== Base typography (SF on Apple, Segoe on Windows) ====== */
html, body, [class*="st-"] {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
               "Helvetica Neue", Helvetica, Arial, "Segoe UI", Roboto, sans-serif !important;
  color: #0f1419;
  font-size: 16px;
}

/* Background */
.stApp { background: #fafafa; }

/* Content width */
.main .block-container{
  max-width: 1200px;
  padding-top: 1.25rem;
  padding-bottom: 2rem;
}

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Navbar */
.navbar {
  position: sticky;
  top: 0;
  z-index: 999;
  background: rgba(250,250,250,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #dbdbdb;
  padding: 12px 0;
  margin: -1.25rem -1rem 1rem -1rem;
}
.nav-inner{
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
}
.brand-title{
  font-size: 18px;
  font-weight: 900;
  letter-spacing: -0.3px;
}
.brand-sub{
  font-size: 13px;
  color: #6e6e6e;
  margin-top: -2px;
}
.icon-pill{
  display:inline-flex;
  align-items:center;
  gap:8px;
  border-radius:999px;
  padding:10px 14px;
  background:#ffffff;
  border:1px solid #dbdbdb;
  font-size:13px;
  font-weight:800;
  color:#111;
}

/* Inputs bigger */
.stTextInput>div>div>input, .stTextArea textarea {
  border-radius: 14px !important;
  border: 1px solid #dbdbdb !important;
  background: #fff !important;
  padding: 14px 14px !important;
  box-shadow: none !important;
  font-size: 15px !important;
}
.stSlider > div { padding-top: 0.25rem; }
.stSelectbox>div>div>div {
  border-radius: 14px !important;
  border: 1px solid #dbdbdb !important;
  background: #fff !important;
}

/* Primary button bigger */
.stButton>button{
  width:100%;
  border-radius: 999px !important;
  border: 1px solid transparent !important;
  background: #0095f6 !important;
  color: #fff !important;
  font-weight: 900 !important;
  height: 52px !important;
  font-size: 15px !important;
  box-shadow: none !important;
  transition: filter .15s ease, transform .15s ease;
}
.stButton>button:hover{
  filter: brightness(0.95);
  transform: translateY(-1px);
}

/* Chips */
.chip-row{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-top: 12px;
}
.chip{
  display:inline-flex;
  align-items:center;
  gap:8px;
  border-radius:999px;
  padding:8px 12px;
  background:#efefef;
  border:1px solid #efefef;
  font-size:13px;
  font-weight:900;
  color:#111;
}
.chip-muted{ color:#6e6e6e; font-weight:900; }

/* Panel */
.panel{
  background:#fff;
  border:1px solid #dbdbdb;
  border-radius:20px;
  padding:16px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}

/* Make the settings panel sticky (never “sumir”) */
.sticky-panel{
  position: sticky;
  top: 86px; /* below navbar */
  max-height: calc(100vh - 110px);
  overflow: auto;
  padding-bottom: 8px;
}

/* Post card */
.post{
  background:#fff;
  border:1px solid #dbdbdb;
  border-radius:20px;
  padding:16px 16px 14px 16px;
  margin-bottom:14px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}
.post-header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  margin-bottom:10px;
}
.user{
  display:flex;
  align-items:center;
  gap:10px;
  min-width:0;
}
.avatar{
  width:42px;
  height:42px;
  border-radius:999px;
  background: linear-gradient(135deg,#feda75,#fa7e1e,#d62976,#962fbf,#4f5bd5);
  display:flex;
  align-items:center;
  justify-content:center;
  flex:0 0 auto;
}
.avatar-inner{
  width:38px;
  height:38px;
  border-radius:999px;
  background:#fff;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight:900;
  font-size:13px;
  color:#111;
}
.user-name{
  font-weight:900;
  font-size:15px;
  line-height:1.2;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.user-city{
  font-size:13px;
  color:#6e6e6e;
}
.bio{
  margin-top:8px;
  color:#444;
  display:-webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow:hidden;
  font-size: 14px;
}
.small-note{
  font-size: 13px;
  color:#6e6e6e;
}
.meta-row{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-top:12px;
}

/* Pills */
.pill-link{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  border-radius:999px;
  padding:10px 14px;
  font-size:13px;
  font-weight:900;
  border:1px solid #dbdbdb;
  background:#fff;
  color:#111 !important;
  text-decoration:none !important;
}
.pill-primary{
  border:1px solid #0095f6;
  background:#0095f6;
  color:#fff !important;
}
.pill-muted{
  background:#efefef;
  border:1px solid #efefef;
  color:#111 !important;
}
hr.sep{
  border: none;
  border-top: 1px solid #efefef;
  margin: 14px 0;
}
a { color:#00376b !important; text-decoration:none; }
a:hover { text-decoration:underline; }
</style>
""", unsafe_allow_html=True)

def render_navbar():
    st.markdown("""
    <div class="navbar">
      <div class="nav-inner">
        <div>
          <div class="brand-title">Verso Sourcing Pro</div>
          <div class="brand-sub">Prospecção de lojistas com estética Instagram</div>
        </div>
        <div style="display:flex; gap:10px; align-items:center;">
          <div class="icon-pill">📍 Leads</div>
          <div class="icon-pill">✨ Feed</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# FUNÇÕES DE BUSCA
# =========================
def overpass_query(city_name: str):
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:90];
    area["name"="{city_name}"]["boundary"="administrative"]->.searchArea;
    (
      nwr["shop"~"clothes|boutique|apparel|fashion|clothing"](area.searchArea);
    );
    out center tags;
    """
    try:
        response = requests.get(overpass_url, params={'data': query}, timeout=90)
        if response.status_code == 200:
            return response.json().get('elements', [])
        return []
    except Exception:
        return []

FOOD_WORDS = [
    "restaurante","restaurant","bar","pub","lanchonete","lanche","pizzaria","pizza","hamburguer",
    "burger","café","cafe","coffee","bistrô","bistro","sushi","yakisoba","pastelaria",
    "padaria","bakery","confeitaria","doceria","sorveteria","açaí","acai","churrascaria",
    "steakhouse","cervejaria","brew","adega","vinhos","food","comida","bebida","bebidas"
]
FOOD_AMENITIES = {"restaurant","cafe","bar","pub","fast_food","ice_cream","food_court"}

def is_food_related(name: str, tags: dict) -> bool:
    n = (name or "").lower()
    if any(w in n for w in FOOD_WORDS):
        return True
    amenity = (tags.get("amenity") or "").lower()
    if amenity in FOOD_AMENITIES:
        return True
    if "cuisine" in tags:
        return True
    return False

def is_valid_store(name: str, tags: dict) -> bool:
    if not name:
        return False

    name_lower = name.lower()
    exclude_big = [
        'renner','c&a','zara','riachuelo','marisa','pernambucanas',
        'havan','carrefour','extra','pão de açúcar','pao de acucar'
    ]
    if any(x in name_lower for x in exclude_big):
        return False

    if is_food_related(name, tags):
        return False

    keywords = ['feminina','boutique','concept','moda','fashion','estilo','look','vestuário','vestuario','multimarca']
    if any(k in name_lower for k in keywords):
        return True

    shop_type = (tags.get('shop') or '').lower()
    if shop_type in ['boutique', 'clothes']:
        return True

    return False

def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return "VV"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def maps_link(address: str, city: str, store: str) -> str:
    q = address if address and address != "N/A" else f"{store} {city}"
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"

def google_html(query: str):
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/122.0 Safari/537.36"),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    time.sleep(random.uniform(0.9, 1.8))
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.text
        return None
    except Exception:
        return None

def extract_instagram_from_google(html: str, city: str | None):
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    city_l = (city or "").lower().strip()

    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "instagram.com/" not in href:
            continue
        m = re.search(r"instagram\.com/([^/?&]+)", href)
        if not m:
            continue
        username = m.group(1)
        if username in {"reels","stories","explore","p","tags"}:
            continue

        # score by nearby text mentioning the city
        score = 0
        parent_text = ""
        for parent in [a.parent, a.parent.parent if a.parent else None]:
            if parent:
                parent_text += " " + parent.get_text(" ", strip=True)
        t = parent_text.lower()
        if city_l and city_l in t:
            score += 2

        candidates.append((score, username))

    if not candidates:
        return None
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return candidates[0][1]

def find_instagram_username(store_name: str, city: str):
    # 1) "Loja Instagram" (match city in snippet)
    html1 = google_html(f"{store_name} instagram")
    u1 = extract_instagram_from_google(html1, city)
    if u1:
        return u1
    # 2) fallback "Loja Cidade Instagram"
    html2 = google_html(f"{store_name} {city} instagram")
    u2 = extract_instagram_from_google(html2, city)
    return u2

# =========================
# APP
# =========================
render_navbar()

if "df" not in st.session_state:
    st.session_state.df = None

col_feed, col_side = st.columns([0.68, 0.32], gap="large")

with col_side:
    # Sticky wrapper + panel
    st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### Configurações")

    # Logo (nunca derruba o app)
    logo_path = Path(__file__).parent / "LOGOOFICIALBRANCA.png"
    if logo_path.exists():
        st.image(str(logo_path), width=240)

    city_input = st.text_input("Cidades (separadas por vírgula)", placeholder="Ex: São Paulo, Curitiba")
    limit = st.slider("Limite de lojas por cidade", 10, 500, 100)
    st.markdown("<hr class='sep'/>", unsafe_allow_html=True)
    st.markdown("<div class='small-note'>Dica: comece com 20–50 por cidade para reduzir bloqueios do Google.</div>", unsafe_allow_html=True)

    start = st.button("🚀 Iniciar prospecção")

    st.markdown("</div>", unsafe_allow_html=True)  # panel
    st.markdown("</div>", unsafe_allow_html=True)  # sticky-panel

def run_prospect(cities, limit):
    all_leads = []
    progress_bar = col_feed.progress(0)
    status_text = col_feed.empty()

    for idx, city in enumerate(cities):
        status_text.markdown(f"**Buscando lojas em {city}...**")
        raw_elements = overpass_query(city)

        valid = []
        for el in raw_elements:
            tags = el.get("tags", {}) or {}
            name = tags.get("name")
            if name and is_valid_store(name, tags):
                valid.append((name, tags))

        valid = valid[:limit]

        for i, (name, tags) in enumerate(valid):
            status_text.markdown(f"**[{city}] Enriquecendo:** {name}  \n<span class='small-note'>({i+1}/{len(valid)})</span>", unsafe_allow_html=True)

            username = find_instagram_username(name, city)
            handle = f"@{username}" if username else "N/A"

            address = f"{tags.get('addr:street', '')}, {tags.get('addr:housenumber', '')}".strip(", ").strip()
            if not address:
                address = "N/A"

            all_leads.append({
                "Loja": name,
                "Cidade": city,
                "Instagram": handle,
                "Telefone": tags.get("phone") or tags.get("contact:phone") or "N/A",
                "Endereço": address,
            })

        progress_bar.progress((idx + 1) / max(1, len(cities)))

    status_text.markdown("✅ **Prospecção concluída!**")
    return pd.DataFrame(all_leads) if all_leads else pd.DataFrame()

if start:
    cities = [c.strip() for c in re.split(r",|\n|;", city_input or "") if c.strip()]
    if not cities:
        with col_feed:
            st.warning("Por favor, digite pelo menos uma cidade.")
    else:
        st.session_state.df = run_prospect(cities, limit)

with col_feed:
    st.markdown("## ✨ Feed de Leads")
    df = st.session_state.df

    if df is None:
        st.markdown("<div class='small-note'>Digite as cidades à direita e clique em <b>Iniciar prospecção</b>.</div>", unsafe_allow_html=True)
    elif df.empty:
        st.info("Nenhuma loja encontrada com os filtros atuais. Tente outra cidade ou aumente o limite.")
    else:
        total = len(df)
        cities_n = len(set(df["Cidade"]))
        with_insta = int((df["Instagram"] != "N/A").sum())

        st.markdown(f"""
        <div class="chip-row">
          <div class="chip"><span class="chip-muted">Total:</span> {total}</div>
          <div class="chip"><span class="chip-muted">Cidades:</span> {cities_n}</div>
          <div class="chip"><span class="chip-muted">Com Instagram:</span> {with_insta}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr class='sep'/>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            loja = str(row["Loja"])
            cidade = str(row["Cidade"])
            insta = str(row["Instagram"])
            telefone = str(row["Telefone"])
            endereco = str(row["Endereço"])

            av = initials(loja)
            insta_url = f"https://instagram.com/{insta[1:]}" if insta.startswith("@") else None
            maps_url = maps_link(endereco, cidade, loja)

            actions = []
            if insta_url:
                actions.append(f"<a class='pill-link pill-primary' href='{insta_url}' target='_blank'>Ver Instagram</a>")
            else:
                actions.append("<span class='pill-link pill-muted'>Sem Instagram</span>")
            actions.append(f"<a class='pill-link pill-muted' href='{maps_url}' target='_blank'>Ver no Maps</a>")

            if telefone and telefone != "N/A":
                safe_phone = telefone.replace("'", "\\'")
                copy_btn = f"<a class='pill-link pill-muted' href='#' onclick=\"navigator.clipboard.writeText('{safe_phone}'); return false;\">Copiar telefone</a>"
            else:
                copy_btn = "<span class='pill-link pill-muted'>Telefone N/A</span>"

            st.markdown(f"""
            <div class="post">
              <div class="post-header">
                <div class="user">
                  <div class="avatar"><div class="avatar-inner">{av}</div></div>
                  <div>
                    <div class="user-name">{loja}</div>
                    <div class="user-city">{cidade}</div>
                  </div>
                </div>
              </div>

              <div>
                <div style="font-size:14px;"><b>Instagram:</b> {("<a href='"+insta_url+"' target='_blank'>"+insta+"</a>") if insta_url else insta}</div>
                <div class="meta-row">
                  <span class="chip"><span class="chip-muted">Telefone:</span> {telefone}</span>
                </div>
                <div class="small-note" style="margin-top:8px;"><b>Endereço:</b> {endereco}</div>

                <div class="meta-row" style="margin-top:12px;">
                  {"".join(actions)}
                  {copy_btn}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Leads")

        st.download_button(
            label="📥 Baixar Planilha Excel (.xlsx)",
            data=output.getvalue(),
            file_name="leads_verso_vivo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
