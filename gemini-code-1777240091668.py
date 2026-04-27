import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup

# 1. Configurações Iniciais
st.set_page_config(page_title="App Preço Teto Automatizado", layout="wide")

# 2. Definição das Ações e Links
acoes_config = {
    'CXSE3': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout': 0.90, 'url': 'https://investidor10.com.br/acoes/cxse3/'},
    'ITSA4': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout': 0.35, 'url': 'https://investidor10.com.br/acoes/itsa4/'},
    'CPLE3': {'nome': 'Copel', 'cor': '#2d3e50', 'payout': 0.50, 'url': 'https://investidor10.com.br/acoes/cple3/'},
    'AXIA6': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout': 0.25, 'url': 'https://investidor10.com.br/acoes/axia6/'}
}

# 3. Função de Web Scraping para o Investidor 10
@st.cache_data(ttl=43200) # Atualiza a cada 12 horas
def extrair_dados_investidor10(ticker, url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Busca os cards de indicadores
        indicadores = soup.find_all("div", class_="_card-body")
        dados = {}
        for ind in indicadores:
            titulo = ind.find("span").text.strip() if ind.find("span") else ""
            valor = ind.find("div", class_="_card-value").text.strip() if ind.find("div", class_="_card-value") else "0"
            
            # Limpeza do valor (converte "R$ 1,20" para 1.20)
            valor_limpo = float(valor.replace("R$", "").replace(".", "").replace(",", ".").replace("%", "").strip())
            
            if "LPA" in titulo: dados['lpa'] = valor_limpo
            if "VPA" in titulo: dados['vpa'] = valor_limpo
            if "DY" in titulo: dados['dy_hist'] = valor_limpo
        return dados
    except:
        return {'lpa': 1.0, 'vpa': 1.0, 'dy_hist': 6.0}

# 4. Interface e Cálculos
st.title("📈 Preço Teto Automático (Web Scraping)")
yield_alvo = st.sidebar.selectbox("Yield Desejado", [0.06, 0.08, 0.09], format_func=lambda x: f"{int(x*100)}%")

if st.sidebar.button("🔄 Sincronizar com Investidor 10"):
    st.cache_data.clear()
    st.rerun()

cols = st.columns(len(acoes_config))

for i, (ticker, info) in enumerate(acoes_config.items()):
    with cols[i]:
        # Busca Preço no Yahoo Finance
        yf_ticker = yf.Ticker(f"{ticker}.SA")
        preco_atual = yf_ticker.history(period="1d")['Close'].iloc[-1]
        
        # Extrai LPA e VPA do Investidor 10
        dados_i10 = extrair_dados_investidor10(ticker, info['url'])
        
        lpa = dados_i10.get('lpa', 0)
        vpa = dados_i10.get('vpa', 0)
        
        # Cálculo Teto Projetivo (LPA * Payout / Yield)
        teto_proj = (lpa * info['payout']) / yield_alvo
        
        # Cálculo Graham (apenas para AXIA6 ou como segunda métrica)
        teto_graham = (22.5 * lpa * vpa) ** 0.5 if lpa > 0 and vpa > 0 else 0
        
        margem = ((teto_proj - preco_atual) / teto_proj) * 100
        cor = "green" if margem > 0 else "red"

        st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background-color:white; border-top:8px solid {info['cor']}; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <h4>{ticker}</h4>
                <p style="font-size:0.8em; color:gray;">{info['nome']}</p>
                <hr>
                <small>Preço Atual:</small> <b>R$ {preco_atual:.2f}</b><br>
                <small>LPA (I10):</small> <b>R$ {lpa:.2f}</b><br>
                <small>Preço Teto:</small> <b style="font-size:1.1em; color:#007bff;">R$ {teto_proj:.2f}</b><br>
                <div style="margin-top:10px; padding:5px; background-color:{cor}; color:white; text-align:center; border-radius:5px;">
                    Margem: {margem:.1f}%
                </div>
            </div>
        """, unsafe_allow_html=True)

# 5. Gráfico de Tendência
st.markdown("---")
ticker_sel = st.selectbox("Selecione para ver o gráfico:", list(acoes_config.keys()))
df_hist = yf.Ticker(f"{ticker_sel}.SA").history(period="1y")
fig = go.Figure(data=[go.Scatter(x=df_hist.index, y=df_hist['Close'], line=dict(color=acoes_config[ticker_sel]['cor']))])
fig.update_layout(title=f"Tendência 12 Meses - {ticker_sel}", template="plotly_white", height=400)
st.plotly_chart(fig, use_container_width=True)
