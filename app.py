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
# CSS (IG-like + Desktop readable)
# =========================
st.markdown("""
<style>
html, body, [class*="st-"] {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
               "Helvetica Neue", Helvetica, Arial, "Segoe UI", Roboto, sans-serif !important;
  color: #0f1419;
  font-size: 16px;
}
.stApp { background: #fafafa; }

.main .block-container{
  max-width: 1400px;
  padding-top: 1.6rem;
  padding-bottom: 2.2rem;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

h1,h2,h3 { letter-spacing: -0.2px; }

.stTextInput>div>div>input {
  border-radius: 12px !important;
  border: 1px solid #dbdbdb !important;
  background: #fff !important;
  padding: 12px 12px !important;
  box-shadow: none !important;
  font-size: 16px !important;
}
.stSlider, .stSlider * { font-size: 15px !important; }

.stButton>button{
  width:100%;
  border-radius: 14px !important;
  border: 0 !important;
  background: linear-gradient(45deg, #f02d71, #ff6600) !important;
  color: #fff !important;
  font-weight: 800 !important;
  height: 52px !important;
  font-size: 16px !important;
  box-shadow: 0 6px 16px rgba(240, 45, 113, 0.18) !important;
  transition: transform .15s ease, filter .15s ease;
}
.stButton>button:hover{ transform: translateY(-1px); filter: brightness(0.98); }

.card{
  background:#fff;
  border:1px solid #e7e7e7;
  border-radius: 18px;
  padding: 16px 16px 14px 16px;
  margin-bottom: 14px;
  box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}
.card h4{
  margin: 0 0 6px 0;
  font-size: 17px;
  font-weight: 900;
}
.muted{ color:#6e6e6e; font-size: 13px; line-height:1.35; }
.row{
  display:flex; flex-wrap:wrap; gap:10px; margin-top:10px; align-items:center;
}
.pill{
  display:inline-flex; align-items:center; gap:8px;
  border-radius: 999px;
  padding: 8px 12px;
  background:#f2f2f2;
  border:1px solid #f2f2f2;
  font-size: 13px;
  font-weight: 800;
  color:#111;
}
a { color:#00376b !important; text-decoration:none; font-weight: 800; }
a:hover { text-decoration: underline; }

.metric-wrap{
  display:flex; flex-wrap:wrap; gap:10px; margin: 8px 0 14px 0;
}
.metric{
  border-radius: 999px;
  padding: 10px 14px;
  background:#fff;
  border:1px solid #e7e7e7;
  font-weight: 900;
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}
</style>
""", unsafe_allow_html=True)

# =========================
# FUNÇÕES (BUSCA)
# =========================

def overpass_query(city_name: str):
    """Busca POIs de lojas no Overpass API."""
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
        r = requests.get(overpass_url, params={"data": query}, timeout=90)
        if r.status_code == 200:
            return r.json().get("elements", [])
        return []
    except Exception:
        return []

FOOD_EXCLUDE = [
    "bar", "restaurante", "restaurant", "lanchonete", "lanches", "hamburguer", "hamburger",
    "café", "cafe", "cafeteria", "pizza", "pizzaria", "sushi", "japones", "japonês",
    "açaí", "acai", "sorveteria", "padaria", "bakery", "churrasco", "steakhouse",
    "cervejaria", "brew", "pub", "drinks", "bistrô", "bistro", "food", "bebidas", "alimentos",
    "a&b", "comida", "cozinha", "mercado", "supermercado"
]

BIG_RETAIL_EXCLUDE = [
    "renner","c&a","zara","riachuelo","marisa","pernambucanas","havan","carrefour","extra","pão de açúcar","pao de acucar"
]

FEM_KEYWORDS = ["feminina","boutique","concept","moda","fashion","estilo","look","vestuário","vestuario","multimarca"]

def is_valid_store(name: str, tags: dict) -> bool:
    """Mantém lojas de moda e elimina grandes redes + alimentação/bebidas."""
    name_lower = (name or "").lower()

    if any(x in name_lower for x in BIG_RETAIL_EXCLUDE):
        return False

    # Eliminar claramente alimentação/bebidas pelo nome
    if any(x in name_lower for x in FOOD_EXCLUDE):
        return False

    # Eliminar se OSM indicar amenity/cuisine/food
    if tags.get("amenity") in ["restaurant", "cafe", "bar", "pub", "fast_food"]:
        return False
    if "cuisine" in tags or "brewery" in tags or "bar" in tags:
        # tags variadas que costumam aparecer em A&B
        return False

    # Preferência por palavras-chave de moda feminina/boutique
    if any(k in name_lower for k in FEM_KEYWORDS):
        return True

    # Fallback: se for shop clothes/boutique, mantém
    shop_type = tags.get("shop", "")
    if shop_type in ["boutique", "clothes", "apparel", "fashion", "clothing"]:
        return True

    return False

def _google_search_html(q: str) -> str | None:
    url = f"https://www.google.com/search?q={quote_plus(q)}&hl=pt-BR&gl=BR"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    try:
        time.sleep(random.uniform(1.0, 2.0))
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            return r.text
        return None
    except Exception:
        return None

def search_instagram_username(store_name: str, city: str) -> str | None:
    """
    Estratégia manual automatizada:
    1) '{Loja} Instagram' e tentar escolher resultado que menciona a cidade.
    2) fallback: '{Loja} {Cidade} Instagram'
    Retorna apenas username (sem followers/bio).
    """
    def pick_username_from_html(html: str, city_hint: str | None):
        soup = BeautifulSoup(html, "lxml")
        candidates = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "instagram.com/" not in href:
                continue
            m = re.search(r"instagram\.com/([^/?&]+)", href)
            if not m:
                continue
            username = m.group(1)
            if username in ["reels","stories","explore","p","tags"]:
                continue

            # Score pelo contexto (texto do bloco)
            score = 0
            block = a.find_parent("div")
            if block:
                txt = block.get_text(" ", strip=True).lower()
                if city_hint and city_hint.lower() in txt:
                    score += 3
                # se menciona instagram + loja (não garantido)
                if "instagram" in txt:
                    score += 1
            # Prioriza perfis (não /p/, /reels/ etc já filtramos)
            candidates.append((score, username))

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    q1 = f"{store_name} instagram"
    html1 = _google_search_html(q1)
    if html1:
        u = pick_username_from_html(html1, city)
        if u:
            return u

    q2 = f"{store_name} {city} instagram"
    html2 = _google_search_html(q2)
    if html2:
        u = pick_username_from_html(html2, city)
        if u:
            return u

    return None

def build_address(tags: dict) -> str:
    street = tags.get("addr:street", "")
    num = tags.get("addr:housenumber", "")
    addr = f"{street}, {num}".strip(", ").strip()
    return addr if addr else "N/A"

# =========================
# UI
# =========================
st.image("LOGOOFICIALBRANCA.png", width=220) if True else None
st.subheader("Sua ferramenta para encontrar lojistas multimarcas (estética IG)")

with st.sidebar:
    st.header("Configurações")
    city_input = st.text_input("Cidades (separadas por vírgula):", placeholder="Ex: Florianópolis, Curitiba")
    limit = st.slider("Limite de lojas por cidade:", 10, 500, 100)
    st.info("Dica: comece com 20–50 por cidade para reduzir bloqueios do Google.")
    start = st.button("🚀 INICIAR PROSPECÇÃO")

if start:
    if not city_input.strip():
        st.warning("Por favor, digite pelo menos uma cidade.")
        st.stop()

    # split robusto
    cities = [c.strip() for c in re.split(r",|\n|;", city_input) if c.strip()]
    all_leads = []

    progress = st.progress(0)
    status = st.empty()

    for idx, city in enumerate(cities):
        status.markdown(f"**Buscando lojas em {city}...**")
        raw = overpass_query(city)

        valid = []
        for el in raw:
            tags = el.get("tags", {})
            name = tags.get("name")
            if name and is_valid_store(name, tags):
                valid.append((name, tags))

        valid = valid[:limit]

        for i, (name, tags) in enumerate(valid):
            status.markdown(f"**[{city}]** Enriquecendo Instagram: **{name}** ({i+1}/{len(valid)})")
            username = search_instagram_username(name, city)
            handle = f"@{username}" if username else "N/A"

            all_leads.append({
                "Loja": name,
                "Cidade": city,
                "Instagram": handle,
                "Telefone": tags.get("phone") or tags.get("contact:phone") or "N/A",
                "Endereço": build_address(tags)
            })

        progress.progress((idx + 1) / max(1, len(cities)))

    status.markdown("✅ **Prospecção concluída!**")

    if not all_leads:
        st.info("Nenhuma loja encontrada com os filtros atuais. Tente outra cidade.")
        st.stop()

    df = pd.DataFrame(all_leads)

    st.markdown("### ✨ Lojas Encontradas")
    st.markdown(f"""
    <div class="metric-wrap">
      <div class="metric">Total: {len(df)}</div>
      <div class="metric">Cidades: {len(set(df["Cidade"]))}</div>
      <div class="metric">Com Instagram: {int((df["Instagram"]!="N/A").sum())}</div>
    </div>
    """, unsafe_allow_html=True)

    for _, row in df.iterrows():
        insta = row["Instagram"]
        insta_link = f"https://instagram.com/{insta[1:]}" if isinstance(insta, str) and insta.startswith("@") else None

        st.markdown(f"""
        <div class="card">
          <h4>{row["Loja"]} <span class="muted">· {row["Cidade"]}</span></h4>
          <div class="row">
            <span class="pill">📸 Instagram: {"<a href='"+insta_link+"' target='_blank'>"+insta+"</a>" if insta_link else insta}</span>
            <span class="pill">📞 {row["Telefone"]}</span>
          </div>
          <div class="muted" style="margin-top:10px;"><b>Endereço:</b> {row["Endereço"]}</div>
        </div>
        """, unsafe_allow_html=True)

    # Download Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")

    st.download_button(
        label="📥 Baixar Planilha Excel (.xlsx)",
        data=output.getvalue(),
        file_name="leads_verso_vivo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
