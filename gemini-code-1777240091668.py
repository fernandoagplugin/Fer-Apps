import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Configurações da Página
st.set_page_config(page_title="Preço Teto Ações", layout="wide")

# Estilos Visuais
st.markdown("""
    <style>
    .main-title { font-size: 42px; font-weight: bold; text-align: center; margin-bottom: 0px; color: #1E1E1E; }
    .subtitle { font-size: 16px; text-align: center; color: #666; margin-bottom: 30px; font-style: italic; }
    .card { padding: 20px; border-radius: 12px; background-color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; }
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 15px; height: 60px; }
    .logo-img { border-radius: 8px; object-fit: contain; }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho Fixo
st.markdown('<div class="main-title">Preço Teto Ações</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">por Fer</div>', unsafe_allow_html=True)

# 2. Configuração das Ações com Domínios Corrigidos
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.90, 'lpa_base': 1.15, 'domain': 'caixaseguridade.com.br'},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.35, 'lpa_base': 1.20, 'domain': 'itausa.com.br'},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.50, 'lpa_base': 0.65, 'domain': 'copel.com.br'},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 0.25, 'lpa_base': 0.50, 'domain': 'axiaenergia.com.br'}
}

# 3. Sidebar
st.sidebar.header("⚙️ Parâmetros")
yield_alvo = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.10], index=0, format_func=lambda x: f"{int(x*100)}%")

st.sidebar.markdown("---")
st.sidebar.header("🔮 Projeções Futuras")
projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        lpa_p = st.number_input(f"LPA Projetado ({ticker[:5]})", value=conf['lpa_base'], step=0.05)
        payout_p = st.slider(f"Payout % ({ticker[:5]})", 10, 100, int(conf['payout_base']*100)) / 100
        projeções[ticker] = {'lpa': lpa_p, 'payout': payout_p}

@st.cache_data(ttl=3600)
def buscar_dados_longo_prazo(tickers):
    dados = {}
    ibov = yf.Ticker("^BVSP").history(period="10y")['Close']
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="10y")['Close']
            if hist.empty: continue
            dados[t] = {
                'preco': hist.iloc[-1],
                'hist_norm': (hist / hist.iloc[0]) * 100,
                'ibov_norm': (ibov.reindex(hist.index, method='ffill') / ibov.iloc[0]) * 100,
                'datas': hist.index
            }
        except: continue
    return dados

dados_mercado = buscar_dados_longo_prazo(list(acoes_config.keys()))

# 4. Exibição dos Cards
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in dados_mercado:
        with cols[i]:
            d = dados_mercado[ticker]
            dpa_proj = projeções[ticker]['lpa'] * projeções[ticker]['payout']
            teto_proj = dpa_proj / yield_alvo
            margem = ((teto_proj - d['preco']) / teto_proj) * 100 if teto_proj > 0 else 0
            cor_m = "#28a745" if margem > 0 else "#dc3545"
            
            # Usando o serviço de favicon do Google que é mais resiliente para logos brasileiros
            logo_url = f"https://www.google.com/s2/favicons?domain={conf['domain']}&sz=128"

            st.markdown(f"""
                <div class="card" style="border-top: 8px solid {conf['cor']};">
                    <div class="logo-container">
                        <img src="{logo_url}" class="logo-img" width="50">
                    </div>
                    <b style="font-size:1.3em;">{ticker[:5]}</b><br>
                    <small style="color:gray;">{conf['nome']}</small>
                    <hr style="margin:15px 0;">
                    <p style="margin:0; font-size:1em;">Preço: <b>R$ {d['preco']:.2f}</b></p>
                    <p style="margin:5px 0; font-size:1.1em; color:{cor_m};">Teto: <b>R$ {teto_proj:.2f}</b></p>
                    <div style="background-color:{cor_m}; color:white; text-align:center; border-radius:6px; margin-top:10px; padding:5px; font-weight:bold;">
                        Margem: {margem:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# 5. Gráfico de Performance 10 Anos
st.subheader("📊 Performance Acumulada (10 Anos)")
ticker_sel = st.selectbox("Selecione o Ativo para Comparação:", list(dados_mercado.keys()), format_func=lambda x: x[:5])

if ticker_sel in dados_mercado:
    d = dados_mercado[ticker_sel]
    dias = len(d['datas'])
    # Simulação CDI composta
    cdi_norm = [100 * (1.108)**(i/252) for i in range(dias)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d['datas'], y=d['hist_norm'], name=f"Ação: {ticker_sel[:5]}", line=dict(color=acoes_config[ticker_sel]['cor'], width=3)))
    fig.add_trace(go.Scatter(x=d['datas'], y=d['ibov_norm'], name='Benchmark: IBOVESPA', line=dict(color='#95a5a6', dash='dash')))
    fig.add_trace(go.Scatter(x=d['datas'], y=cdi_norm, name='Benchmark: CDI', line=dict(color='#e74c3c', dash='dot')))

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0),
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
