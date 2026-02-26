import streamlit as st
import pandas as pd
import requests
import re
import time
import random
from bs4 import BeautifulSoup
from io import BytesIO
from urllib.parse import quote_plus

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Verso Vivo - Buscador Multimarcas", page_icon="📸", layout="wide")

# --- CSS (Instagram-like, desktop, SF font, bigger UI) ---
st.markdown("""
<style>
/* SF on macOS/iOS, Segoe on Windows (desktop) */
html, body, [class*="st-"] {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
               "Helvetica Neue", Helvetica, Arial, "Segoe UI", Roboto, sans-serif !important;
  color: #111;
}

/* Background like Instagram web */
.stApp { background: #fafafa; }
.main .block-container { padding-top: 1.8rem; padding-bottom: 2.2rem; max-width: 1400px; }

/* Hide Streamlit chrome (optional) */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Headings */
h1 { font-size: 38px !important; font-weight: 900 !important; letter-spacing: -0.5px; margin-bottom: 0.25rem; }
h2 { font-size: 26px !important; font-weight: 800 !important; letter-spacing: -0.3px; }
h3 { font-size: 20px !important; font-weight: 800 !important; }

/* Inputs */
.stTextInput > div > div > input {
  border-radius: 14px !important;
  border: 1px solid #dbdbdb !important;
  background: #fff !important;
  padding: 12px 14px !important;
  font-size: 15px !important;
  height: 48px !important;
}
.stSelectbox > div > div > div, .stSlider {
  font-size: 15px !important;
}
.stSlider > div { padding-top: 8px; }

/* Sidebar look */
section[data-testid="stSidebar"] {
  background: #ffffff !important;
  border-right: 1px solid #ededed !important;
}
section[data-testid="stSidebar"] .block-container {
  padding-top: 1.25rem !important;
}

/* Primary button (bigger) */
.stButton > button {
  width: 100%;
  border-radius: 999px !important;
  border: 1px solid transparent !important;
  background: #0095f6 !important; /* IG blue */
  color: #fff !important;
  font-weight: 900 !important;
  font-size: 16px !important;
  height: 52px !important;
  box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;
  transition: filter .15s ease, transform .15s ease;
}
.stButton > button:hover { filter: brightness(0.96); transform: translateY(-1px); }

/* Progress bar */
.stProgress > div > div > div > div { background-color: #0095f6 !important; }

/* Metric chips */
.chip-row{ display:flex; flex-wrap:wrap; gap:10px; margin: 6px 0 18px 0;}
.chip{
  display:inline-flex; align-items:center; gap:8px;
  padding: 8px 12px; border-radius: 999px;
  background: #efefef; border: 1px solid #efefef;
  font-size: 13px; font-weight: 900; color: #111;
}
.chip span{ color:#6e6e6e; font-weight: 900; }

/* Result card (Instagram-like post) */
.card {
  background-color: #fff;
  padding: 18px 18px 16px 18px;
  border-radius: 18px;
  border: 1px solid #dbdbdb;
  margin-bottom: 16px;
  box-shadow: 0 1px 0 rgba(0,0,0,0.02);
}
.card-header{
  display:flex; align-items:center; justify-content:space-between; gap:12px;
  margin-bottom: 10px;
}
.user{
  display:flex; align-items:center; gap:12px; min-width:0;
}
.avatar{
  width:44px; height:44px; border-radius: 999px;
  background: linear-gradient(135deg,#feda75,#fa7e1e,#d62976,#962fbf,#4f5bd5);
  display:flex; align-items:center; justify-content:center; flex: 0 0 auto;
}
.avatar-inner{
  width:40px; height:40px; border-radius: 999px; background:#fff;
  display:flex; align-items:center; justify-content:center;
  font-weight: 900; font-size: 13px;
}
.title{
  font-weight: 950; font-size: 16px; line-height: 1.15;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.subtitle{ font-size: 13px; color:#6e6e6e; margin-top: 1px; }

.row{ margin-top: 8px; font-size: 14px; line-height: 1.35; color:#111; }
.label{ color:#6e6e6e; font-weight: 900; margin-right: 6px; }

.actions{ display:flex; gap:10px; flex-wrap:wrap; margin-top: 12px; }
.pill{
  display:inline-flex; align-items:center; justify-content:center;
  padding: 10px 14px; border-radius: 999px;
  font-size: 13px; font-weight: 950;
  border: 1px solid #dbdbdb; background:#fff; color:#111 !important;
  text-decoration:none !important;
}
.pill-primary{ background:#0095f6; border-color:#0095f6; color:#fff !important; }
.pill-muted{ background:#efefef; border-color:#efefef; color:#111 !important; }

a { color:#00376b !important; text-decoration:none; }
a:hover { text-decoration:underline; }
.small-note{ color:#6e6e6e; font-size: 13px; }

</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BUSCA ---

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
                       "Chrome/123.0 Safari/537.36"),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    try:
        time.sleep(random.uniform(1.0, 2.0))
        response = requests.get(url, headers=headers, timeout=12)
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
                       "Chrome/123.0 Safari/537.36"),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    try:
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc:
                content = meta_desc.get("content", "")
                followers_match = re.search(r'([\d.,KM]+)\s*Followers', content)
                followers = followers_match.group(1) if followers_match else "N/A"
                return f"@{username}", followers, content
        # 429/403/etc:
        return f"@{username}", "N/A", f"Perfil encontrado (status {response.status_code})"
    except Exception:
        return f"@{username}", "N/A", "Erro ao acessar"

# --- FILTROS ---

def is_valid_store(name: str, tags: dict):
    """Filtra para manter apenas lojas de moda feminina e excluir grandes redes."""
    name_lower = name.lower()
    exclude = ['renner', 'c&a', 'zara', 'riachuelo', 'marisa', 'pernambucanas', 'havan', 'carrefour', 'extra', 'pão de açúcar', 'pao de acucar']
    if any(x in name_lower for x in exclude):
        return False

    keywords = ['feminina', 'boutique', 'concept', 'moda', 'fashion', 'estilo', 'look', 'vestuário', 'vestuario', 'multimarca']
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

# --- INTERFACE ---
st.title("📸 Verso Vivo - Buscador de Multimarcas")
st.subheader("Sua ferramenta para encontrar parceiros de moda feminina")

with st.sidebar:
    st.header("Configurações")
    city_input = st.text_input("Cidades (separadas por vírgula):", placeholder="Ex: São Paulo, Curitiba")
    limit = st.slider("Limite de lojas por cidade:", 10, 500, 100)
    st.info("O enriquecimento do Instagram pode demorar alguns segundos por loja para evitar bloqueios. Comece com 20–50 por cidade. 😉")

run = st.sidebar.button("🚀 Iniciar prospecção")

if run:
    if not city_input.strip():
        st.warning("Por favor, digite pelo menos uma cidade.")
        st.stop()

    # Split robusto: aceita vírgula, ponto-e-vírgula e quebra de linha
    cities = [c.strip() for c in re.split(r"[,;\n]+", city_input) if c.strip()]

    all_leads = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, city in enumerate(cities):
        status_text.text(f"Buscando lojas em {city}...")
        raw_elements = overpass_query(city)

        valid_stores = []
        for el in raw_elements:
            tags = el.get('tags', {})
            name = tags.get('name')
            if name and is_valid_store(name, tags):
                valid_stores.append((name, tags))

        valid_stores = valid_stores[:limit]

        for i, (name, tags) in enumerate(valid_stores):
            status_text.text(f"[{city}] Enriquecendo: {name} ({i+1}/{len(valid_stores)})")

            username = search_instagram_username(name, city)
            handle, followers, bio = get_instagram_data(username)

            endereco = f"{tags.get('addr:street', '')}, {tags.get('addr:housenumber', '')}".strip(', ').strip()
            if not endereco:
                endereco = "N/A"

            all_leads.append({
                "Loja": name,
                "Cidade": city,
                "Instagram": handle,
                "Seguidores": followers,
                "Bio": bio,
                "Telefone": tags.get('phone') or tags.get('contact:phone') or "N/A",
                "Endereço": endereco
            })

        progress_bar.progress((idx + 1) / max(1, len(cities)))

    status_text.text("✅ Busca concluída!")

    if all_leads:
        df = pd.DataFrame(all_leads)
        st.success(f"Encontradas {len(df)} lojas qualificadas!")

        # Métricas (chips)
        total = len(df)
        cidades_n = len(set(df["Cidade"]))
        com_insta = int((df["Instagram"] != "N/A").sum())
        st.markdown(f"""
        <div class="chip-row">
          <div class="chip"><span>Total</span> {total}</div>
          <div class="chip"><span>Cidades</span> {cidades_n}</div>
          <div class="chip"><span>Com Instagram</span> {com_insta}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ✨ Lojas Encontradas")

        # Cards estilo “post”
        for _, row in df.iterrows():
            loja = row["Loja"]
            cidade = row["Cidade"]
            instagram = row["Instagram"]
            seguidores = row["Seguidores"]
            bio = row["Bio"]
            telefone = row["Telefone"]
            endereco = row["Endereço"]

            av = initials(loja)
            insta_url = f"https://instagram.com/{instagram[1:]}" if isinstance(instagram, str) and instagram.startswith("@") else ""
            maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus((endereco if endereco!='N/A' else f'{loja} {cidade}'))}"

            actions = ""
            if insta_url:
                actions += f"<a class='pill pill-primary' href='{insta_url}' target='_blank'>Ver Instagram</a>"
            else:
                actions += f"<span class='pill pill-muted'>Sem Instagram</span>"
            actions += f"<a class='pill pill-muted' href='{maps_url}' target='_blank'>Ver no Maps</a>"

            # Copiar telefone (best-effort)
            if telefone and telefone != "N/A":
                safe_phone = str(telefone).replace("'", "\\'")
                actions += f"<a class='pill pill-muted' href='#' onclick=\"navigator.clipboard.writeText('{safe_phone}'); return false;\">Copiar telefone</a>"
            else:
                actions += f"<span class='pill pill-muted'>Telefone N/A</span>"

            st.markdown(f"""
            <div class="card">
              <div class="card-header">
                <div class="user">
                  <div class="avatar"><div class="avatar-inner">{av}</div></div>
                  <div style="min-width:0;">
                    <div class="title">{loja}</div>
                    <div class="subtitle">{cidade}</div>
                  </div>
                </div>
              </div>

              <div class="row"><span class="label">Instagram:</span> {f"<a href='{insta_url}' target='_blank'>{instagram}</a>" if insta_url else instagram}</div>
              <div class="row"><span class="label">Seguidores:</span> {seguidores}</div>
              <div class="row"><span class="label">Telefone:</span> {telefone}</div>
              <div class="row"><span class="label">Bio:</span> {bio}</div>
              <div class="row"><span class="label">Endereço:</span> {endereco}</div>

              <div class="actions">{actions}</div>
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
    else:
        st.info("Nenhuma loja encontrada com os filtros atuais. Tente outra cidade ou aumente o limite.")
