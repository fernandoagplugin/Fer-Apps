import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import os

# 1. Configurações da Página
st.set_page_config(page_title="Preço Teto Ações", layout="wide")

# --- LÓGICA DE PERSISTÊNCIA ---
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

# --- ESTILOS VISUAIS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;700&display=swap');
    .main-title { font-family: 'Roboto', sans-serif; font-size: 48px; font-weight: 700; text-align: center; margin-bottom: 0px; color: #1E1E1E; }
    .subtitle { font-family: 'Roboto', sans-serif; font-size: 18px; text-align: center; color: #666; margin-top: -5px; margin-bottom: 30px; font-style: italic; }
    .card { padding: 20px; border-radius: 15px; background-color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; height: 100%; border: 1px solid #eee; display: flex; flex-direction: column; align-items: center; }
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 15px; height: 80px; width: 100%; }
    .logo-img { max-width: 120px; max-height: 70px; object-fit: contain; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">Preço Teto Ações</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">por Fer</div>', unsafe_allow_html=True)

# 2. Configuração de Ativos
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 1.20, 'lpa_base': 0.65, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.55, 'lpa_base': 0.85, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.90, 'lpa_base': 1.40, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.45, 'lpa_base': 1.55, 'logo': f"{base_raw}Itausa.png"}
}

# 3. Busca de Dados Avançada
@st.cache_data(ttl=300)
def buscar_dados_completos(tickers):
    todos = tickers + ['BOVA11.SA', 'DIVO11.SA']
    dados = {}
    for t in todos:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="1y") # Reduzi para 1 ano para carregar mais rápido no update
            if hist.empty: continue
            
            # Tenta pegar o consenso de mercado (Forward EPS)
            info = tk.info
            lpa_mercado = info.get('forwardEps') or info.get('trailingEps')
            
            dados[t] = {
                'preco': hist['Close'].iloc[-1],
                'hist_norm': (hist['Close'] / hist['Close'].iloc[0]) * 100,
                'datas': hist.index,
                'lpa_consenso': lpa_mercado
            }
        except: continue
    return dados

dados_mercado = buscar_dados_completos(list(acoes_config.keys()))

# 4. Sidebar - Parâmetros
st.sidebar.header("⚙️ Parâmetros de Mercado")

# Slider de Yield (0.5 em 0.5)
if 'yield_alvo_slider' not in st.session_state:
    st.session_state.yield_alvo_slider = float(st.session_state.user_settings.get('yield_alvo', 0.06) * 100)

yield_valor = st.sidebar.slider("Yield Mínimo Desejado (%)", 6.0, 12.0, step=0.5, format="%.1f", key='yield_alvo_slider')
yield_alvo = yield_valor / 100

if yield_alvo != st.session_state.user_settings.get('yield_alvo'):
    st.session_state.user_settings['yield_alvo'] = yield_alvo
    salvar_configuracoes(st.session_state.user_settings)

# BOTÃO UPDATE (Limpa overrides manuais zerados e força busca de mercado)
if st.sidebar.button("🔄 Update"):
    # Limpa o cache do session_state para LPA/Payout se eles estiverem zerados ou quisermos resetar
    for ticker in acoes_config:
        if st.session_state.user_settings.get(f'lpa_{ticker}', 0) == 0:
            st.session_state.user_settings.pop(f'lpa_{ticker}', None)
            st.session_state.user_settings.pop(f'payout_{ticker}', None)
    
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📈 Projeções Futuras (2026)")

projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        # Prioridade: 1. Valor salvo no JSON | 2. Consenso Yahoo Finance | 3. Valor Base Manual
        consenso = dados_mercado.get(ticker, {}).get('lpa_consenso')
        default_lpa = st.session_state.user_settings.get(f'lpa_{ticker}')
        
        if default_lpa is None: # Se não houver nada salvo, usa o consenso ou a base
            default_lpa = consenso if consenso else conf['lpa_base']
            
        default_payout = st.session_state.user_settings.get(f'payout_{ticker}', conf['payout_base'])
        
        lpa_input = st.number_input(f"LPA ({ticker[:5]})", value=float(default_lpa), step=0.01, key=f"lpa_in_{ticker}")
        payout_input = st.slider(f"Payout % ({ticker[:5]})", 10, 200, int(default_payout*100), key=f"p_in_{ticker}") / 100
        
        # Salva apenas se o usuário de fato mexer no componente
        if lpa_input != default_lpa or (payout_input != default_payout):
            st.session_state.user_settings[f'lpa_{ticker}'] = lpa_input
            st.session_state.user_settings[f'payout_{ticker}'] = payout_input
            salvar_configuracoes(st.session_state.user_settings)
            
        projeções[ticker] = {'lpa': lpa_input, 'payout': payout_input}

# 5. Interface de Cards
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in dados_mercado:
        with cols[i]:
            d = dados_mercado[ticker]
            dpa_proj = projeções[ticker]['lpa'] * projeções[ticker]['payout']
            teto_proj = dpa_proj / yield_alvo if yield_alvo > 0 else 0
            margem = ((teto_proj - d['preco']) / teto_proj) * 100 if teto_proj > 0 else -100
            cor_m = "#28a745" if margem > 0 else "#dc3545"

            st.markdown(f"""
                <div class="card" style="border-top: 8px solid {conf['cor']};">
                    <div class="logo-container"><img src="{conf['logo']}" class="logo-img"></div>
                    <b style="font-size:1.3em;">{ticker[:5]}</b><br>
                    <small style="color:gray;">{conf['nome']}</small><hr style="width:100%">
                    <p style="margin:0; font-size:0.95em;">Preço Atual: <b>R$ {d['preco']:.2f}</b></p>
                    <p style="margin:0; font-size:0.95em;">Div. Projetado: <b>R$ {dpa_proj:.2f}</b></p>
                    <p style="margin:10px 0 5px 0; font-size:1.2em; color:{cor_m};">Teto: <b>R$ {teto_proj:.2f}</b></p>
                    <div style="background-color:{cor_m}; color:white; text-align:center; border-radius:8px; margin-top:auto; padding:8px; font-weight:bold; width:100%;">
                        Margem: {margem:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)

# 6. Gráfico (Simplificado para carregar mais rápido no Update)
st.markdown("---")
st.subheader("📊 Performance vs Índices")
ticker_sel = st.selectbox("Selecione para comparar:", list(acoes_config.keys()), format_func=lambda x: x[:5])
if ticker_sel in dados_mercado:
    d = dados_mercado[ticker_sel]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d['datas'], y=d['hist_norm'], name=f"{ticker_sel[:5]}", line=dict(color=acoes_config[ticker_sel]['cor'], width=3)))
    if 'BOVA11.SA' in dados_mercado:
        fig.add_trace(go.Scatter(x=dados_mercado['BOVA11.SA']['datas'], y=dados_mercado['BOVA11.SA']['hist_norm'], name='BOVA11', line=dict(color='#95a5a6', dash='dot')))
    fig.update_layout(template="plotly_white", height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
