import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Configuração simples e robusta
st.set_page_config(layout="wide", page_title="EquityDash")

# 1. Definição dos ativos (Apenas tickers atuais)
# Adicionei o preço 'base' como referência para caso a API falhe
acoes_config = {
    'AXIA3.SA': {'nome': 'Axia Energia', 'logo': 'https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png', 'base': 50.0},
    'CPLE3.SA': {'nome': 'Copel', 'logo': 'https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png', 'base': 15.0}
}

st.title("EquityDash - Painel Blindado")

# 2. Busca de dados protegida por tratamento de erro
@st.cache_data(ttl=600)
def buscar_precos():
    precos = {}
    for ticker in acoes_config:
        try:
            # Busca rápida usando fast_info para evitar erros de histórico
            preco = yf.Ticker(ticker).fast_info['last_price']
            precos[ticker] = preco if preco > 1 else acoes_config[ticker]['base']
        except:
            precos[ticker] = acoes_config[ticker]['base']
    return precos

precos_mercado = buscar_precos()

# 3. Exibição dos Cards com opção de correção manual
cols = st.columns(len(acoes_config))
for i, (ticker, conf) in enumerate(acoes_config.items()):
    with cols[i]:
        st.image(conf['logo'], width=80)
        st.subheader(ticker)
        
        # Campo de entrada para corrigir o preço caso a API erre
        preco_manual = st.number_input(f"Ajustar preço {ticker}", value=float(precos_mercado[ticker]), step=0.1, key=f"in_{ticker}")
        
        st.metric("Preço Atual", f"R$ {preco_manual:.2f}")
        st.info("O cálculo do valuation usará o preço ajustado acima.")

# 4. Botão de reset
if st.button("Recarregar dados do mercado"):
    st.cache_data.clear()
    st.rerun()
