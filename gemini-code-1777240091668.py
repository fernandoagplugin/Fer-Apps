import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import os

# 1. Configurações da Página
st.set_page_config(page_title="Preço Teto Ações", layout="wide")

# --- PERSISTÊNCIA ---
DB_FILE = "settings_cache.json"

def carregar_configuracoes():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def salvar_configuracoes(config_dict):
    with open(DB_FILE, "w") as f:
        json.dump(config_dict, f)

if 'user_settings' not in st.session_state:
    st.session_state.user_settings = carregar_configuracoes()

# --- ESTILOS VISUAIS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;700&display=swap');
    .main-title { font-family: 'Roboto', sans-serif; font-size: 42px; font-weight: 700; text-align: center; color: #1E1E1E; margin-bottom: 30px; }
    .card { padding: 20px; border-radius: 15px; background-color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; height: 100%; border: 1px solid #eee; display: flex; flex-direction: column; align-items: center; }
    .logo-container { height: 70px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
    .logo-img { max-width: 100px; max-height: 60px; object-fit: contain; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">Preço Teto Ações</div>', unsafe_allow_html=True)

# 2. Configuração de Ativos
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 1.0, 'lpa_base': 0.65, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.5, 'lpa_base': 0.85, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.9, 'lpa_base': 1.40, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.4, 'lpa_base': 1.55, 'logo': f"{base_raw}Itausa.png"}
}

# 3. Busca de Dados (Preço, Índices e Consenso)
@st.cache_data(ttl=300)
def buscar_dados_completos(tickers):
    todos = tickers + ['BOVA11.SA', 'DIVO11.SA']
    dados = {}
    for t in todos:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="10y")
            if hist.empty: continue
            
            info = tk.info
            lpa_m = info.get('forwardEps') or info.get('trailingEps')
            
            dados[t] = {
                'preco': hist['Close'].iloc[-1],
                'lpa_consenso': lpa_m,
                'datas': hist.index,
                'hist_norm': (hist['Close'] / hist['Close'].iloc[0]) * 100
            }
        except: continue
    return dados

dados_mercado = buscar_dados_completos(list(acoes_config.keys()))

# 4. Sidebar - Parâmetros
st.sidebar.header("⚙️ Parâmetros")

if 'yield_alvo_slider' not in st.session_state:
    st.session_state.yield_alvo_slider = float(st.session_state.user_settings.get('yield_alvo', 0.06) * 100)

y_val = st.sidebar.slider("Yield Mínimo (%)", 6.0, 12.0, step=0.5, format="%.1f", key='yield_alvo_slider')
yield_alvo = y_val / 100

if yield_alvo != st.session_state.user_settings.get('yield_alvo'):
    st.session_state.user_settings['yield_alvo'] = yield_alvo
    salvar_configuracoes(st.session_state.user_settings)

# BOTÃO UPDATE: Limpa overrides manuais para forçar o deslizamento dos valores de mercado
if st.sidebar.button("Update"):
    for ticker in acoes_config:
        st.session_state.user_settings.pop(f'lpa_{ticker}', None)
        st.session_state.user_settings.pop(f'payout_{ticker}', None)
    
    salvar_configuracoes(st.session_state.user_settings)
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📈 Projeções 2026")

projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        
        # Lógica de preenchimento (Garante que nunca fique zerado na tela)
        v_lpa_original = st.session_state.user_settings.get(f'lpa_{ticker}')
        if v_lpa_original is None:
            cons = dados_mercado.get(ticker, {}).get('lpa_consenso')
            v_lpa_original = cons if cons and cons > 0 else conf['lpa_base']
        
        v_payout_original = st.session_state.user_settings.get(f'payout_{ticker}', conf['payout_base'])
        
        # Inputs manuais que recebem os valores de mercado ou padrão
        lpa_input = st.number_input(f"LPA {ticker[:5]}", value=float(v_lpa_original), step=0.01, key=f"n_{ticker}")
        payout_input = st.slider(f"Payout % {ticker[:5]}", 10, 200, int(v_payout_original * 100), key=f"s_{ticker}") / 100
        
        if lpa_input != v_lpa_original or payout_input != v_payout_original:
            st.session_state.user_settings[f'lpa_{ticker}'] = lpa_input
            st.session_state.user_settings[f'payout_{ticker}'] = payout_input
            salvar_configuracoes(st.session_state.user_settings)
            
        projeções[ticker] = {'lpa': lpa_input, 'payout': payout_input}

# 5. Interface de Cards
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in dados_mercado:
        d = dados_mercado[ticker]
        proj = projeções[ticker]
        dpa = proj['lpa'] * proj['payout']
        teto = dpa / yield_alvo if yield_alvo > 0 else 0
        margem = ((teto - d['preco']) / teto) * 100 if teto > 0 else -100
        cor = "#28a745" if margem > 0 else "#dc3545"
        
        with cols[i]:
            st.markdown(f"""
                <div class="card" style="border-top: 5px solid {conf['cor']};">
                    <div class="logo-container"><img src="{conf['logo']}" class="logo-img"></div>
                    <b>{ticker[:5]}</b><br>
                    <p style="margin:5px 0; font-size:14px;">Preço: R$ {d['preco']:.2f}</p>
                    <p style="margin:5px 0; font-size:14px;">Div: R$ {dpa:.2f}</p>
                    <p style="font-size:18px; color:{cor}; margin:10px 0;"><b>Teto: R$ {teto:.2f}</b></p>
                    <div style="background:{cor}; color:white; padding:5px; border-radius:5px; width:100%;"><b>{margem:.1f}%</b></div>
                </div>
            """, unsafe_allow_html=True)

# 6. Gráfico Comparativo de Performance (RESTAURADO)
st.markdown("---")
st.subheader("📊 Performance Acumulada vs Índices (10 Anos)")
ticker_sel = st.selectbox("Selecione para comparar:", list(acoes_config.keys()), format_func=lambda x: x[:5])

if ticker_sel in dados_mercado:
    d = dados_mercado[ticker_sel]
    fig = go.Figure()

    # Ativo Selecionado
    fig.add_trace(go.Scatter(x=d['datas'], y=d['hist_norm'], name=f"{ticker_sel[:5]}", 
                             line=dict(color=acoes_config[ticker_sel]['cor'], width=3.5)))
    
    # DIVO11
    if 'DIVO11.SA' in dados_mercado:
        fig.add_trace(go.Scatter(x=dados_mercado['DIVO11.SA']['datas'], y=dados_mercado['DIVO11.SA']['hist_norm'], 
                                 name='DIVO11', line=dict(color='#f1c40f', width=2, dash='dash')))
    
    # BOVA11
    if 'BOVA11.SA' in dados_mercado:
        fig.add_trace(go.Scatter(x=dados_mercado['BOVA11.SA']['datas'], y=dados_mercado['BOVA11.SA']['hist_norm'], 
                                 name='BOVA11', line=dict(color='#95a5a6', width=2, dash='dot')))

    fig.update_layout(template="plotly_white", hovermode="x unified", height=500,
                      yaxis=dict(ticksuffix="%"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
