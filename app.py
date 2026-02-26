import streamlit as st
import pandas as pd
import requests
import re
import time
import random
from bs4 import BeautifulSoup
from io import BytesIO

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Verso Sourcing Pro 3.0", page_icon="👗", layout="wide")

# --- CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; border: none; background-color: #d81b60; color: white; font-weight: bold; height: 3em; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #ad1457; transform: scale(1.02); }
    .card { background-color: white; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #d81b60; }
    .stProgress > div > div > div > div { background-color: #d81b60; }
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
        response = requests.get(overpass_url, params={'data': query}, timeout=90)
        if response.status_code == 200:
            return response.json().get('elements', [])
        return []
    except Exception as e:
        return []

def search_instagram_username(store_name, city):
    """Busca o username do Instagram no Google via raspagem leve."""
    query = f"{store_name} {city} instagram"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        # Pequeno delay para evitar bloqueios rápidos
        time.sleep(random.uniform(1, 2))
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'instagram.com/' in href:
                    # Extrair o username
                    match = re.search(r'instagram\.com/([^/?&]+)', href)
                    if match:
                        username = match.group(1)
                        if username not in ['reels', 'stories', 'explore', 'p', 'tags']:
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
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc:
                content = meta_desc.get("content", "")
                # Exemplo: "1,234 Followers, 567 Following, 89 Posts..."
                followers_match = re.search(r'([\d.,KM]+)\s*Followers', content)
                followers = followers_match.group(1) if followers_match else "N/A"
                return f"@{username}", followers, content
        return f"@{username}", "N/A", "Perfil encontrado"
    except:
        return f"@{username}", "N/A", "Erro ao acessar"

# --- FILTROS ---

def is_valid_store(name, tags):
    """Filtra para manter apenas lojas de moda feminina e excluir grandes redes."""
    name_lower = name.lower()
    exclude = ['renner', 'c&a', 'zara', 'riachuelo', 'marisa', 'pernambucanas', 'havan', 'carrefour', 'extra', 'pão de açúcar']
    if any(x in name_lower for x in exclude):
        return False
    
    # Palavras-chave de moda feminina/boutique
    keywords = ['feminina', 'boutique', 'concept', 'moda', 'fashion', 'estilo', 'look', 'vestuário', 'multimarca']
    if any(k in name_lower for k in keywords):
        return True
    
    # Se não tiver palavra-chave, mas for shop=clothes/boutique, mantemos por precaução
    shop_type = tags.get('shop', '')
    if shop_type in ['boutique', 'clothes']:
        return True
        
    return False

# --- INTERFACE ---
st.title("👗 Verso Sourcing Pro 3.0")
st.subheader("Prospecção Inteligente de Lojas Multimarcas")

with st.sidebar:
    st.header("Configurações")
    city_input = st.text_input("Cidades (separadas por vírgula):", placeholder="Ex: São Paulo, Curitiba")
    limit = st.slider("Limite de lojas por cidade (para teste):", 5, 500, 250)
    st.info("O enriquecimento do Instagram pode demorar alguns segundos por loja para evitar bloqueios.")

if st.sidebar.button("🚀 INICIAR PROSPECÇÃO"):
    if city_input:
        cities = [c.strip() for c in city_input.split(',') if c.strip()]
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
            
            # Limitar para não demorar demais no teste/demonstração
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
                    "Telefone": tags.get('phone') or tags.get('contact:phone') or "N/A",
                    "Endereço": f"{tags.get('addr:street', '')}, {tags.get('addr:housenumber', '')}".strip(', ') or "N/A"
                })
                
            progress_bar.progress((idx + 1) / len(cities))
            
        status_text.text("✅ Prospecção concluída!")
        
        if all_leads:
            df = pd.DataFrame(all_leads)
            st.success(f"Encontradas {len(df)} lojas qualificadas!")
            
            # Métricas
            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Leads", len(df))
            m2.metric("Cidades", len(cities))
            m3.metric("Com Instagram", len(df[df['Instagram'] != 'N/A']))

            # Tabela de resultados
            st.dataframe(df)
            
            # Download Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Leads')
            
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=output.getvalue(),
                file_name=f"leads_verso_vivo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("Por favor, digite pelo menos uma cidade.")
