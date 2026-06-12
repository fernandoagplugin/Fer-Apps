import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# Configuração Base
st.set_page_config(layout="wide")

# 1. ATIVOS: O PREÇO AQUI É A VERDADE ABSOLUTA
acoes_config = {
    'AXIA3.SA': {'tipo': 'Acao', 'price': 50.00, 'lpa': 6.80, 'payout': 1.0, 'vpa': 52.10, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png"},
    'CPLE3.SA': {'tipo': 'Acao', 'price': 15.90, 'lpa': 0.85, 'payout': 0.5, 'vpa': 10.40, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png"},
    # Adicione os outros aqui seguindo o mesmo padrão...
}

# 2. BUSCA DE DADOS (APENAS PARA OS GRÁFICOS)
@st.cache_data(ttl=3600)
def get_hist_data():
    results = {}
    for t in acoes_config.keys():
        try:
            tk = yf.Ticker(t)
            results[t] = tk.history(period="2y")
        except:
            results[t] = pd.DataFrame()
    return results

market_hist = get_hist_data()

# 3. INTERFACE
cols = st.columns(len(acoes_config))
for i, (ticker, conf) in enumerate(acoes_config.items()):
    # FORÇA O USO DO PREÇO DO DICIONÁRIO
    price = conf['price']
    
    with cols[i]:
        st.metric(ticker, f"R$ {price:.2f}")

# 4. GRÁFICOS (PROTEGIDOS)
st.markdown("---")
target = st.selectbox("Selecione o ativo:", list(acoes_config.keys()))
if target in market_hist and not market_hist[target].empty:
    fig = go.Figure(go.Scatter(x=market_hist[target].index, y=market_hist[target]['Close']))
    fig.update_layout(title=f"Histórico {target}", height=300)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Sem dados históricos para este ativo no Yahoo.")
