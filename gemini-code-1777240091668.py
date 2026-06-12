import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações da Página
st.set_page_config(page_title="EquityDash Ultra v7.0", layout="wide")

# --- CSS Profissional ---
st.markdown("""
    <style>
    .card-equity { background: white; padding: 20px; border-radius: 20px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; height: 100%; display: flex; flex-direction: column; }
    .badge-buy { background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    .badge-wait { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração de Ativos
acoes_config = {
    'AXIA3.SA': {'tipo': 'Acao', 'payout': 1.0, 'lpa': 3.50, 'vpa': 52.10, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png"},
    'CPLE3.SA': {'tipo': 'Acao', 'payout': 0.5, 'lpa': 0.85, 'vpa': 10.40, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png"},
    'CXSE3.SA': {'tipo': 'Acao', 'payout': 0.9, 'lpa': 1.40, 'vpa': 4.10, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Caixa.png"},
    'ITSA4.SA': {'tipo': 'Acao', 'payout': 0.4, 'lpa': 1.55, 'vpa': 8.90, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Itausa.png"},
    'EQIX': {'tipo': 'REIT', 'dpa': 17.04, 'ffo': 34.80, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/02b13adcb14ea6c1530085e2af5a531738423aec/Equinix_Logo.png"}
}

# 3. Sidebar com Override de Preço
st.sidebar.title("⚙️ Ajustes de Mercado")
precos_manuais = {}
for ticker in acoes_config.keys():
    precos_manuais[ticker] = st.sidebar.number_input(f"Preço {ticker} (0 p/ auto)", value=0.0, step=1.0)

yield_alvo = st.sidebar.select_slider("Yield Alvo BR (%)", options=[6.0, 7.0, 8.0, 9.0, 10.0], value=6.0) / 100

# 4. Engine de Dados
@st.cache_data(ttl=600)
def get_data():
    results = {}
    for t in acoes_config.keys():
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="1y")
            results[t] = hist['Close'].iloc[-1] if not hist.empty else 0
        except: results[t] = 0
    return results

market_prices = get_data()

# 5. Dashboard
cols = st.columns(4)
idx = 0
for ticker, conf in acoes_config.items():
    # Prioriza o preço manual, se for 0, usa o do Yahoo
    price = precos_manuais[ticker] if precos_manuais[ticker] > 0 else market_prices[ticker]
    
    # Cálculos
    if conf['tipo'] == 'Acao':
        teto = (conf['lpa'] * conf['payout']) / yield_alvo
    else:
        teto = conf['dpa'] / 0.025 # Yield EUA fixo
        
    margem = ((teto - price) / teto) * 100
    
    with cols[idx % 4]:
        st.markdown(f"""
            <div class="card-equity">
                <img src="{conf['logo']}" width="60">
                <p><b>{ticker}</b></p>
                <h3>R$ {price:.2f}</h3>
                <span class="{'badge-buy' if margem > 0 else 'badge-wait'}">{margem:.1f}%</span>
                <p style="font-size:12px;">Teto Sugerido: R$ {teto:.2f}</p>
            </div>
        """, unsafe_allow_html=True)
    idx += 1
