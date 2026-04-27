import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Configurações da Página
st.set_page_config(page_title="Preço Teto Ações", layout="wide")

# Estilos Visuais - Foco na Fixação e Design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;700&display=swap');
    
    .main-title { font-family: 'Roboto', sans-serif; font-size: 48px; font-weight: 700; text-align: center; margin-bottom: 0px; color: #1E1E1E; }
    .subtitle { font-family: 'Roboto', sans-serif; font-size: 18px; text-align: center; color: #666; margin-top: -5px; margin-bottom: 30px; }
    .card { padding: 20px; border-radius: 15px; background-color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; height: 100%; border: 1px solid #eee; display: flex; flex-direction: column; align-items: center; }
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 15px; height: 80px; width: 100%; }
    .logo-img { max-width: 100px; max-height: 70px; object-fit: contain; }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho Fixo
st.markdown('<div class="main-title">Preço Teto Ações</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">por Fer</div>', unsafe_allow_html=True)

# 2. Configuração com Tickers e Logos estáveis
acoes_config = {
    'CXSE3.SA': {
        'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.90, 'lpa_base': 1.15,
        'logo': 'https://s3-symbol-logo.tradingview.com/caixa-seguridade-on-nm--big.svg'
    },
    'ITSA4.SA': {
        'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.35, 'lpa_base': 1.20,
        'logo': 'https://s3-symbol-logo.tradingview.com/itausa--big.svg'
    },
    'CPLE3.SA': {
        'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.50, 'lpa_base': 0.65,
        'logo': 'https://s3-symbol-logo.tradingview.com/copel--big.svg'
    },
    'AXIA6.SA': {
        'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 1.10, 'lpa_base': 0.50,
        'logo': 'https://s3-symbol-logo.tradingview.com/braskem-pna--big.svg' # Placeholder de energia estável
    }
}

# 3. Sidebar - Payout agora vai até 200%
st.sidebar.header("⚙️ Parâmetros")
yield_alvo = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.10], index=0, format_func=lambda x: f"{int(x*100)}%")

st.sidebar.markdown("---")
st.sidebar.header("🔮 Projeções Futuras")
projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        lpa_p = st.number_input(f"LPA Projetado ({ticker[:5]})", value=conf['lpa_base'], step=0.05, key=f"lpa_{ticker}")
        # AJUSTE: Payout agora com max_value de 200
        payout_p = st.slider(f"Payout % ({ticker[:5]})", 10, 200, int(conf['payout_base']*100), key=f"p_{ticker}") / 100
        projeções[ticker] = {'lpa': lpa_p, 'payout': payout_p}

@st.cache_data(ttl=3600)
def buscar_dados(tickers):
    dados = {}
    divo_tk = yf.Ticker("DIVO11.SA")
    divo_hist = divo_tk.history(period="10y")['Close']
    
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="10y")['Close']
            if hist.empty: continue
            
            divo_sync = divo_hist.reindex(hist.index, method='ffill')
            dados[t] = {
                'preco': hist.iloc[-1],
                'hist_norm': (hist / hist.iloc[0]) * 100,
                'divo_norm': (divo_sync / divo_sync.iloc[0]) * 100,
                'datas': hist.index
            }
        except: continue
    return dados

dados_mercado = buscar_dados(list(acoes_config.keys()))

# 4. Interface de Cards
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in dados_mercado:
        with cols[i]:
            d = dados_mercado[ticker]
            # Cálculo do dividendo esperado (LPA * Payout)
            dpa_proj = projeções[ticker]['lpa'] * projeções[ticker]['payout']
            teto_proj = dpa_proj / yield_alvo
            
            margem = ((teto_proj - d['preco']) / teto_proj) * 100 if teto_proj > 0 else -100
            cor_m = "#28a745" if margem > 0 else "#dc3545"

            st.markdown(f"""
                <div class="card" style="border-top: 8px solid {conf['cor']};">
                    <div class="logo-container">
                        <img src="{conf['logo']}" class="logo-img" onerror="this.src='https://cdn-icons-png.flaticon.com/512/25/25694.png';">
                    </div>
                    <b style="font-size:1.4em;">{ticker[:5]}</b><br>
                    <small style="color:gray;">{conf['nome']}</small>
                    <hr style="width:100%">
                    <p style="margin:0; font-size:1em;">Cotação: <b>R$ {d['preco']:.2f}</b></p>
                    <p style="margin:5px 0; font-size:1.1em;">Dividendos: <b>R$ {dpa_proj:.2f}</b></p>
                    <p style="margin:5px 0; font-size:1.2em; color:{cor_m};">Teto: <b>R$ {teto_proj:.2f}</b></p>
                    <div style="background-color:{cor_m}; color:white; text-align:center; border-radius:8px; margin-top:auto; padding:8px; font-weight:bold; width:100%;">
                        Margem: {margem:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# 5. Gráfico de Performance
st.subheader("📊 Performance Acumulada vs DIVO11 e CDI (10 Anos)")
ticker_sel = st.selectbox("Selecione o Ativo:", list(dados_mercado.keys()), format_func=lambda x: x[:5])

if ticker_sel in dados_mercado:
    d = dados_mercado[ticker_sel]
    # CDI 10 anos (~11.6% aa médio)
    cdi_norm = [100 * (1.116)**(i/252) for i in range(len(d['datas']))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d['datas'], y=d['hist_norm'], name=f"{ticker_sel[:5]}", line=dict(color=acoes_config[ticker_sel]['cor'], width=3)))
    fig.add_trace(go.Scatter(x=d['datas'], y=d['divo_norm'], name='DIVO11', line=dict(color='#95a5a6', dash='dash')))
    fig.add_trace(go.Scatter(x=d['datas'], y=cdi_norm, name='CDI', line=dict(color='#e74c3c', dash='dot')))

    fig.update_layout(template="plotly_white", hovermode="x unified", height=500,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
