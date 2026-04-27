import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="App Preço Teto: Ações vs Benchmarks", layout="wide")

# Configuração das Ações
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.90, 'lpa_base': 1.15},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.35, 'lpa_base': 1.20},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.50, 'lpa_base': 0.65},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 0.25, 'lpa_base': 0.50}
}

# Sidebar
st.sidebar.header("🎯 Parâmetros")
yield_alvo = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.10], index=0, format_func=lambda x: f"{int(x*100)}%")

st.sidebar.markdown("---")
st.sidebar.header("🔮 Ajuste sua Projeção")
projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Projetar {ticker[:5]}"):
        lpa_p = st.number_input(f"LPA Estimado ({ticker[:5]})", value=conf['lpa_base'], step=0.05)
        payout_p = st.slider(f"Payout % ({ticker[:5]})", 10, 100, int(conf['payout_base']*100)) / 100
        projeções[ticker] = {'lpa': lpa_p, 'payout': payout_p}

@st.cache_data(ttl=3600)
def buscar_dados_completos(tickers):
    dados = {}
    # Busca IBOV para comparação
    ibov = yf.Ticker("^BVSP").history(period="1y")['Close']
    
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            hist = tk.history(period="1y")['Close']
            
            # Normalização (Base 100) para comparação justa
            dados[t] = {
                'preco': info.get('currentPrice') or hist.iloc[-1],
                'dpa_hist': info.get('trailingAnnualDividendRate') or 0,
                'hist_norm': (hist / hist.iloc[0]) * 100,
                'ibov_norm': (ibov / ibov.iloc[0]) * 100,
                'datas': hist.index
            }
        except: continue
    return dados

dados_mercado = buscar_dados_completos(list(acoes_config.keys()))

st.title("📈 Performance vs Benchmarks (IBOV e CDI)")

# --- CARDS DE PREÇO TETO (Mesma lógica anterior) ---
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in dados_mercado:
        with cols[i]:
            d = dados_mercado[ticker]
            dpa_proj = projeções[ticker]['lpa'] * projeções[ticker]['payout']
            teto_proj = dpa_proj / yield_alvo
            margem = ((teto_proj - d['preco']) / teto_proj) * 100 if teto_proj > 0 else 0
            cor = "#28a745" if margem > 0 else "#dc3545"

            st.markdown(f"""
                <div style="padding:15px; border-radius:10px; background-color:white; border-top:8px solid {conf['cor']}; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
                    <h4 style="margin:0;">{ticker[:5]}</h4>
                    <hr>
                    <small>Preço Atual:</small> <b>R$ {d['preco']:.2f}</b><br>
                    <small>Teto Projetado:</small> <b style="color:{cor};">R$ {teto_proj:.2f}</b><br>
                    <div style="background-color:{cor}; color:white; text-align:center; border-radius:5px; margin-top:5px; font-size:0.8em;">
                        Margem: {margem:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# --- GRÁFICO COMPARATIVO ---
st.subheader("📊 Comparativo de Rentabilidade (Últimos 12 Meses)")
ticker_sel = st.selectbox("Selecione o Ativo para Comparar:", list(acoes_config.keys()))

if ticker_sel in dados_mercado:
    d = dados_mercado[ticker_sel]
    
    # Simulação do CDI (acumulado ~11% ao ano)
    dias_uteis = len(d['datas'])
    taxa_diaria = (1.11)**(1/252) - 1
    cdi_norm = [100 * (1 + taxa_diaria)**i for i in range(dias_uteis)]

    fig = go.Figure()

    # Linha do Ativo
    fig.add_trace(go.Scatter(x=d['datas'], y=d['hist_norm'], name=ticker_sel[:5], line=dict(color=acoes_config[ticker_sel]['cor'], width=3)))
    
    # Linha do IBOV
    fig.add_trace(go.Scatter(x=d['datas'], y=d['ibov_norm'], name='IBOVESPA', line=dict(color='#95a5a6', dash='dash')))
    
    # Linha do CDI
    fig.add_trace(go.Scatter(x=d['datas'], y=cdi_norm, name='CDI (Simulado)', line=dict(color='#e74c3c', dash='dot')))

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        yaxis_title="Retorno Acumulado (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Ajuste para mostrar 100 como ponto de partida (0%)
    fig.update_yaxes(tickformat=".0f")
    
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Nota: Os valores são normalizados para 100 no início do período para comparação direta de rentabilidade percentual.")
