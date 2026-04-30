import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações e CSS (Mantidos para preservar o visual moderno)
st.set_page_config(page_title="EquityDash Ultra v5", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .main-header { 
        background: linear-gradient(90deg, #0f172a 0%, #1e3a8a 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;
    }
    .card-equity {
        background: white; padding: 20px; border-radius: 20px; border: 1px solid #eef2f6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between;
    }
    .label-text { color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>EquityDash Ultra v5</h1><p>Valuation Projetivo com CAGR e Crescimento de Lucros</p></div>', unsafe_allow_html=True)

# 2. Configuração de Ativos
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'cor': '#3bb54a', 'payout': 1.0, 'cagr_default': 0.05, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'cor': '#2d3e50', 'payout': 0.5, 'cagr_default': 0.08, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'cor': '#005ca9', 'payout': 0.9, 'cagr_default': 0.12, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'cor': '#ec7000', 'payout': 0.4, 'cagr_default': 0.10, 'logo': f"{base_raw}Itausa.png"}
}

# 3. Sidebar - Inteligência Projetiva
st.sidebar.title("🚀 Projeção de Crescimento")
tempo_proj = st.sidebar.slider("Horizonte de Projeção (Anos)", 1, 10, 5)
yield_valor = st.sidebar.select_slider("Yield Alvo %", options=[6.0, 8.0, 10.0, 12.0], value=6.0)
yield_alvo = yield_valor / 100

st.sidebar.markdown("---")
projeções_usuario = {}
for ticker in acoes_config.keys():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        cagr = st.number_input(f"CAGR Lucro % ({ticker[:5]})", value=acoes_config[ticker]['cagr_default']*100, step=0.5) / 100
        payout = st.slider(f"Payout % ({ticker[:5]})", 0, 100, int(acoes_config[ticker]['payout']*100)) / 100
        projeções_usuario[ticker] = {'cagr': cagr, 'payout': payout}

# 4. Busca de Dados
@st.cache_data(ttl=600)
def fetch_data(tickers):
    data = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            data[t] = {
                'price': tk.history(period="1d")['Close'].iloc[-1],
                'lpa_atual': tk.info.get('forwardEps') or tk.info.get('trailingEps') or 1.0
            }
        except: continue
    return data

market_data = fetch_data(list(acoes_config.keys()))

# 5. Interface de Cards com Lógica Projetiva
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in market_data:
        d = market_data[ticker]
        proj = projeções_usuario[ticker]
        
        # CÁLCULOS PROJETIVOS
        lpa_futuro = d['lpa_atual'] * ((1 + proj['cagr']) ** tempo_proj)
        dpa_futuro = lpa_futuro * proj['payout']
        teto_projetado = dpa_futuro / yield_alvo
        
        margem = ((teto_projetado - d['price']) / teto_projetado) * 100

        with cols[i]:
            cor_margem = "#15803d" if margem > 0 else "#92400e"
            st.markdown(f"""
                <div class="card-equity" style="border-top: 5px solid {conf['cor']};">
                    <div>
                        <img src="{conf['logo']}" style="height:40px;">
                        <div class="label-text" style="margin-top:10px;">{ticker}</div>
                        <div style="font-size:20px; font-weight:700;">R$ {d['price']:.2f}</div>
                    </div>
                    <div style="background:#f8fafc; padding:10px; border-radius:10px; margin:10px 0;">
                        <div style="display:flex; justify-content:space-between;"><span class="label-text">LPA Projetado</span><b>R$ {lpa_futuro:.2f}</b></div>
                        <div style="display:flex; justify-content:space-between;"><span class="label-text">Div. Projetado</span><b>R$ {dpa_futuro:.2f}</b></div>
                    </div>
                    <div>
                        <div class="label-text">Preço Teto ({tempo_proj} anos)</div>
                        <div style="font-size:18px; font-weight:700; color:{cor_margem};">R$ {teto_projetado:.2f}</div>
                        <div style="font-size:12px; color:{cor_margem}; font-weight:bold;">Margem: {margem:.1f}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
