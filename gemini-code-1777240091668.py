import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações da Página
LOGO_SIDEBAR = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Logo.png"
LOGO_HEADER = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Horizontal.png"

st.set_page_config(page_title="EquityDash Ultra v6.8", page_icon=LOGO_SIDEBAR, layout="wide")

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
    .label-text {{ color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
    </style>
    """, unsafe_allow_html=True)

st.sidebar.image(LOGO_SIDEBAR, use_container_width=True)
st.markdown(f'<div class="main-header"><img src="{LOGO_HEADER}" class="header-logo"></div>', unsafe_allow_html=True)

# 2. Ativos e Parâmetros (Inteligência REIT adicionada e Logo EQIX atualizado)
acoes_config = {
    'AXIA6.SA': {'tipo': 'Acao', 'cor': '#3bb54a', 'payout': 1.0, 'lpa': 6.80, 'vpa': 52.10, 'price': 68.65, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png", 'moeda': 'R$'},
    'CPLE3.SA': {'tipo': 'Acao', 'cor': '#2d3e50', 'payout': 0.5, 'lpa': 0.85, 'vpa': 10.40, 'price': 15.90, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png", 'moeda': 'R$'},
    'CXSE3.SA': {'tipo': 'Acao', 'cor': '#005ca9', 'payout': 0.9, 'lpa': 1.40, 'vpa': 4.10, 'price': 18.09, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Caixa.png", 'moeda': 'R$'},
    'ITSA4.SA': {'tipo': 'Acao', 'cor': '#ec7000', 'payout': 0.4, 'lpa': 1.55, 'vpa': 8.90, 'price': 13.92, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Itausa.png", 'moeda': 'R$'},
    'SAPR4.SA': {'tipo': 'Acao', 'cor': '#009fe3', 'payout': 0.5, 'lpa': 1.10, 'vpa': 6.80, 'price': 7.88, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0dd7c40bf47a5487a468aeaca985451e8d24cc6a/Sanepar.PNG", 'moeda': 'R$'},
    'EQIX': {'tipo': 'REIT', 'cor': '#E31C23', 'dpa': 17.04, 'ffo': 34.80, 'price': 800.00, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/02b13adcb14ea6c1530085e2af5a531738423aec/Equinix_Logo.png", 'moeda': 'US$'}
}

# 3. Sidebar
st.sidebar.title("💰 Gestão de Capital")
valor_aporte = st.sidebar.number_input("Valor Investimento (R$)", min_value=0.0, value=1000.0)

st.sidebar.markdown("---")
st.sidebar.title("⚙️ Filtros de Valuation")
# Yield Brasil
yield_valor_br = st.sidebar.select_slider("Yield Alvo BR (Bazin) %", options=[round(x*0.1,1) for x in range(60,125,5)], value=6.0)
yield_alvo_br = yield_valor_br / 100

# Yield EUA
yield_valor_us = st.sidebar.select_slider("Yield Alvo EUA/REITs %", options=[round(x*0.1,1) for x in range(15,65,5)], value=2.5)
yield_alvo_us = yield_valor_us / 100

st.sidebar.markdown("---")
periodo_texto = st.sidebar.radio("Período Gráfico:", ["1 Ano", "2 Anos", "5 Anos", "10 Anos"], index=2)

# 4. Engine de Dados
@st.cache_data(ttl=600)
def get_data():
    tickers = list(acoes_config.keys()) + ['BOVA11.SA', 'DIVO11.SA']
    results = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            h = tk.history(period="10y")
            results[t] = {'p': h['Close'].iloc[-1] if not h.empty else None, 'h': h}
        except: results[t] = {'p': None, 'h': pd.DataFrame()}
    return results

market_data = get_data()

# 5. Cards (Ajustado para Valuation Híbrido BR/US)
calculos = []
cols = st.columns(len(acoes_config))
for i, ticker in enumerate(acoes_config.keys()):
    conf = acoes_config[ticker]
    price = market_data[ticker]['p'] or conf['price']
    
    if conf['tipo'] == 'Acao':
        # Lógica BR Clássica
        t_bazin = (conf['lpa'] * conf['payout']) / yield_alvo_br
        t_secundario = math.sqrt(max(0, 22.5 * conf['lpa'] * conf['vpa'])) # Graham
        nome_secundario = "Graham"
        peso_b = 0.8 if ticker in ['CXSE3.SA', 'SAPR4.SA'] else 0.5
        teto = (t_bazin * peso_b) + (t_secundario * (1 - peso_b))
        
    elif conf['tipo'] == 'REIT':
        # Lógica US REIT (Usa Dividendos e FFO, ignora VPA/LPA)
        t_bazin = conf['dpa'] / yield_alvo_us
        t_secundario = conf['ffo'] * 22.0 # Múltiplo de FFO Justo histórico p/ Data Centers
        nome_secundario = "FFO x22"
        peso_b = 0.5 # 50/50 entre yield esperado e valor do portfólio (FFO)
        teto = (t_bazin * peso_b) + (t_secundario * (1 - peso_b))
        
    margem = ((teto - price) / teto) * 100
    calculos.append({'t': ticker, 'm': margem, 'p': price, 'moeda': conf['moeda']})

    with cols[i]:
        st.markdown(f"""
            <div class="card-equity">
                <img src="{conf['logo']}" style="max-width:100px; height:40px; margin:auto; object-fit:contain;">
                <div class="label-text" style="margin-top:10px;">{ticker}</div>
                <div style="font-size:22px; font-weight:700;">{conf['moeda']} {price:.2f}</div>
                <span class="{"badge-buy" if margem > 0 else "badge-wait"}">
                    {margem:.1f}%
                </span>
                <div style="margin-top:15px; text-align: left; background: #fdfdfd; padding: 10px; border-radius: 10px; font-size:12px;">
                    Bazin: <b>{conf['moeda']} {t_bazin:.2f}</b><br>
                    {nome_secundario}: <b>{conf['moeda']} {t_secundario:.2f}</b><br>
                    Teto: <b style="color:#1e3a8a">{conf['moeda']} {teto:.2f}</b>
                </div>
            </div>
        """, unsafe_allow_html=True)

# 6. Aporte
st.markdown("---")
oports = [c for c in calculos if c['m'] > 0]
if oports and valor_aporte > 0:
    st.subheader("🎯 Sugestão de Aporte (Ações BR)")
    oports_br = [o for o in oports if o['moeda'] == 'R$']
    if oports_br:
        a_cols = st.columns(len(oports_br))
        for idx, c in enumerate(oports_br):
            qtd = (valor_aporte / len(oports_br)) // c['p']
            a_cols[idx].metric(f"Comprar {c['t'][:5]}", f"{int(qtd)} cotas", f"R$ {qtd*c['p']:.2f}")
    else:
        st.info("Nenhuma ação brasileira com margem de segurança no momento.")

# 7. Gráfico
st.markdown("<br>", unsafe_allow_html=True)
target = st.selectbox("Comparativo Histórico (Base 100):", list(acoes_config.keys()), index=5)
fig = go.Figure()
anos = {"1 Ano": 1, "2 Anos": 2, "5 Anos": 5, "10 Anos": 10}[periodo_texto]
data_limite = datetime.now() - timedelta(days=anos * 365)

for t in [target, 'BOVA11.SA', 'DIVO11.SA']:
    if t in market_data:
        df = market_data[t]['h'].copy()
        if not df.empty:
            df.index = df.index.tz_localize(None)
            df = df[df.index >= data_limite]
            if not df.empty:
                norm = (df['Close'] / df['Close'].iloc[0]) * 100
                fig.add_trace(go.Scatter(x=df.index, y=norm, name=t[:6], line=dict(width=2)))

fig.update_layout(
    template="plotly_white", 
    height=450, 
    margin=dict(l=0, r=0, t=10, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações da Página
LOGO_SIDEBAR = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Logo.png"
LOGO_HEADER = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Horizontal.png"

st.set_page_config(page_title="EquityDash Ultra v6.9", page_icon=LOGO_SIDEBAR, layout="wide")

# --- CSS Profissional ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .main-header { background-color: #20B2AA; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 30px; }
    .header-logo { width: 500px; height: auto; display: block; margin: 0 auto; }
    .card-equity { background: white; padding: 15px; border-radius: 15px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; height: 100%; display: flex; flex-direction: column; }
    .badge-buy { background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    .badge-wait { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    .label-text { color: #64748b; font-size: 10px; text-transform: uppercase; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.image(LOGO_SIDEBAR, use_container_width=True)
st.markdown(f'<div class="main-header"><img src="{LOGO_HEADER}" class="header-logo"></div>', unsafe_allow_html=True)

# 2. Ativos (AXIA6 atualizado para AXIA3.SA)
acoes_config = {
    'AXIA3.SA': {'tipo': 'Acao', 'cor': '#3bb54a', 'payout': 1.0, 'lpa': 0.70, 'vpa': 52.10, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png", 'moeda': 'R$'},
    'CPLE3.SA': {'tipo': 'Acao', 'cor': '#2d3e50', 'payout': 0.5, 'lpa': 0.85, 'vpa': 10.40, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png", 'moeda': 'R$'},
    'CXSE3.SA': {'tipo': 'Acao', 'cor': '#005ca9', 'payout': 0.9, 'lpa': 1.40, 'vpa': 4.10, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Caixa.png", 'moeda': 'R$'},
    'ITSA4.SA': {'tipo': 'Acao', 'cor': '#ec7000', 'payout': 0.4, 'lpa': 1.55, 'vpa': 8.90, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Itausa.png", 'moeda': 'R$'},
    'SAPR4.SA': {'tipo': 'Acao', 'cor': '#009fe3', 'payout': 0.5, 'lpa': 1.10, 'vpa': 6.80, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0dd7c40bf47a5487a468aeaca985451e8d24cc6a/Sanepar.PNG", 'moeda': 'R$'},
    'EQIX': {'tipo': 'REIT', 'cor': '#E31C23', 'dpa': 17.04, 'ffo': 34.80, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/02b13adcb14ea6c1530085e2af5a531738423aec/Equinix_Logo.png", 'moeda': 'US$'}
}

# 3. Sidebar
st.sidebar.title("⚙️ Filtros de Valuation")
yield_valor_br = st.sidebar.select_slider("Yield Alvo BR %", options=[round(x*0.1,1) for x in range(60,125,5)], value=6.0)
yield_alvo_br = yield_valor_br / 100
yield_alvo_us = 0.025 

# 4. Engine de Dados
@st.cache_data(ttl=600)
def get_data():
    tickers = list(acoes_config.keys()) + ['BOVA11.SA', 'DIVO11.SA']
    results = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            h = tk.history(period="5y")
            results[t] = {'p': h['Close'].iloc[-1] if not h.empty else None, 'h': h}
        except: results[t] = {'p': None, 'h': pd.DataFrame()}
    return results

market_data = get_data()

# 5. Cards com Layout Responsivo (Grade 4 Colunas)
ativos_list = list(acoes_config.items())
for i in range(0, len(ativos_list), 4):
    cols = st.columns(4)
    for j, (ticker, conf) in enumerate(ativos_list[i:i+4]):
        price = market_data[ticker]['p'] or 0
        
        # Lógica Valuation
        if conf['tipo'] == 'Acao':
            teto = (conf['lpa'] * conf['payout']) / yield_alvo_br
        else:
            teto = conf['dpa'] / yield_alvo_us
            
        margem = ((teto - price) / teto) * 100 if teto > 0 else 0
        
        with cols[j]:
            st.markdown(f"""
                <div class="card-equity">
                    <img src="{conf['logo']}" style="max-width:80px; height:30px; margin:auto;">
                    <div class="label-text">{ticker}</div>
                    <div style="font-size:18px; font-weight:700;">{conf['moeda']} {price:.2f}</div>
                    <span class="{"badge-buy" if margem > 0 else "badge-wait"}">{margem:.1f}%</span>
                    <div style="margin-top:10px; font-size:11px;">Teto: <b>{conf['moeda']} {teto:.2f}</b></div>
                </div>
            """, unsafe_allow_html=True)
