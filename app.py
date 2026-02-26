import streamlit as st
import pandas as pd
import requests
import re
import time
import random
from bs4 import BeautifulSoup
from io import BytesIO

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Verso Vivo - Buscador Multimarcas", page_icon="📸", layout="wide")

# --- CSS CUSTOMIZADO (Instagram-like) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
        color: #262626; /* Instagram-like dark grey */
    }
    .main { 
        background-color: #fafafa; /* Light grey background */
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px; /* More rounded corners */
        border: none;
        background: linear-gradient(45deg, #f02d71, #ff6600); /* Instagram gradient */
        color: white;
        font-weight: 600;
        height: 3.5em; /* Slightly taller button */
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(240, 45, 113, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(240, 45, 113, 0.4);
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 15px; /* More rounded cards */
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08); /* Softer shadow */
        border-left: 6px solid #f02d71; /* Accent color */
        transition: all 0.3s ease;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        border-left-color: #ff6600; /* Change accent on hover */
    }
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
    }
    .stProgress > div > div > div > div {
        background-color: #f02d71; /* Instagram-like progress bar */
    }
    h1, h2, h3, h4, h5, h6 {
        color: #262626;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #dcdcdc;
        padding: 10px;
    }
    .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1px solid #dcdcdc;
    }
    .stMarkdown a {
        color: #00376b; /* Instagram link blue */
        text-decoration: none;
    }
    .stMarkdown a:hover {
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BUSCA ---

def overpass_query(city_name):
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
        response = requests.get(overpass_url, params={\'data\': query}, timeout=90)
        if response.status_code == 200:
            return response.json().get(\'elements\', [])
        return []
    except Exception as e:
        return []

def search_instagram_username(store_name, city):
    """Busca o username do Instagram no Google via raspagem leve."""
    query = f"{store_name} {city} instagram"
    url = f"https://www.google.com/search?q={query.replace(\' \', \'+\')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        # Pequeno delay para evitar bloqueios rápidos
        time.sleep(random.uniform(1, 2))
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, \'html.parser\')
            for a in soup.find_all(\'a\', href=True):
                href = a[\'href\']
                if \'instagram.com/\' in href:
                    # Extrair o username
                    match = re.search(r\'instagram\\.com/([^/?&]+)\\' , href)
                    if match:
                        username = match.group(1)
                        if username not in [\'reels\', \'stories\', \'explore\', \'p\', \'tags\']:
                            return username
        return None
    except:
        return None

def get_instagram_data(username):
    """Extrai seguidores e bio do perfil público do Instagram."""
    if not username:
        return "N/A", "N/A", "N/A"
    
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, \'html.parser\')
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc:
                content = meta_desc.get("content", "")
                # Exemplo: "1,234 Followers, 567 Following, 89 Posts..."
                followers_match = re.search(r\'([\\d.,KM]+)\\s*Followers\', content)
                followers = followers_match.group(1) if followers_match else "N/A"
                return f"@{username}", followers, content
        return f"@{username}", "N/A", "Perfil encontrado"
    except:
        return f"@{username}", "N/A", "Erro ao acessar"

# --- FILTROS ---

def is_valid_store(name, tags):
    """Filtra para manter apenas lojas de moda feminina e excluir grandes redes."""
    name_lower = name.lower()
    exclude = [\'renner\', \'c&a\', \'zara\', \'riachuelo\', \'marisa\', \'pernambucanas\', \'havan\', \'carrefour\', \'extra\', \'pão de açúcar\']
    if any(x in name_lower for x in exclude):
        return False
    
    # Palavras-chave de moda feminina/boutique
    keywords = [\'feminina\', \'boutique\', \'concept\', \'moda\', \'fashion\', \'estilo\', \'look\', \'vestuário\', \'multimarca\']
    if any(k in name_lower for k in keywords):
        return True
    
    # Se não tiver palavra-chave, mas for shop=clothes/boutique, mantemos por precaução
    shop_type = tags.get(\'shop\', \'\')
    if shop_type in [\'boutique\', \'clothes\']:
        return True
        
    return False

# --- INTERFACE ---
st.title("📸 Verso Sourcing Pro")
st.subheader("Sua ferramenta para encontrar parceiros de moda feminina")

with st.sidebar:
    st.header("Configurações")
    city_input = st.text_input("Cidades (separadas por vírgula):", placeholder="Ex: São Paulo, Curitiba")
    limit = st.slider("Limite de lojas por cidade:", 10, 500, 100) # Ajustado para 100 como padrão, max 500
    st.info("O enriquecimento do Instagram pode demorar alguns segundos por loja para evitar bloqueios. Seja paciente! 😉")

if st.sidebar.button("🚀 INICIAR PROSPECÇÃO"):
    if city_input:
        cities = [c.strip() for c in city_input.split(\' , \') if c.strip()]
        all_leads = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, city in enumerate(cities):
            status_text.text(f"Buscando lojas em {city}...")
            raw_elements = overpass_query(city)
            
            valid_stores = []
            for el in raw_elements:
                tags = el.get(\'tags\', {})
                name = tags.get(\'name\')
                if name and is_valid_store(name, tags):
                    valid_stores.append((name, tags))
            
            valid_stores = valid_stores[:limit]
            
            for i, (name, tags) in enumerate(valid_stores):
                status_text.text(f"[{city}] Enriquecendo: {name} ({i+1}/{len(valid_stores)})")
                
                username = search_instagram_username(name, city)
                handle, followers, bio = get_instagram_data(username)
                
                all_leads.append({
                    "Loja": name,
                    "Cidade": city,
                    "Instagram": handle,
                    "Seguidores": followers,
                    "Bio": bio,
                    "Telefone": tags.get(\'phone\') or tags.get(\'contact:phone\') or "N/A",
                    "Endereço": f"{tags.get(\'addr:street\', \'\')}, {tags.get(\'addr:housenumber\', \'\')}".strip(\' , \') or "N/A"
                })
                
            progress_bar.progress((idx + 1) / len(cities))
            
        status_text.text("✅ Prospecção concluída!")
        
        if all_leads:
            df = pd.DataFrame(all_leads)
            st.success(f"Encontradas {len(df)} lojas qualificadas!")
            
            # Métricas com ícones
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='metric-card'><h3>Total de Leads</h3><p>{len(df)}</p></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-card'><h3>Cidades Buscadas</h3><p>{len(cities)}</p></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-card'><h3>Com Instagram</h3><p>{len(df[df['Instagram'] != 'N/A'])}</p></div>", unsafe_allow_html=True)

            st.markdown("--- ")
            st.markdown("### ✨ Lojas Encontradas")
            
            # Exibição em Cards com mais estilo
            for i, row in df.iterrows():
                st.markdown(f"""
                <div class="card">
                    <h4>{row['Loja']} - {row['Cidade']}</h4>
                    <p><b>Instagram:</b> <a href="https://instagram.com/{row['Instagram'][1:]}" target="_blank">{row['Instagram']}</a></p>
                    <p><b>Seguidores:</b> {row['Seguidores']}</p>
                    <p><b>Bio:</b> {row['Bio']}</p>
                    <p><b>Telefone:</b> {row['Telefone']}</p>
                    <p><b>Endereço:</b> {row['Endereço']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Download Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine=\'openpyxl\') as writer:
                df.to_excel(writer, index=False, sheet_name=\'Leads\')
            
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=output.getvalue(),
                file_name=f"leads_verso_vivo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("Por favor, digite pelo menos uma cidade.")
