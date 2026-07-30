import streamlit as st
import yfinance as yf
import pandas as pd
import math

# 1. Configurações da Página
LOGO_SIDEBAR = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Logo.png"
LOGO_HEADER = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Horizontal.png"

st.set_page_config(page_title="EquityDash Ultra v7.1", page_icon=LOGO_SIDEBAR, layout="wide")

# --- CSS Profissional ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; background-color: #f8f9fa; }}
    .main-header {{ background-color: #20B2AA; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 30px; }}
    .header-logo {{ width: 500px; height: auto; display: block; margin: 0 auto; }}
    .card-equity {{ background: white; padding: 20px; border-radius: 20px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }}
    .badge-buy {{ background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }}
    .badge-wait {{ background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }}
    .badge-error {{ background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }}
    .label-text {{ color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
    </style>
    """, unsafe_allow_html=True)

st.sidebar.image(LOGO_SIDEBAR, use_container_width=True)
st.markdown(f'<div class="main-header"><img src="{LOGO_HEADER}" class="header-logo"></div>', unsafe_allow_html=True)

# 2. Ativos
acoes_config = {
    'AXIA3.SA': {'cor': '#3bb54a', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png"},
    'CPLE3.SA': {'cor': '#2d3e50', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png"},
    'CXSE3.SA': {'cor': '#005ca9', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Caixa.png"},
    'ITSA4.SA': {'cor': '#ec7000', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Itausa.png"},
    'SAPR4.SA': {'cor': '#009fe3', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0dd7c40bf47a5487a468aeaca985451e8d24cc6a/Sanepar.PNG"},
    'BRBI11.SA': {'cor': '#1e3a8a', 'logo': "https://placehold.co/100x40/f8f9fa/64748b?text=BRBI11"},
    'SBSP3.SA': {'cor': '#0284c7', 'logo': "https://placehold.co/100x40/f8f9fa/64748b?text=SBSP3"}
}

# 3. Sidebar - Apenas Filtros
st.sidebar.title("⚙️ Filtros de Valuation")
yield_valor_br = st.sidebar.select_slider("Yield Alvo BR (Bazin) %", options=[round(x*0.1, 1) for x in range(60, 125, 5)], value=6.0)
yield_alvo_br = yield_valor_br / 100

# 4. Engine de Dados Mais Robusta
@st.cache_data(ttl=600)
def get_live_data():
    tickers = list(acoes_config.keys())
    results = {}
    
    # Data de corte para somar dividendos dos últimos 12 meses
    um_ano_atras = pd.Timestamp.now(tz='UTC') - pd.DateOffset(years=1)

    for t in tickers:
        try:
            tk = yf.Ticker(t)
            
            # Preço mais recente
            hist = tk.history(period="1mo")
            preco = hist['Close'].iloc[-1] if not hist.empty else 0
            
            # Dividendos Reais Pagos (Soma dos últimos 12 meses da aba de proventos)
            divs = tk.dividends
            if not divs.empty:
                divs.index = pd.to_datetime(divs.index, utc=True)
                divs_12m = divs[divs.index >= um_ano_atras].sum()
            else:
                divs_12m = 0
                
            # Dados de Balanço (LPA e VPA) - Yahoo costuma falhar aqui para BR
            info = tk.info
            lpa = info.get('trailingEps') or info.get('forwardEps') or 0
            vpa = info.get('bookValue') or 0
            
            results[t] = {
                'p': preco, 
                'lpa': lpa,
                'vpa': vpa,
                'div_pagos': divs_12m
            }
        except Exception: 
            results[t] = {'p': 0, 'lpa': 0, 'vpa': 0, 'div_pagos': 0}
            
    return results

market_data = get_live_data()

# 5. Cards
cols = st.columns(len(acoes_config))

for i, ticker in enumerate(acoes_config.keys()):
    conf = acoes_config[ticker]
    dados = market_data[ticker]
    
    price = dados['p']
    lpa = dados['lpa']
    vpa = dados['vpa']
    div_pagos = dados['div_pagos']
    
    # Só calcula se a API retornou dados válidos
    if price > 0 and lpa > 0 and vpa > 0:
        t_bazin = div_pagos / yield_alvo_br if yield_alvo_br > 0 else 0
        t_graham = math.sqrt(max(0, 22.5 * lpa * vpa))
        
        peso_b = 0.8 if ticker in ['CXSE3.SA', 'SAPR4.SA', 'CPLE3.SA', 'SBSP3.SA'] else 0.5
        teto = (t_bazin * peso_b) + (t_graham * (1 - peso_b))
        
        margem = ((teto - price) / teto) * 100 if teto > 0 else 0
        badge_html = f'<span class="{"badge-buy" if margem > 0 else "badge-wait"}">{margem:.1f}%</span>'
    else:
        t_bazin = t_graham = teto = margem = 0
        badge_html = '<span class="badge-error">Sem Dados de Balanço</span>'

    with cols[i]:
        st.markdown(f"""
            <div class="card-equity">
                <img src="{conf['logo']}" style="max-width:100px; height:40px; margin:auto; object-fit:contain;">
                <div class="label-text" style="margin-top:10px;">{ticker}</div>
                <div style="font-size:22px; font-weight:700;">R$ {price:.2f}</div>
                {badge_html}
                <div style="margin-top:15px; text-align: left; background: #fdfdfd; padding: 10px; border-radius: 10px; font-size:12px;">
                    Bazin: <b>R$ {t_bazin:.2f}</b><br>
                    Graham: <b>R$ {t_graham:.2f}</b><br>
                    Teto: <b style="color:#1e3a8a">R$ {teto:.2f}</b>
                </div>
            </div>
        """, unsafe_allow_html=True)
