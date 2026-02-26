import streamlit as st
import pandas as pd
import requests
import re
import time
import io

# --- CONFIGURAÇÕES ---
st.set_page_config(
    page_title="Verso Vivo ELITE - Prospecção Feminina",
    page_icon="👗",
    layout="wide"
)

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .main { background-color: #fff5f8; }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3.5em;
        background-color: #d81b60;
        color: white;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stProgress > div > div > div > div { background-color: #d81b60; }
    h1, h2, h3 { color: #880e4f; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE BUSCA ---

def normalize_instagram(value: str) -> str:
    if not value: return ""
    v = value.strip().split("?")[0].split("#")[0]
    if v.startswith("@"): return v
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", v, flags=re.IGNORECASE)
    if m:
        handle = m.group(1).strip("/")
        if handle.lower() not in {"p", "reel", "reels", "tv", "stories", "explore"}:
            return f"@{handle}"
    if re.fullmatch(r"[A-Za-z0-9._]{2,30}", v): return f"@{v}"
    return v

def overpass_query_ultra_refined(city_name):
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    q = f"""
    [out:json][timeout:180];
    area["name"="{city_name}"]["admin_level"~"4|8"]->.a;
    (
      nwr(area.a)["shop"="clothes"];
      nwr(area.a)["shop"="boutique"];
      nwr(area.a)["shop"="fashion"];
    );
    out center tags;
    """
    try:
        r = requests.post(OVERPASS_URL, data=q.encode("utf-8"), timeout=200)
        return r.json().get("elements", []) or []
    except:
        return []

def filter_female_multibrand(elements, city):
    qualified = []
    seen = set()
    
    termos_alvo = ["feminina", "mulher", "boutique", "multimarcas", "concept", "moda", "store", "closet", "estilo", "look", "chic", "fashion", "curadoria", "trend", "luxo", "premium"]
    termos_excluir = ["car", "auto", "oficina", "moto", "veiculos", "masculino", "homem", "kids", "infantil", "bebe", "baby", "renner", "cea", "c&a", "riachuelo", "marisa", "zara", "pernambucanas", "havan", "magazine", "casas bahia"]

    for el in elements:
        tags = el.get("tags", {}) or {}
        nome = (tags.get("name") or "").strip()
        if not nome: continue
        
        nome_l = nome.lower()
        if any(ex in nome_l for ex in termos_excluir): continue
        if not any(t in nome_l or (tags.get("description") or "").lower() in t for t in termos_alvo): continue
            
        if nome_l in seen: continue
        seen.add(nome_l)
        
        tel = (tags.get("phone") or tags.get("contact:phone") or "").strip()
        insta = (tags.get("contact:instagram") or tags.get("instagram") or "").strip()
        site = (tags.get("website") or tags.get("contact:website") or "").strip()
        
        qualified.append({
            "Loja": nome,
            "Cidade": city,
            "Instagram": normalize_instagram(insta),
            "WhatsApp/Tel": tel,
            "Site": site,
            "Endereço": f"{tags.get('addr:street', '')}, {tags.get('addr:housenumber', '')}".strip(", ")
        })
    return qualified

# --- INTERFACE ---

st.title("👗 Verso Vivo ELITE")
st.subheader("O buscador definitivo de Lojistas Multimarcas Femininas")

with st.sidebar:
    st.header("📍 Cidades para Prospectar")
    cidades_input = st.text_area("Digite as cidades (uma por linha):", value="Florianópolis\nCuritiba\nSão Paulo\nPorto Alegre", height=200)
    cidades = [c.strip() for c in cidades_input.split("\n") if c.strip()]
    st.info("O algoritmo bloqueia automaticamente lojas de carros e grandes redes.")

if st.button("🚀 GERAR LISTA DE LEADS"):
    if not cidades:
        st.error("Insira ao menos uma cidade.")
    else:
        all_results = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        for idx, cidade in enumerate(cidades):
            status.info(f"🔎 Mapeando lojas em **{cidade}**...")
            raw_elements = overpass_query_ultra_refined(cidade)
            leads = filter_female_multibrand(raw_elements, cidade)
            all_results.extend(leads)
            progress_bar.progress((idx + 1) / len(cidades))
            time.sleep(1)

        status.success(f"✅ Encontramos **{len(all_results)}** lojas qualificadas.")
        if all_results:
            df = pd.DataFrame(all_results)
            st.dataframe(df, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Leads_Elite')
            st.download_button(label="📥 BAIXAR PLANILHA (.xlsx)", data=output.getvalue(), file_name=f"leads_elite_{time.strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
