import streamlit as st
import pandas as pd
import requests
import re
import time
import random
from bs4 import BeautifulSoup
from io import BytesIO
from urllib.parse import quote_plus

# =========================
# CONFIGURAÇÕES DA PÁGINA
# =========================
st.set_page_config(page_title="Verso Sourcing Pro", page_icon="📸", layout="wide")

# =========================
# CSS (Instagram Web-ish)
# =========================
st.markdown("""
<style>
/* ====== Base typography (SF on Apple, Segoe on Windows) ====== */
html, body, [class*="st-"] {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
               "Helvetica Neue", Helvetica, Arial, "Segoe UI", Roboto, sans-serif !important;
  color: #0f1419;
}

/* Page background like Instagram */
.stApp { background: #fafafa; }

/* Centered container */
.main .block-container{
  max-width: 1200px;
  padding-top: 1.0rem;
  padding-bottom: 2rem;
}

/* Hide Streamlit chrome for “app” feel */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Navbar */
.navbar {
  position: sticky;
  top: 0;
  z-index: 999;
  background: rgba(250,250,250,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #dbdbdb;
  padding: 10px 0;
  margin: -1rem -1rem 1rem -1rem;
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
.brand{
  display:flex;
  align-items:center;
  gap:10px;
  min-width: 220px;
}
.brand-title{
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.2px;
}
.brand-sub{
  font-size: 12px;
  color: #6e6e6e;
  margin-top: -2px;
}
.nav-actions{
  display:flex;
  gap:8px;
  align-items:center;
  justify-content:flex-end;
  min-width: 220px;
}
.icon-pill{
  display:inline-flex;
  align-items:center;
  gap:8px;
  border-radius:999px;
  padding:8px 12px;
  background:#ffffff;
  border:1px solid #dbdbdb;
  font-size:12px;
  font-weight:700;
  color:#111;
}

/* Inputs */
.stTextInput>div>div>input, .stTextArea textarea {
  border-radius: 12px !important;
  border: 1px solid #dbdbdb !important;
  background: #fff !important;
  padding: 12px 12px !important;
  box-shadow: none !important;
}
.stSelectbox>div>div>div {
  border-radius: 12px !important;
  border: 1px solid #dbdbdb !important;
  background: #fff !important;
}

/* Primary button (Instagram blue, pill) */
.stButton>button{
  width:100%;
  border-radius: 999px !important;
  border: 1px solid transparent !important;
  background: #0095f6 !important;
  color: #fff !important;
  font-weight: 800 !important;
  height: 44px !important;
  box-shadow: none !important;
  transition: filter .15s ease, transform .15s ease;
}
.stButton>button:hover{
  filter: brightness(0.95);
  transform: translateY(-1px);
}

/* Secondary buttons (we emulate via st.markdown links styled as pills) */
a { color:#00376b !important; text-decoration:none; }
a:hover { text-decoration:underline; }

.chip-row{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top: 10px;
}
.chip{
  display:inline-flex;
  align-items:center;
  gap:8px;
  border-radius:999px;
  padding:6px 10px;
  background:#efefef;
  border:1px solid #efefef;
  font-size:12px;
  font-weight:700;
  color:#111;
}
.chip-muted{
  font-weight:700;
  color:#6e6e6e;
}

/* Sidebar card (right column) */
.panel{
  background:#fff;
  border:1px solid #dbdbdb;
  border-radius:18px;
  padding:14px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}
.panel-title{
  font-size: 14px;
  font-weight: 900;
  margin-bottom: 10px;
}
.panel-help{
  font-size: 12px;
  color: #6e6e6e;
  line-height: 1.35;
}

/* “Post” card */
.post{
  background:#fff;
  border:1px solid #dbdbdb;
  border-radius:18px;
  padding:14px 14px 12px 14px;
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
  width:38px;
  height:38px;
  border-radius:999px;
  background: linear-gradient(135deg,#feda75,#fa7e1e,#d62976,#962fbf,#4f5bd5);
  display:flex;
  align-items:center;
  justify-content:center;
  flex:0 0 auto;
}
.avatar-inner{
  width:34px;
  height:34px;
  border-radius:999px;
  background:#fff;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight:900;
  font-size:12px;
  color:#111;
}
.user-meta{
  display:flex;
  flex-direction:column;
  min-width:0;
}
.user-name{
  font-weight:900;
  font-size:14px;
  line-height:1.2;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.user-city{
  font-size:12px;
  color:#6e6e6e;
}
.post-body{
  font-size:13px;
  color:#111;
  line-height:1.35;
}
.bio{
  margin-top:6px;
  color:#444;
  display:-webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow:hidden;
}
.meta-row{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:10px;
}
.pill-link{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  border-radius:999px;
  padding:8px 12px;
  font-size:12px;
  font-weight:900;
  border:1px solid #dbdbdb;
  background:#fff;
  color:#111 !important;
  text-decoration:none !important;
}
.pill-link:hover{ filter: brightness(0.98); text-decoration:none !important; }
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
.small-note{
  font-size: 12px;
  color:#6e6e6e;
}
hr.sep{
  border: none;
  border-top: 1px solid #efefef;
  margin: 12px 0;
}
</style>
""", unsafe_allow_html=True)

# =========================
# FUNÇÕES DE BUSCA
# =========================

def overpass_query(city_name: str):
    """Busca lojas no Overpass API."""
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

def search_instagram_username(store_name: str, city: str):
    """Busca o username do Instagram no Google via raspagem leve."""
    query = f"{store_name} {city} instagram"
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36")
    }
    try:
        time.sleep(random.uniform(1.0, 2.0))
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'instagram.com/' in href:
                    match = re.search(r'instagram\.com/([^/?&]+)', href)
                    if match:
                        username = match.group(1)
                        if username not in ['reels', 'stories', 'explore', 'p', 'tags']:
                            return username
        return None
    except Exception:
        return None

def get_instagram_data(username: str):
    """Extrai seguidores e bio do perfil público do Instagram."""
    if not username:
        return "N/A", "N/A", "N/A"
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0 Safari/537.36")
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc:
                content = meta_desc.get("content", "")
                followers_match = re.search(r'([\d.,KM]+)\s*Followers', content)
                followers = followers_match.group(1) if followers_match else "N/A"
                return f"@{username}", followers, content
        return f"@{username}", "N/A", "Perfil encontrado"
    except Exception:
        return f"@{username}", "N/A", "Erro ao acessar"

def is_valid_store(name: str, tags: dict):
    """Filtra para manter apenas lojas de moda feminina e excluir grandes redes."""
    name_lower = name.lower()
    exclude = [
        'renner','c&a','zara','riachuelo','marisa','pernambucanas',
        'havan','carrefour','extra','pão de açúcar','pao de acucar'
    ]
    if any(x in name_lower for x in exclude):
        return False

    keywords = ['feminina','boutique','concept','moda','fashion','estilo','look','vestuário','vestuario','multimarca']
    if any(k in name_lower for k in keywords):
        return True

    shop_type = tags.get('shop', '')
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

def render_navbar():
    st.markdown("""
    <div class="navbar">
      <div class="nav-inner">
        <div class="brand">
          <div>
            <div class="brand-title">Verso Sourcing Pro</div>
            <div class="brand-sub">Prospecção com estética Instagram Web</div>
          </div>
        </div>
        <div class="nav-actions">
          <div class="icon-pill">📍 Leads</div>
          <div class="icon-pill">✨ Feed</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

render_navbar()

# =========================
# ESTADO
# =========================
if "df" not in st.session_state:
    st.session_state.df = None
if "cities" not in st.session_state:
    st.session_state.cities = []
if "running" not in st.session_state:
    st.session_state.running = False

# =========================
# LAYOUT (Feed + Side)
# =========================
col_feed, col_side = st.columns([0.68, 0.32], gap="large")

with col_side:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Configurações</div>', unsafe_allow_html=True)

    # Logo opcional (não quebra se não existir)
    try:
        st.image("LOGOOFICIALBRANCA.png", use_container_width=True)
    except Exception:
        st.markdown('<div class="small-note">Logo não encontrada (LOGOOFICIALBRANCA.png).</div>', unsafe_allow_html=True)

    city_input = st.text_input("Cidades (separadas por vírgula)", placeholder="Ex: São Paulo, Curitiba")
    limit = st.slider("Limite de lojas por cidade", 10, 500, 100)

    st.markdown('<hr class="sep"/>', unsafe_allow_html=True)
    st.markdown('<div class="panel-help">O enriquecimento do Instagram pode demorar alguns segundos por loja para evitar bloqueios. Em listas grandes, comece com 20–50 por cidade.</div>', unsafe_allow_html=True)

    start = st.button("🚀 Iniciar prospecção")
    st.markdown('</div>', unsafe_allow_html=True)

def run_prospect(cities, limit):
    all_leads = []
    progress_bar = col_feed.progress(0)
    status_text = col_feed.empty()

    for idx, city in enumerate(cities):
        status_text.markdown(f"**Buscando lojas em {city}...**")
        raw_elements = overpass_query(city)

        valid_stores = []
        for el in raw_elements:
            tags = el.get('tags', {})
            name = tags.get('name')
            if name and is_valid_store(name, tags):
                valid_stores.append((name, tags))

        valid_stores = valid_stores[:limit]

        for i, (name, tags) in enumerate(valid_stores):
            status_text.markdown(f"**[{city}] Enriquecendo:** {name}  \n<i class='small-note'>({i+1}/{len(valid_stores)})</i>", unsafe_allow_html=True)

            username = search_instagram_username(name, city)
            handle, followers, bio = get_instagram_data(username)

            address = f"{tags.get('addr:street', '')}, {tags.get('addr:housenumber', '')}".strip(', ').strip()
            if not address:
                address = "N/A"

            all_leads.append({
                "Loja": name,
                "Cidade": city,
                "Instagram": handle,
                "Seguidores": followers,
                "Bio": bio,
                "Telefone": tags.get('phone') or tags.get('contact:phone') or "N/A",
                "Endereço": address
            })

        progress_bar.progress((idx + 1) / max(1, len(cities)))

    status_text.markdown("✅ **Prospecção concluída!**")
    return pd.DataFrame(all_leads) if all_leads else pd.DataFrame()

# =========================
# AÇÃO
# =========================
if start:
    # split robusto por vírgula
    cities = [c.strip() for c in re.split(r",|\n|;", city_input) if c.strip()]
    st.session_state.cities = cities

    if not cities:
        with col_feed:
            st.warning("Por favor, digite pelo menos uma cidade.")
    else:
        st.session_state.running = True
        df = run_prospect(cities, limit)
        st.session_state.df = df
        st.session_state.running = False

# =========================
# FEED (Resultados)
# =========================
with col_feed:
    st.markdown("### ✨ Feed de Leads")

    df = st.session_state.df

    if df is None:
        st.markdown("<div class='small-note'>Configure as cidades ao lado e clique em <b>Iniciar prospecção</b>.</div>", unsafe_allow_html=True)

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

        # Render posts
        for _, row in df.iterrows():
            loja = str(row["Loja"])
            cidade = str(row["Cidade"])
            insta = str(row["Instagram"])
            seguidores = str(row["Seguidores"])
            bio = str(row["Bio"])
            telefone = str(row["Telefone"])
            endereco = str(row["Endereço"])

            av = initials(loja)
            insta_url = f"https://instagram.com/{insta[1:]}" if insta.startswith("@") else None
            maps_url = maps_link(endereco, cidade, loja)

            actions_html = []
            if insta_url:
                actions_html.append(f"<a class='pill-link pill-primary' href='{insta_url}' target='_blank'>Ver Instagram</a>")
            else:
                actions_html.append(f"<span class='pill-link pill-muted'>Sem Instagram</span>")
            actions_html.append(f"<a class='pill-link pill-muted' href='{maps_url}' target='_blank'>Ver no Maps</a>")

            # Copy phone using JS (works on most modern browsers)
            copy_btn = ""
            if telefone and telefone != "N/A":
                safe_phone = telefone.replace("'", "\\'")
                copy_btn = f"""
                <a class='pill-link pill-muted' href='#' onclick="navigator.clipboard.writeText('{safe_phone}'); return false;">Copiar telefone</a>
                """
            else:
                copy_btn = "<span class='pill-link pill-muted'>Telefone N/A</span>"

            st.markdown(f"""
            <div class="post">
              <div class="post-header">
                <div class="user">
                  <div class="avatar"><div class="avatar-inner">{av}</div></div>
                  <div class="user-meta">
                    <div class="user-name">{loja}</div>
                    <div class="user-city">{cidade}</div>
                  </div>
                </div>
              </div>

              <div class="post-body">
                <div><b>Instagram:</b> {"<a href='"+insta_url+"' target='_blank'>"+insta+"</a>" if insta_url else insta}</div>
                <div class="meta-row">
                  <span class="chip"><span class="chip-muted">Seguidores:</span> {seguidores}</span>
                  <span class="chip"><span class="chip-muted">Telefone:</span> {telefone}</span>
                </div>
                <div class="bio"><b>Bio:</b> {bio}</div>
                <div class="small-note" style="margin-top:8px;"><b>Endereço:</b> {endereco}</div>

                <div class="meta-row" style="margin-top:12px;">
                  {"".join(actions_html)}
                  {copy_btn}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Download Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads')

        st.download_button(
            label="📥 Baixar Planilha Excel (.xlsx)",
            data=output.getvalue(),
            file_name="leads_verso_vivo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
