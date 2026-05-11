import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações da Página
LOGO_SIDEBAR = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Logo.png"
LOGO_HEADER = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Horizontal.png"

st.set_page_config(page_title="EquityDash Ultra v6.6", page_icon=LOGO_SIDEBAR, layout="wide")

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

# 2. Ativos e Parâmetros (Adicionado EQIX)
acoes_config = {
    'AXIA6.SA': {'cor': '#3bb54a', 'payout': 1.0, 'lpa': 6.80, 'vpa': 52.10, 'price': 68.65, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png", 'moeda': 'R$'},
    'CPLE3.SA': {'cor': '#2d3e50', 'payout': 0.5, 'lpa': 0.85, 'vpa': 10.40, 'price': 15.90, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png", 'moeda': 'R$'},
    'CXSE3.SA': {'cor': '#005ca9', 'payout': 0.9, 'lpa': 1.40, 'vpa': 4.10, 'price': 18.09, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Caixa.png", 'moeda': 'R$'},
    'ITSA4.SA': {'cor': '#ec7000', 'payout': 0.4, 'lpa': 1.55, 'vpa': 8.90, 'price': 13.92, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Itausa.png", 'moeda': 'R$'},
    'SAPR4.SA': {'cor': '#009fe3', 'payout': 0.5, 'lpa': 1.10, 'vpa': 6.80, 'price': 7.88, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0dd7c40bf47a5487a468aeaca985451e8d24cc6a/Sanepar.PNG", 'moeda': 'R$'},
    'EQIX': {'cor': '#E31C23', 'payout': 0.45, 'lpa': 10.50, 'vpa': 135.00, 'price': 800.00, 'logo': "https://logo.clearbit.com/equinix.com", 'moeda': 'US$'}
}

# 3. Sidebar
st.sidebar.title("💰 Gestão de Capital")
valor_aporte = st.sidebar.number_input("Valor Investimento (R$)", min_value=0.0, value=1000.0)
yield_valor = st.sidebar.select_slider("Yield Alvo %", options=[round(x*0.1,1) for x in range(60,125,5)], value=6.0)
yield_alvo = yield_valor / 100
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

# 5. Cards (Ajustado para 6 Colunas)
calculos = []
cols = st.columns(len(acoes_config))
for i, ticker in enumerate(acoes_config.keys()):
    conf = acoes_config[ticker]
    price = market_data[ticker]['p'] or conf['price']
    
    # Lógica de Valuation (EQIX usa yield alvo ajustado para mercado US se necessário, mas mantivemos o slider para controle)
    t_bazin = (conf['lpa'] * conf['payout']) / yield_alvo
    t_graham = math.sqrt(max(0, 22.5 * conf['lpa'] * conf['vpa']))
    
    # Pesos (Equinix segue peso 50/50 por padrão de crescimento/valor)
    peso_b = 0.8 if ticker in ['CXSE3.SA', 'SAPR4.SA'] else 0.5
    teto = (t_bazin * peso_b) + (t_graham * (1 - peso_b))
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
                    Graham: <b>{conf['moeda']} {t_graham:.2f}</b><br>
                    Teto: <b style="color:#1e3a8a">{conf['moeda']} {teto:.2f}</b>
                </div>
            </div>
        """, unsafe_allow_html=True)

# 6. Aporte
st.markdown("---")
oports = [c for c in calculos if c['m'] > 0]
if oports and valor_aporte > 0:
    st.subheader("🎯 Sugestão de Aporte (Ações BR)")
    # Filtrar apenas ativos em R$ para sugestão de aporte simples
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

# Lista de ativos para o gráfico (Ativo selecionado + Benchmarks)
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
