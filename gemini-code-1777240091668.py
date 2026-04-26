import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Configurações Iniciais e Estilo (Identidade Visual)
st.set_page_config(page_title="App Preço Teto - Investidor10 Style", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .card { padding: 20px; border-radius: 10px; background-color: white; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# 2. Parâmetros e Dados das Ações
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'metodo': 'Bazin'},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'metodo': 'Bazin'},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'metodo': 'Bazin'},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'metodo': 'Graham'}
}

# 3. Sidebar de Preferências
st.sidebar.header("⚙️ Configurações")
yield_selecionado = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.09], format_func=lambda x: f"{int(x*100)}%")
btn_update = st.sidebar.button("🔄 Forçar Update de Valores")

# 4. Função para buscar dados (Simulando Integração Investidor10/Yahoo Finance)
@st.cache_data(ttl=3600) # Atualiza a cada hora ou no botão
def buscar_dados(tickers):
    resultados = {}
    for t in tickers:
        data = yf.Ticker(t)
        info = data.info
        # Simulando DPA (Dividendos por Ação) e LPA/VPA
        resultados[t] = {
            'preco_atual': info.get('currentPrice', 0),
            'dpa': info.get('trailingAnnualDividendRate', 0),
            'lpa': info.get('trailingEps', 0),
            'vpa': info.get('bookValue', 0)
        }
    return resultados

dados = buscar_dados(list(acoes_config.keys()))

# 5. Dashboard Principal
st.title("📊 Painel de Preço Teto & Margem de Segurança")
st.info("Dados baseados na estratégia de dividendos e métricas de valor patrimonial.")

cols = st.columns(4)

for i, (ticker, config) in enumerate(acoes_config.items()):
    with cols[i]:
        d = dados[ticker]
        
        # Lógica de Cálculo
        if config['metodo'] == 'Bazin':
            preco_teto = d['dpa'] / yield_selecionado
        else: # Graham: raiz(22.5 * LPA * VPA)
            preco_teto = (22.5 * d['lpa'] * d['vpa']) ** 0.5 if d['lpa'] > 0 else 0
            
        margem = ((preco_teto - d['preco_atual']) / preco_teto) * 100 if preco_teto > 0 else 0
        cor_margem = "green" if margem > 0 else "red"
        status = "COMPRA" if margem > 0 else "AGUARDAR"

        # Interface Visual
        st.markdown(f"""
            <div class="card" style="border-top: 8px solid {config['cor']};">
                <h3 style="color:{config['cor']};">{ticker.replace('.SA', '')}</h3>
                <p><b>{config['nome']}</b></p>
                <hr>
                <p>Preço Atual: <b>R$ {d['preco_atual']:.2f}</b></p>
                <p>Preço Teto: <b style="font-size: 1.2em;">R$ {preco_teto:.2f}</b></p>
                <p style="color:{cor_margem};">Margem: <b>{margem:.2f}%</b></p>
                <div style="background-color:{cor_margem}; color:white; text-align:center; padding:5px; border-radius:5px;">
                    {status}
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Nota: O cálculo de Graham é aplicado preferencialmente para AXIA6 conforme solicitado. Para as demais, utiliza-se o Yield desejado sobre os dividendos históricos.")