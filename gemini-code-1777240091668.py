import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math

# 1. Configurações da Página
st.set_page_config(page_title="EquityDash Ultra", layout="wide", initial_sidebar_state="expanded")

# --- CSS AVANÇADO (Visual Moderno) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    .main-header { 
        background: linear-gradient(90deg, #0f172a 0%, #1e3a8a 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px;
    }
    .card-equity {
        background: white; padding: 20px; border-radius: 20px; border: 1px solid #eef2f6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03); transition: all 0.3s ease;
        text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between;
    }
    .card-equity:hover { transform: translateY(-5px); box-shadow: 0 12px 24px rgba(0,0,0,0.08); border-color: #3b82f6; }
    .badge-buy { background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    .badge-wait { background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }
    .label-text { color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>EquityDash Ultra</h1><p>Valuation Profissional & Alocação • por Fer</p></div>', unsafe_allow_html=True)

# 2. Configuração de Ativos
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'cor': '#3bb54a', 'payout': 1.0, 'fallback_lpa': 0.65, 'fallback_vpa': 5.20, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'cor': '#2d3e50', 'payout': 0.5, 'fallback_lpa': 0.85, 'fallback_vpa': 10.40, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'cor': '#005ca9', 'payout': 0.9, 'fallback_lpa': 1.40, 'fallback_vpa': 4.10, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'cor': '#ec7000', 'payout': 0.4, 'fallback_lpa': 1.55, 'fallback_vpa': 8.90, 'logo': f"{base_raw}Itausa.png"}
}

# 3. Sidebar
st.sidebar.title("💰 Gestão de Capital")
valor_aporte = st.sidebar.number_input("Valor para investir (R$)", min_value=0.0, value=1000.0, step=100.0)

st.sidebar.markdown("---")
st.sidebar.title("⚙️ Filtros")
# CORREÇÃO 3: Seleção de Yield de 0.5 em 0.5
opcoes_yield = [round(x * 0.1, 1) for x in range(60, 125, 5)] # Gera [6.0, 6.5, 7.0... 12.0]
yield_valor = st.sidebar.select_slider("Yield Alvo (Bazin) %", options=opcoes_yield, value=6.0)
yield_alvo = yield_valor / 100

st.sidebar.subheader("📅 Horizonte Gráfico")
periodo_map = {"1 Ano": 1, "2 Anos": 2, "5 Anos": 5, "10 Anos": 10}
periodo_texto = st.sidebar.radio("Período:", list(periodo_map.keys()), index=2)

# CORREÇÃO 2: Botão de Atualizar Mercado de volta
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar Mercado Agora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 4. Engine de Dados
@st.cache_data(ttl=600)
def fetch_market_data(tickers):
    data = {}
    for t in tickers + ['BOVA11.SA', 'DIVO11.SA']:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="10y")
            if hist.empty: continue
            data[t] = {
                'price': hist['Close'].iloc[-1],
                'lpa': tk.info.get('forwardEps') or tk.info.get('trailingEps'),
                'vpa': tk.info.get('bookValue'),
                'hist': hist
            }
        except: continue
    return data

market_data = fetch_market_data(list(acoes_config.keys()))

# 5. Processamento dos Cards
calculos_ativos = []
cols = st.columns(4)

for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in market_data:
        d = market_data[ticker]
        lpa = d['lpa'] if d['lpa'] and d['lpa'] > 0 else conf['fallback_lpa']
        vpa = d['vpa'] if d['vpa'] and d['vpa'] > 0 else conf['fallback_vpa']
        
        teto_bazin = (lpa * conf['payout']) / yield_alvo
        teto_graham = math.sqrt(max(0, 22.5 * lpa * vpa)) if lpa > 0 and vpa > 0 else 0
        
        teto_final = (teto_bazin + teto_graham) / 2 if teto_graham > 0 else teto_bazin
        margem = ((teto_final - d['price']) / teto_final) * 100 if teto_final > 0 else -100
        
        calculos_ativos.append({'ticker': ticker, 'margem': margem, 'price': d['price']})

        with cols[i]:
            status_css = "badge-buy" if margem > 0 else "badge-wait"
            status_txt = "COMPRA" if margem > 0 else "AGUARDAR"
            st.markdown(f"""
                <div class="card-equity">
                    <div>
                        <img src="{conf['logo']}" class="logo-img">
                        <div class="label-text">{ticker}</div>
                        <div class="price-text">R$ {d['price']:.2f}</div>
                        <span class="{status_css}">{status_txt}: {margem:.1f}%</span>
                    </div>
                    <div style="margin-top:15px; text-align: left; background: #fdfdfd; padding: 10px; border-radius: 10px;">
                        <div style="display:flex; justify-content:space-between"><span class="label-text">Bazin</span><b>R$ {teto_bazin:.2f}</b></div>
                        <div style="display:flex; justify-content:space-between"><span class="label-text">Graham</span><b>R$ {teto_graham:.2f}</b></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# 6. Sugestão de Alocação
st.markdown("---")
st.subheader("🎯 Sugestão de Alocação")
oportunidades = [c for c in calculos_ativos if c['margem'] > 0]

if oportunidades and valor_aporte > 0:
    sugestao_cols = st.columns(len(oportunidades))
    for idx, c in enumerate(oportunidades):
        fatia = valor_aporte / len(oportunidades)
        cotas = fatia // c['price']
        with sugestao_cols[idx]:
            st.metric(f"Comprar {c['ticker'][:5]}", f"{int(cotas)} cotas", f"R$ {cotas*c['price']:.2f}")
else:
    st.info("Nenhuma oportunidade de compra identificada com margem de segurança positiva.")

# 7. Gráfico Comparativo (CORREÇÃO 1: Fuso Horário)
st.markdown("<br>", unsafe_allow_html=True)
with st.container():
    st.markdown('<div style="background: white; padding: 30px; border-radius: 20px; border: 1px solid #eef2f6;">', unsafe_allow_html=True)
    target = st.selectbox("Analisar Histórico de:", list(acoes_config.keys()), index=3)
    
    if target in market_data:
        fig = go.Figure()
        anos = periodo_map[periodo_texto]
        
        def plot_series(t, is_main=False):
            df = market_data[t]['hist'].copy()
            # Remove o fuso horário para permitir comparação segura com datetime.now()
            df.index = df.index.tz_localize(None)
            
            data_corte = datetime.now() - timedelta(days=anos * 365)
            df_f = df[df.index >= data_corte]
            
            if not df_f.empty:
                norm = (df_f['Close'] / df_f['Close'].iloc[0]) * 100
                color = acoes_config[t]['cor'] if t in acoes_config else ('#f1c40f' if 'DIVO' in t else '#95a5a6')
                fig.add_trace(go.Scatter(x=df_f.index, y=norm, name=t[:6], 
                                         line=dict(color=color, width=3 if is_main else 1.5, dash=None if is_main else 'dot')))

        plot_series(target, is_main=True)
        for index_ticker in ['DIVO11.SA', 'BOVA11.SA']:
            if index_ticker in market_data: plot_series(index_ticker)

        fig.update_layout(template="plotly_white", hovermode="x unified", height=450,
                          legend=dict(orientation="h", yanchor="top", y=-0.2, x=0.5, xanchor="center"),
                          margin=dict(l=0, r=0, t=10, b=100))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)
