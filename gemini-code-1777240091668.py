import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="App Preço Teto Estratégico", layout="wide")

# Configuração das Ações
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.90, 'lpa_base': 1.10},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.40, 'lpa_base': 1.15},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.50, 'lpa_base': 0.60},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 0.30, 'lpa_base': 0.50}
}

st.sidebar.header("🎯 Parâmetros de Mercado")
yield_alvo = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.10], index=0, format_func=lambda x: f"{int(x*100)}%")

st.sidebar.markdown("---")
st.sidebar.header("🔮 Projeções Individuais")

# Criando inputs dinâmicos para cada ação
projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        lpa_p = st.number_input(f"LPA Projetado ({ticker[:5]})", value=conf['lpa_base'], step=0.05)
        payout_p = st.slider(f"Payout Projetado % ({ticker[:5]})", 10, 100, int(conf['payout_base']*100)) / 100
        projeções[ticker] = {'lpa': lpa_p, 'payout': payout_p}

@st.cache_data(ttl=3600)
def buscar_precos(tickers):
    dados = {}
    for t in tickers:
        tk = yf.Ticker(t)
        hist = tk.history(period="1d")
        dados[t] = hist['Close'].iloc[-1] if not hist.empty else 0
    return dados

precos = buscar_precos(list(acoes_config.keys()))

st.title("📈 Calculadora de Valor Justo Projetado")

cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    with cols[i]:
        p_atual = precos[ticker]
        lpa_f = projeções[ticker]['lpa']
        payout_f = projeções[ticker]['payout']
        
        # O Pulo do Gato: Dividendo Projetado
        dpa_proj = lpa_f * payout_f
        teto = dpa_proj / yield_alvo
        
        margem = ((teto - p_atual) / teto) * 100 if teto > 0 else 0
        cor_card = "#28a745" if margem > 0 else "#dc3545"

        st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background-color:white; border-top:8px solid {conf['cor']}; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <h3 style="margin:0;">{ticker[:5]}</h3>
                <p style="color:gray; font-size:0.8em; margin:0;">{conf['nome']}</p>
                <hr>
                <small>Preço Atual:</small> <b>R$ {p_atual:.2f}</b><br>
                <small>Div. Projetado:</small> <b>R$ {dpa_proj:.2f}</b><br>
                <p style="margin-top:10px; margin-bottom:5px;">Preço Teto:</p>
                <b style="font-size:1.5em; color:{cor_card};">R$ {teto:.2f}</b>
                <div style="margin-top:10px; font-size:0.9em;">
                    Margem: <b>{margem:.1f}%</b>
                </div>
            </div>
        """, unsafe_allow_html=True)

st.info("💡 **Dica:** Tente ajustar o Payout ou o LPA na barra lateral conforme as notícias recentes das empresas. Se o Preço Teto está baixo, talvez sua projeção esteja muito conservadora ou o mercado esteja aceitando um Yield menor que 6%.")
