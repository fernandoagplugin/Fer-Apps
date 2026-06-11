import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import json
import os

# 1. Configurações da Página
st.set_page_config(page_title="EquityDash - Preço Teto", layout="wide")

# --- LÓGICA DE PERSISTÊNCIA ---
DB_FILE = "settings_cache.json"

def carregar_configuracoes():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
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
    .main-title { font-family: 'Roboto', sans-serif; font-size: 48px; font-weight: 700; text-align: center; margin-bottom: 0px; color: #1E1E1E; }
    .subtitle { font-family: 'Roboto', sans-serif; font-size: 18px; text-align: center; color: #666; margin-top: -5px; margin-bottom: 30px; font-style: italic; }
    .card { padding: 20px; border-radius: 15px; background-color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center; height: 100%; border: 1px solid #eee; display: flex; flex-direction: column; align-items: center; }
    .logo-container { display: flex; justify-content: center; align-items: center; margin-bottom: 15px; height: 80px; width: 100%; }
    .logo-img { max-width: 120px; max-height: 70px; object-fit: contain; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">EquityDash</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Preço Teto & Valuation</div>', unsafe_allow_html=True)

# 2. Configuração de Ativos (Links RAW do GitHub)
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"

acoes_config = {
    'AXIA3.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_base': 1.20, 'lpa_base': 0.65, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_base': 0.55, 'lpa_base': 0.85, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_base': 0.90, 'lpa_base': 1.40, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_base': 0.45, 'lpa_base': 1.55, 'logo': f"{base_raw}Itausa.png"},
    'SAPR4.SA': {'nome': 'Sanepar', 'cor': '#00a3e0', 'payout_base': 0.50, 'lpa_base': 1.10, 'logo': f"{base_raw}Sanepar.png"}
}

# 3. Sidebar - Parâmetros e Projeções
st.sidebar.header("⚙️ Parâmetros de Mercado")

# Correção do Slider de Yield (Vínculo direto com session_state via key)
if 'yield_alvo_slider' not in st.session_state:
    st.session_state.yield_alvo_slider = int(st.session_state.user_settings.get('yield_alvo', 0.06) * 100)

yield_valor = st.sidebar.slider("Yield Mínimo Desejado (%)", 6, 12, key='yield_alvo_slider')
yield_alvo = yield_valor / 100

# Sincronização com o arquivo de configurações
if yield_alvo != st.session_state.user_settings.get('yield_alvo'):
    st.session_state.user_settings['yield_alvo'] = yield_alvo
    salvar_configuracoes(st.session_state.user_settings)

if st.sidebar.button("🔄 Atualizar Preços Agora"):
    st.cache_data.clear()

st.sidebar.markdown("---")
st.sidebar.header("📈 Projeções Futuras (2026)")

projeções = {}
for ticker, conf in acoes_config.items():
    with st.sidebar.expander(f"Ajustar {ticker[:5]}"):
        s_lpa = st.session_state.user_settings.get(f'lpa_{ticker}', conf['lpa_base'])
        s_payout = st.session_state.user_settings.get(f'payout_{ticker}', conf['payout_base'])
        
        lpa_p = st.number_input(f"LPA ({ticker[:5]})", value=float(s_lpa), step=0.01, key=f"in_lpa_{ticker}")
        payout_p = st.slider(f"Payout % ({ticker[:5]})", 10, 200, int(s_payout*100), key=f"in_p_{ticker}") / 100
        
        if lpa_p != s_lpa or (payout_p != s_payout):
            st.session_state.user_settings[f'lpa_{ticker}'] = lpa_p
            st.session_state.user_settings[f'payout_{ticker}'] = payout_p
            salvar_configuracoes(st.session_state.user_settings)
            
        projeções[ticker] = {'lpa': lpa_p, 'payout': payout_p}

# 4. Busca de Dados
@st.cache_data(ttl=60)
def buscar_dados(tickers):
    todos = tickers + ['BOVA11.SA', 'DIVO11.SA']
    dados = {}
    for t in todos:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="10y")
            if hist.empty: continue
            dados[t] = {
                'preco': hist['Close'].iloc[-1],
                'hist_norm': (hist['Close'] / hist['Close'].iloc[0]) * 100,
                'datas': hist.index
            }
        except: continue
    return dados

dados_mercado = buscar_dados(list(acoes_config.keys()))

# 5. Interface de Cards (Layout Dinâmico em Múltiplas Linhas)
ativos_validos = [(ticker, conf) for ticker, conf in acoes_config.items() if ticker in dados_mercado]

# Cria o layout quebrando a linha a cada 4 ativos
for i in range(0, len(ativos_validos), 4):
    cols = st.columns(4)
    linha_atual = ativos_validos[i:i+4]
    
    for j, (ticker, conf) in enumerate(linha_atual):
        with cols[j]:
            d = dados_mercado[ticker]
            dpa_proj = projeções[ticker]['lpa'] * projeções[ticker]['payout']
            
            # Prevenção de divisão por zero
            teto_proj = dpa_proj / yield_alvo if yield_alvo > 0 else 0
            
            # Cálculo de margem seguro
            if teto_proj > 0:
                margem = ((teto_proj - d['preco']) / teto_proj) * 100
            else:
                margem = -100
                
            cor_m = "#28a745" if margem > 0 else "#dc3545"

            st.markdown(f"""
                <div class="card" style="border-top: 8px solid {conf['cor']};">
                    <div class="logo-container"><img src="{conf['logo']}" class="logo-img"></div>
                    <b style="font-size:1.3em;">{ticker[:5]}</b><br>
                    <small style="color:gray;">{conf['nome']}</small><hr style="width:100%">
                    <p style="margin:0; font-size:0.95em;">Preço Atual: <b>R$ {d['preco']:.2f}</b></p>
                    <p style="margin:0; font-size:0.95em;">Div. Projetado: <b>R$ {dpa_proj:.2f}</b></p>
                    <p style="margin:10px 0 5px 0; font-size:1.2em; color:{cor_m};">Teto: <b>R$ {teto_proj:.2f}</b></p>
                    <div style="background-color:{cor_m}; color:white; text-align:center; border-radius:8px; margin-top:auto; padding:8px; font-weight:bold; width:100%;">
                        Margem: {margem:.1f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)

# 6. Gráfico Comparativo
st.markdown("---")
st.subheader("📊 Performance Acumulada vs Índices (10 Anos)")

# Filtra o selectbox para mostrar apenas os ativos que carregaram corretamente
opcoes_grafico = [t for t in acoes_config.keys() if t in dados_mercado]

if opcoes_grafico:
    ticker_sel = st.selectbox("Selecione o ativo para comparação:", opcoes_grafico, format_func=lambda x: x[:5])

    if ticker_sel in dados_mercado:
        d = dados_mercado[ticker_sel]
        hover_fmt = "Rendimento: %{y:.2f}%<extra></extra>"
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=d['datas'], y=d['hist_norm'], name=f"{ticker_sel[:5]}", 
                                 hovertemplate=hover_fmt, line=dict(color=acoes_config[ticker_sel]['cor'], width=3.5)))
        
        if 'DIVO11.SA' in dados_mercado:
            fig.add_trace(go.Scatter(x=dados_mercado['DIVO11.SA']['datas'], y=dados_mercado['DIVO11.SA']['hist_norm'], 
                                     name='DIVO11', hovertemplate=hover_fmt, line=dict(color='#f1c40f', width=2, dash='dash')))
        
        if 'BOVA11.SA' in dados_mercado:
            fig.add_trace(go.Scatter(x=dados_mercado['BOVA11.SA']['datas'], y=dados_mercado['BOVA11.SA']['hist_norm'], 
                                     name='BOVA11', hovertemplate=hover_fmt, line=dict(color='#95a5a6', width=2, dash='dot')))

        fig.update_layout(template="plotly_white", hovermode="x unified", height=500, yaxis=dict(ticksuffix="%"),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nenhum dado de mercado foi carregado para exibir o gráfico.")
