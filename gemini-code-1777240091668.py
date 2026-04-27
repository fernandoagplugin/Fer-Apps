import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="App Preço Teto: Histórico vs Projetivo", layout="wide")

# Configuração das Ações
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.90, 'lpa_base': 1.15},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.35, 'lpa_base': 1.20},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.50, 'lpa_base': 0.65},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 0.25, 'lpa_base': 0.50}
}

st.sidebar.header("🎯 Parâmetros de Mercado")
yield_alvo = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.10], index=0, format_func=lambda x: f"{int(x*100)}%")

st.sidebar.markdown("---")
st.sidebar.header("🔮 Ajuste sua Projeção")
projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Projetar {ticker[:5]}"):
        lpa_p = st.number_input(f"LPA Estimado ({ticker[:5]})", value=conf['lpa_base'], step=0.05)
        payout_p = st.slider(f"Payout Estimado % ({ticker[:5]})", 10, 100, int(conf['payout_base']*100)) / 100
        projeções[ticker] = {'lpa': lpa_p, 'payout': payout_p}

@st.cache_data(ttl=3600)
def buscar_dados_completos(tickers):
    dados = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            # Preço Atual
            preco = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            # Dividendos pagos nos últimos 12 meses (Trailing Annual Dividend Rate)
            dpa_hist = info.get('trailingAnnualDividendRate') or info.get('dividendRate') or 0
            
            dados[t] = {
                'preco': preco,
                'dpa_hist': dpa_hist,
                'hist_grafico': tk.history(period="1y")
            }
        except:
            dados[t] = {'preco': 0, 'dpa_hist': 0, 'hist_grafico': pd.DataFrame()}
    return dados

dados_mercado = buscar_dados_completos(list(acoes_config.keys()))

st.title("📈 Calculadora de Preço Teto: Realidade vs Expectativa")
st.write(f"Comparando o que foi pago nos últimos 12 meses com sua projeção para um Yield de **{int(yield_alvo*100)}%**.")

cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    with cols[i]:
        d = dados_mercado.get(ticker)
        p_atual = d['preco']
        dpa_passado = d['dpa_hist']
        
        # 1. Cálculo Baseado no Passado (Automático)
        teto_hist = dpa_passado / yield_alvo if dpa_passado > 0 else 0
        
        # 2. Cálculo Baseado na sua Projeção (Manual)
        dpa_proj = projeções[ticker]['lpa'] * projeções[ticker]['payout']
        teto_proj = dpa_proj / yield_alvo
        
        # Margem de Segurança (Baseada na sua Projeção)
        margem = ((teto_proj - p_atual) / teto_proj) * 100 if teto_proj > 0 else 0
        cor_margem = "#28a745" if margem > 0 else "#dc3545"

        st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background-color:white; border-top:8px solid {conf['cor']}; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                <h3 style="margin:0;">{ticker[:5]}</h3>
                <small style="color:gray;">{conf['nome']}</small>
                <hr style="margin:10px 0;">
                <p style="margin:0; font-size:0.9em;">Preço Atual: <b>R$ {p_atual:.2f}</b></p>
                <p style="margin:0; font-size:0.9em; color:#555;">Div. Últimos 12m: <b>R$ {dpa_passado:.2f}</b></p>
                <p style="margin:0; font-size:0.9em; color:#007bff;">Div. Projetado: <b>R$ {dpa_proj:.2f}</b></p>
                <hr style="margin:10px 0;">
                <p style="margin:0; font-size:0.8em; color:gray;">Teto pelo Passado:</p>
                <b style="font-size:1.1em; color:#555;">R$ {teto_hist:.2f}</b>
                <p style="margin:10px 0 0 0; font-size:0.8em; color:gray;">Teto pela Projeção:</p>
                <b style="font-size:1.4em; color:{cor_margem};">R$ {teto_proj:.2f}</b>
                <div style="margin-top:10px; padding:3px; background-color:{cor_margem}; color:white; text-align:center; border-radius:5px; font-weight:bold; font-size:0.9em;">
                    Margem Proj: {margem:.1f}%
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")
# Gráfico de Tendência mantido para análise visual
ticker_sel = st.selectbox("Análise Visual de Tendência:", list(acoes_config.keys()))
df_hist = dados_mercado[ticker_sel]['hist_grafico']
if not df_hist.empty:
    fig = go.Figure(data=[go.Scatter(x=df_hist.index, y=df_hist['Close'], name='Preço', line=dict(color=acoes_config[ticker_sel]['cor']))])
    fig.update_layout(template="plotly_white", height=350, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
