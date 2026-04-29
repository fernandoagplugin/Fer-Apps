import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import os

# 1. Configurações da Página
st.set_page_config(page_title="Preço Teto Ações", layout="wide")

# --- PERSISTÊNCIA ---
DB_FILE = "settings_cache.json"

def carregar_configuracoes():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def salvar_configuracoes(config_dict):
    with open(DB_FILE, "w") as f:
        json.dump(config_dict, f)

if 'user_settings' not in st.session_state:
    st.session_state.user_settings = carregar_configuracoes()

# --- ESTILOS ---
st.markdown("""
    <style>
    .main-title { font-size: 42px; font-weight: 700; text-align: center; color: #1E1E1E; margin-bottom: 30px; }
    .card { padding: 20px; border-radius: 15px; background-color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; height: 100%; border: 1px solid #eee; }
    .logo-img { max-width: 100px; max-height: 60px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">Preço Teto Ações</div>', unsafe_allow_html=True)

# 2. Configuração Estática
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 1.0, 'lpa_base': 0.65, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.5, 'lpa_base': 0.85, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.9, 'lpa_base': 1.40, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.4, 'lpa_base': 1.55, 'logo': f"{base_raw}Itausa.png"}
}

# 3. Busca de Dados
@st.cache_data(ttl=300)
def buscar_dados(tickers):
    dados = {}
    for t in tickers + ['BOVA11.SA', 'DIVO11.SA']:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            # Busca consenso de mercado
            lpa_m = info.get('forwardEps') or info.get('trailingEps')
            
            hist = tk.history(period="1y")
            if not hist.empty:
                dados[t] = {
                    'preco': hist['Close'].iloc[-1],
                    'lpa_consenso': lpa_m,
                    'datas': hist.index,
                    'hist': (hist['Close'] / hist['Close'].iloc[0]) * 100
                }
        except: continue
    return dados

dados_mercado = buscar_dados(list(acoes_config.keys()))

# 4. Sidebar
st.sidebar.header("⚙️ Parâmetros")

# Yield Alvo
if 'yield_alvo_slider' not in st.session_state:
    st.session_state.yield_alvo_slider = float(st.session_state.user_settings.get('yield_alvo', 0.06) * 100)

y_val = st.sidebar.slider("Yield Mínimo (%)", 6.0, 12.0, step=0.5, key='yield_alvo_slider')
yield_alvo = y_val / 100

# Salva yield se mudar
if yield_alvo != st.session_state.user_settings.get('yield_alvo'):
    st.session_state.user_settings['yield_alvo'] = yield_alvo
    salvar_configuracoes(st.session_state.user_settings)

# O BOTÃO UPDATE: Limpa o cache e as edições manuais para forçar o "deslizamento" dos valores de mercado
if st.sidebar.button("Update"):
    # Limpa as chaves de LPA e Payout do session_state e do arquivo para resetar ao consenso
    chaves_para_remover = []
    for ticker in acoes_config:
        chaves_para_remover.extend([f'lpa_{ticker}', f'payout_{ticker}'])
    
    for chave in chaves_para_remover:
        st.session_state.user_settings.pop(chave, None)
    
    salvar_configuracoes(st.session_state.user_settings)
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📈 Projeções 2026")

projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        
        # LÓGICA DE SINCRONIZAÇÃO:
        # Se existir no cache (editado pelo usuário), usa. 
        # Se NÃO existir (pós-Update), busca Consenso. 
        # Se Consenso falhar, usa o Padrão do código.
        
        v_lpa_original = st.session_state.user_settings.get(f'lpa_{ticker}')
        if v_lpa_original is None:
            cons = dados_mercado.get(ticker, {}).get('lpa_consenso')
            v_lpa_original = cons if cons and cons > 0 else conf['lpa_base']
        
        v_payout_original = st.session_state.user_settings.get(f'payout_{ticker}', conf['payout_base'])
        
        # Renderiza os inputs com os valores calculados acima
        lpa_input = st.number_input(f"LPA {ticker[:5]}", value=float(v_lpa_original), step=0.01, key=f"n_{ticker}")
        payout_input = st.slider(f"Payout % {ticker[:5]}", 10, 200, int(v_payout_original * 100), key=f"s_{ticker}") / 100
        
        # Se o usuário interagir e mudar o valor, salvamos no cache
        if lpa_input != v_lpa_original or payout_input != v_payout_original:
            st.session_state.user_settings[f'lpa_{ticker}'] = lpa_input
            st.session_state.user_settings[f'payout_{ticker}'] = payout_input
            salvar_configuracoes(st.session_state.user_settings)
            
        projeções[ticker] = {'lpa': lpa_input, 'payout': payout_input}

# 5. Cards (Calculados com base nos inputs acima)
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in dados_mercado:
        d = dados_mercado[ticker]
        proj = projeções[ticker]
        
        dpa = proj['lpa'] * proj['payout']
        teto = dpa / yield_alvo if yield_alvo > 0 else 0
        margem = ((teto - d['preco']) / teto) * 100 if teto > 0 else -100
        cor = "#28a745" if margem > 0 else "#dc3545"
        
        with cols[i]:
            st.markdown(f"""
                <div class="card" style="border-top: 5px solid {conf['cor']};">
                    <img src="{conf['logo']}" class="logo-img"><br>
                    <b>{ticker[:5]}</b><br>
                    <p style="margin:5px 0; font-size:14px;">Preço: R$ {d['preco']:.2f}</p>
                    <p style="margin:5px 0; font-size:14px;">Div: R$ {dpa:.2f}</p>
                    <p style="font-size:18px; color:{cor}; margin:10px 0;"><b>Teto: R$ {teto:.2f}</b></p>
                    <div style="background:{cor}; color:white; padding:5px; border-radius:5px;">{margem:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
