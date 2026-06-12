import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações da Página
st.set_page_config(page_title="EquityDash Ultra v6.8", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .card-equity { background: white; padding: 20px; border-radius: 20px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; }
    .badge-buy { background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    .badge-wait { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração (AXIA3.SA com preço fixo de 50.00)
acoes_config = {
    'AXIA3.SA': {'tipo': 'Acao', 'cor': '#3bb54a', 'payout': 1.0, 'lpa': 6.80, 'vpa': 52.10, 'price': 50.00, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png", 'moeda': 'R$'},
    'CPLE3.SA': {'tipo': 'Acao', 'cor': '#2d3e50', 'payout': 0.5, 'lpa': 0.85, 'vpa': 10.40, 'price': 15.90, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png", 'moeda': 'R$'},
    'CXSE3.SA': {'tipo': 'Acao', 'cor': '#005ca9', 'payout': 0.9, 'lpa': 1.40, 'vpa': 4.10, 'price': 18.09, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Caixa.png", 'moeda': 'R$'}
}

# 3. Engine de Dados Protegida
@st.cache_data(ttl=600)
def get_market_data():
    results = {}
    for t in acoes_config.keys():
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="2y")
            results[t] = hist['Close'].iloc[-1] if not hist.empty else None
        except:
            results[t] = None
    return results

market_prices = get_market_data()

# 4. Interface e Cálculos
cols = st.columns(len(acoes_config))
for i, (ticker, conf) in enumerate(acoes_config.items()):
    # Seleção de preço: usa o da API se disponível, senão usa o da config
    price = market_prices.get(ticker) or conf['price']
    
    # Cálculo Bazin
    teto = (conf['lpa'] * conf['payout']) / 0.06
    margem = ((teto - price) / teto) * 100
    
    with cols[i]:
        st.markdown(f"""
            <div class="card-equity">
                <img src="{conf['logo']}" width="50">
                <p><b>{ticker}</b></p>
                <h3>{conf['moeda']} {price:.2f}</h3>
                <span class="{'badge-buy' if margem > 0 else 'badge-wait'}">Margem: {margem:.1f}%</span>
            </div>
        """, unsafe_allow_html=True)

# 5. Gráfico de Histórico Protegido
st.markdown("---")
target = st.selectbox("Selecione para Gráfico:", list(acoes_config.keys()))
hist = yf.Ticker(target).history(period="2y")

if not hist.empty:
    st.line_chart(hist['Close'])
else:
    st.error("Dados históricos indisponíveis para este ativo.")
