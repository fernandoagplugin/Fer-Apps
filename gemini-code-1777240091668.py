import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import os

# 1. Configurações da Página
st.set_page_config(page_title="Preço Teto Ações", layout="wide")

# --- LÓGICA DE PERSISTÊNCIA ---
DB_FILE = "settings_cache.json"

def carregar_configuracoes():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_configuracoes(config_dict):
    with open(DB_FILE, "w") as f:
        json.dump(config_dict, f)

# Carrega o estado salvo ou inicia vazio
if 'user_settings' not in st.session_state:
    st.session_state.user_settings = carregar_configuracoes()

# ------------------------------

# Estilos Visuais
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

st.markdown('<div class="main-title">Preço Teto Ações</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">por Fer</div>', unsafe_allow_html=True)

# 2. Configuração de Ativos
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.90, 'lpa_base': 1.15, 'logo': 'https://s3-symbol-logo.tradingview.com/caixa-seguridade-on-nm--big.svg'},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.35, 'lpa_base': 1.20, 'logo': 'https://s3-symbol-logo.tradingview.com/itausa--big.svg'},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.50, 'lpa_base': 0.65, 'logo': 'https://s3-symbol-logo.tradingview.com/copel--big.svg'},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 1.10, 'lpa_base': 0.50, 'logo': 'https://cdn-icons-png.flaticon.com/512/2731/2731636.png'}
}

# 3. Sidebar - Parâmetros com Persistência
st.sidebar.header("⚙️ Parâmetros de Mercado")

# Yield salvo ou padrão 6%
saved_yield = st.session_state.user_settings.get('yield_alvo', 0.06)
yield_alvo = st.sidebar.slider("Yield Mínimo Desejado (%)", 6, 12, int(saved_yield*100)) / 100

# Se o yield mudar, salva
if yield_alvo != saved_yield:
    st.session_state.user_settings['yield_alvo'] = yield_alvo
    salvar_configuracoes(st.session_state.user_settings)

st.sidebar.markdown("---")
st.sidebar.header("🔮 Projeções Futuras")

projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        # Busca valores salvos específicos da ação ou usa o padrão da config
        saved_lpa = st.session_state.user_settings.get(f'lpa_{ticker}', conf['lpa_base'])
        saved_payout = st.session_state.user_settings.get(f'payout_{ticker}', conf['payout_base'])
        
        lpa_p = st.number_input(f"LPA Projetado ({ticker[:5]})", value=float(saved_lpa), step=0.05, key=f"in_lpa_{ticker}")
        payout_p = st.slider(f"Payout % ({ticker[:5]})", 10, 200, int(saved_payout*100), key=f"in_p_{ticker}") / 100
        
        # Se os valores mudarem, salva no JSON
        if lpa_p != saved_lpa or (payout_p != saved_payout):
            st.session_state.user_settings[f'lpa_{ticker}'] = lpa_p
            st.session_state.user_settings[f'payout_{ticker}'] = payout_p
            salvar_configuracoes(st.session_state.user_settings)
            
        projeções[ticker] = {'lpa': lpa_p, 'payout': payout_p}

# 4. Busca de Dados e Interface (Mantida a lógica anterior)
@st.cache_data(ttl=3600)
def buscar_dados(tickers):
    dados = {}
    divo_hist = yf.Ticker("DIVO11.SA").history(period="10y")['Close']
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="10y")['Close']
            if hist.empty: continue
            divo_sync = divo_hist.reindex(hist.index, method='ffill')
            dados[t] = {'preco': hist.iloc[-1], 'hist_norm': (hist / hist.iloc[0]) * 100, 
                        'divo_norm': (divo_sync / divo_sync.iloc[0]) * 100, 'datas': hist.index}
        except: continue
    return dados

dados_mercado = buscar_dados(list(acoes_config.keys()))

cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in dados_mercado:
        with cols[i]:
            d = dados_mercado[ticker]
            dpa_proj = projeções[ticker]['lpa'] * projeções[ticker]['payout']
            teto_proj = dpa_proj / yield_alvo
            margem = ((teto_proj - d['preco']) / teto_proj) * 100 if teto_proj > 0 else -100
            cor_m = "#28a745" if margem > 0 else "#dc3545"

            st.markdown(f"""
                <div class="card" style="border-top: 8px solid {conf['cor']};">
                    <div class="logo-container"><img src="{conf['logo']}" class="logo-img"></div>
                    <b style="font-size:1.4em;">{ticker[:5]}</b><br>
                    <small style="color:gray;">{conf['nome']}</small><hr style="width:100%">
                    <p style="margin:0; font-size:0.95em;">Cotação: <b>R$ {d['preco']:.2f}</b></p>
                    <p style="margin:0; font-size:0.95em;">Div. Estimado: <b>R$ {dpa_proj:.2f}</b></p>
                    <p style="margin:10px 0 5px 0; font-size:1.2em; color:{cor_m};">Teto: <b>R$ {teto_proj:.2f}</b></p>
                    <div style="background-color:{cor_m}; color:white; text-align:center; border-radius:8px; margin-top:auto; padding:8px; font-weight:bold; width:100%;">
                        Margem: {margem:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)

# 5. Gráfico (Mantido)
st.markdown("---")
st.subheader(f"📊 Performance vs DIVO11 e CDI (10 Anos)")
ticker_sel = st.selectbox("Selecione o Ativo:", list(dados_mercado.keys()), format_func=lambda x: x[:5])

if ticker_sel in dados_mercado:
    d = dados_mercado[ticker_sel]
    cdi_norm = [100 * (1.116)**(i/252) for i in range(len(d['datas']))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d['datas'], y=d['hist_norm'], name=f"{ticker_sel[:5]}", line=dict(color=acoes_config[ticker_sel]['cor'], width=3)))
    fig.add_trace(go.Scatter(x=d['datas'], y=d['divo_norm'], name='DIVO11', line=dict(color='#95a5a6', dash='dash')))
    fig.add_trace(go.Scatter(x=d['datas'], y=cdi_norm, name='CDI', line=dict(color='#e74c3c', dash='dot')))
    fig.update_layout(template="plotly_white", hovermode="x unified", height=500, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
