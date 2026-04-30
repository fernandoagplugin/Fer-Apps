import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações da Página
st.set_page_config(page_title="EquityDash Ultra v5.3", layout="wide", initial_sidebar_state="expanded")

# --- CSS DEFINITIVO PARA O NOVO VISUAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Fundo e Fonte Geral */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    
    /* Cabeçalho com Gradiente e Logo */
    .main-header { 
        background: linear-gradient(90deg, #0f172a 0%, #1e3a8a 100%);
        padding: 50px 20px; 
        border-radius: 20px; 
        color: white; 
        text-align: center; 
        margin-bottom: 35px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .logo-img { 
        max-width: 150px; 
        margin-bottom: 20px; 
        border-radius: 15px;
        border: 2px solid rgba(255,255,255,0.1);
    }

    /* Estilo dos Cards */
    .card-equity {
        background: white; padding: 20px; border-radius: 20px; border: 1px solid #eef2f6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between;
    }
    .badge-buy { background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    .badge-wait { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    .label-text { color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO (Onde o Logo aparecerá) ---
# Dica: Quando tiver o link da imagem verde-água, coloque-o em LOGO_URL
LOGO_URL = "" 

header_content = f"""
    <div class="main-header">
        {f'<img src="{LOGO_URL}" class="logo-img">' if LOGO_URL else ""}
        <h1 style="margin:0; font-size: 3.5em; font-weight: 800; letter-spacing: -1px;">EquityDash Ultra</h1>
        <p style="opacity: 0.8; font-size: 1.2em; margin-top: 10px; font-weight: 300;">Análise Híbrida de Ativos • por Fer</p>
    </div>
"""
st.markdown(header_content, unsafe_allow_html=True)

# 2. Configuração de Ativos (Mantendo suas logos atuais)
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'cor': '#3bb54a', 'payout': 1.0, 'fallback_lpa': 0.65, 'fallback_vpa': 5.20, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'cor': '#2d3e50', 'payout': 0.5, 'fallback_lpa': 0.85, 'fallback_vpa': 10.40, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'cor': '#005ca9', 'payout': 0.9, 'fallback_lpa': 1.40, 'fallback_vpa': 4.10, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'cor': '#ec7000', 'payout': 0.4, 'fallback_lpa': 1.55, 'fallback_vpa': 8.90, 'logo': f"{base_raw}Itausa.png"}
}

# 3. Sidebar e Logica (Restante do Código)
st.sidebar.title("💰 Gestão")
valor_aporte = st.sidebar.number_input("Investimento (R$)", min_value=0.0, value=1000.0)
yield_valor = st.sidebar.select_slider("Yield Alvo %", options=[round(x*0.1,1) for x in range(60, 125, 5)], value=6.0)
yield_alvo = yield_valor / 100

@st.cache_data(ttl=600)
def fetch_data(tickers):
    data = {}
    for t in tickers + ['BOVA11.SA', 'DIVO11.SA']:
        tk = yf.Ticker(t)
        h = tk.history(period="10y")
        if not h.empty:
            data[t] = {'price': h['Close'].iloc[-1], 'lpa': tk.info.get('forwardEps'), 'vpa': tk.info.get('bookValue'), 'hist': h}
    return data

m_data = fetch_data(list(acoes_config.keys()))

# Cards
calculos = []
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in m_data:
        d = m_data[ticker]
        lpa = d['lpa'] or conf['fallback_lpa']
        vpa = d['vpa'] or conf['fallback_vpa']
        
        t_bazin = (lpa * conf['payout']) / yield_alvo
        t_graham = math.sqrt(max(0, 22.5 * lpa * vpa)) if lpa > 0 and vpa > 0 else 0
        
        # Lógica CXSE3 (80/20)
        teto = (t_bazin * 0.8 + t_graham * 0.2) if ticker == 'CXSE3.SA' else (t_bazin + t_graham) / 2
        margem = ((teto - d['price']) / teto) * 100
        calculos.append({'ticker': ticker, 'margem': margem, 'price': d['price']})

        with cols[i]:
            st.markdown(f"""
                <div class="card-equity">
                    <img src="{conf['logo']}" style="height:35px; margin-bottom:10px; object-fit:contain;">
                    <div class="label-text">{ticker}</div>
                    <div style="font-size:24px; font-weight:700;">R$ {d['price']:.2f}</div>
                    <span class="{"badge-buy" if margem > 0 else "badge-wait"}">{"COMPRA" if margem > 0 else "ESPERAR"}</span>
                    <div style="margin-top:15px; padding-top:10px; border-top:1px solid #eee; font-size:13px;">
                        Teto: <b>R$ {teto:.2f}</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# Gráfico com Legenda Corrigida
st.markdown("---")
target = st.selectbox("Comparativo:", list(acoes_config.keys()))
if target in m_data:
    fig = go.Figure()
    # Adicionar traces... (simplificado para o exemplo)
    fig.add_trace(go.Scatter(y=m_data[target]['hist']['Close'], name=target))
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        margin=dict(b=100), height=450
    )
    st.plotly_chart(fig, use_container_width=True)
