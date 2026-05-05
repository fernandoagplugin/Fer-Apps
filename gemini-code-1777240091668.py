import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações da Página
LOGO_SIDEBAR = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Logo.png"
LOGO_HEADER = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Horizontal.png"

st.set_page_config(
    page_title="EquityDash Ultra v6.5", 
    page_icon=LOGO_SIDEBAR,
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- Estilização CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; background-color: #f8f9fa; }}
    .main-header {{ background-color: #20B2AA; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
    .header-logo {{ width: 500px; height: auto; display: block; margin: 0 auto; }}
    .card-equity {{ background: white; padding: 20px; border-radius: 20px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }}
    .badge-buy {{ background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }}
    .badge-wait {{ background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }}
    .label-text {{ color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
    .weight-info {{ font-size: 9px; color: #94a3b8; margin-top: 5px; font-style: italic; }}
    </style>
    """, unsafe_allow_html=True)

st.sidebar.image(LOGO_SIDEBAR, use_container_width=True)
st.markdown(f'<div class="main-header"><img src="{LOGO_HEADER}" class="header-logo"></div>', unsafe_allow_html=True)

# 2. Configuração de Ativos
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'cor': '#3bb54a', 'payout': 1.0, 'f_lpa': 6.80, 'f_vpa': 52.10, 'f_price': 68.65, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'cor': '#2d3e50', 'payout': 0.5, 'f_lpa': 0.85, 'f_vpa': 10.40, 'f_price': 15.90, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'cor': '#005ca9', 'payout': 0.9, 'f_lpa': 1.40, 'f_vpa': 4.10, 'f_price': 18.09, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'cor': '#ec7000', 'payout': 0.4, 'f_lpa': 1.55, 'f_vpa': 8.90, 'f_price': 13.92, 'logo': f"{base_raw}Itausa.png"},
    'SAPR4.SA': {'cor': '#009fe3', 'payout': 0.5, 'f_lpa': 1.10, 'f_vpa': 6.80, 'f_price': 7.88, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0dd7c40bf47a5487a468aeaca985451e8d24cc6a/Sanepar.PNG"}
}

# 3. Sidebar
st.sidebar.title("💰 Gestão de Capital")
valor_aporte = st.sidebar.number_input("Valor para investir (R$)", min_value=0.0, value=1000.0, step=100.0)
st.sidebar.markdown("---")
st.sidebar.title("⚙️ Filtros")
yield_valor = st.sidebar.select_slider("Yield Alvo (Bazin) %", options=[round(x * 0.1, 1) for x in range(60, 125, 5)], value=6.0)
yield_alvo = yield_valor / 100
st.sidebar.subheader("📅 Horizonte Gráfico")
periodo_map = {"1 Ano": 1, "2 Anos": 2, "5 Anos": 5, "10 Anos": 10}
periodo_texto = st.sidebar.radio("Período:", list(periodo_map.keys()), index=2)

if st.sidebar.button("🔄 Atualizar Mercado", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 4. Busca de Dados
@st.cache_data(ttl=600)
def fetch_market_data(tickers):
    data = {}
    for t in tickers + ['BOVA11.SA', 'DIVO11.SA']:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="10y")
            info = tk.info
            data[t] = {
                'price': hist['Close'].iloc[-1] if not hist.empty else None,
                'lpa': info.get('forwardEps') or info.get('trailingEps'),
                'vpa': info.get('bookValue'),
                'hist': hist
            }
        except: data[t] = {'price': None, 'lpa': None, 'vpa': None, 'hist': pd.DataFrame()}
    return data

market_data = fetch_market_data(list(acoes_config.keys()))

# 5. Cards Principais
calculos_final = []
cols = st.columns(len(acoes_config))

for i, (ticker, conf) in enumerate(acoes_config.items()):
    d = market_data.get(ticker, {})
    price = d.get('price') or conf['f_price']
    lpa = d.get('lpa') if (d.get('lpa') and d.get('lpa') > 2.0 if ticker == 'AXIA6.SA' else 0.1) else conf['f_lpa']
    vpa = d.get('vpa') if (d.get('vpa') and d.get('vpa') > 10.0 if ticker == 'AXIA6.SA' else 0.1) else conf['f_vpa']
    
    t_bazin = (lpa * conf['payout']) / yield_alvo
    t_graham = math.sqrt(max(0, 22.5 * lpa * vpa))
    
    if ticker in ['CXSE3.SA', 'SAPR4.SA']:
        teto = (t_bazin * 0.8) + (t_graham * 0.2)
        label_peso = "80% Bazin / 20% Graham"
    else:
        teto = (t_bazin + t_graham) / 2
        label_peso = "50% Bazin / 50% Graham"
    
    margem = ((teto - price) / teto) * 100
    calculos_final.append({'ticker': ticker, 'margem': margem, 'price': price})

    with cols[i]:
        st.markdown(f"""
            <div class="card-equity">
                <div>
                    <img src="{conf['logo']}" style="max-width:100px; height:40px; object-fit:contain;">
                    <div class="label-text" style="margin-top:10px;">{ticker}</div>
                    <div style="font-size:22px; font-weight:700;">R$ {price:.2f}</div>
                    <span class="{"badge-buy" if margem > 0 else "badge-wait"}">
                        {"COMPRA" if margem > 0 else "AGUARDAR"}: {margem:.1f}%
                    </span>
                    <div class="weight-info">{label_peso}</div>
                </div>
                <div style="margin-top:15px; text-align: left; background: #fdfdfd; padding: 10px; border-radius: 10px;">
                    <div style="display:flex; justify-content:space-between"><span class="label-text">Bazin</span><b>R$ {t_bazin:.2f}</b></div>
                    <div style="display:flex; justify-content:space-between"><span class="label-text">Graham</span><b>R$ {t_graham:.2f}</b></div>
                    <hr style="margin: 8px 0; border: 0; border-top: 1px solid #eee;">
                    <div style="display:flex; justify-content:space-between; color:#1e3a8a"><span class="label-text" style="color:#1e3a8a">Teto Híbrido</span><b>R$ {teto:.2f}</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# 6. Sugestão de Aporte
st.markdown("---")
st.subheader("🎯 Sugestão de Aporte")
oports = [c for c in calculos_final if c['margem'] > 0]
if oports and valor_aporte > 0:
    s_cols = st.columns(len(oports))
    for idx, c in enumerate(oports):
        qtd = (valor_aporte / len(oports)) // c['price']
        s_cols[idx].metric(f"Comprar {c['ticker'][:5]}", f"{int(qtd)} cotas", f"Total R$ {qtd*c['price']:.2f}")
else:
    st.info("Aguardando margem de segurança média para sugerir alocação.")

# 7. Gráfico Comparativo (Área Corrigida)
st.markdown("<br>", unsafe_allow_html=True)
with st.container():
    st.markdown('<div style="background: white; padding: 25px; border-radius: 20px; border: 1px solid #eef2f6;">', unsafe_allow_html=True)
    target = st.selectbox("Histórico Comparativo:", list(acoes_config.keys()), index=4)
    
    fig = go.Figure()
    anos = periodo_map[periodo_texto]
    data_limite = datetime.now() - timedelta(days=anos * 365)
    
    def add_trace(t, is_main=False):
        if t in market_data and not market_data[t]['hist'].empty:
            df = market_data[t]['hist'].copy()
            df.index = df.index.tz_localize(None)
            df_f = df[df.index >= data_limite]
            if not df_f.empty:
                norm = (df_f['Close'] / df_f['Close'].iloc[0]) * 100
                fig.add_trace(go.Scatter(
                    x=df_f.index, y=norm, name=t[:6], 
                    line=dict(color=acoes_config[t]['cor'] if t in acoes_config else '#95a5a6', 
                    width=3 if is_main else 1.5, dash=None if is_main else 'dot')
                ))

    add_trace(target, True)
    for idx in ['DIVO11.SA', 'BOVA11.SA']:
        add_trace(idx)

    fig.update_layout(
        template="plotly_white", hovermode="x unified", height=450, 
        margin=dict(l=0, r=0, t=10, b=80),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
