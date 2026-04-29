import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configurações da Página
st.set_page_config(page_title="EquityDash | Projeções", layout="wide", initial_sidebar_state="expanded")

# --- CSS AVANÇADO (Visual Profissional) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; }
    
    /* Header com Gradiente */
    .main-header { 
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Cards Modernos com Efeito Hover */
    .card-equity {
        background: white;
        padding: 25px;
        border-radius: 20px;
        border: 1px solid #eef2f6;
        box-shadow: 0 10px 25px rgba(0,0,0,0.02);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .card-equity:hover { 
        transform: translateY(-5px); 
        box-shadow: 0 15px 35px rgba(0,0,0,0.08); 
        border-color: #3b82f6;
    }
    
    /* Etiquetas de Status */
    .badge-positive { background-color: #dcfce7; color: #15803d; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; }
    .badge-negative { background-color: #fee2e2; color: #b91c1c; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; }
    
    .logo-img { height: 55px; object-fit: contain; margin-bottom: 15px; }
    .price-text { font-size: 26px; font-weight: 700; color: #1e293b; margin: 10px 0; }
    .label-text { color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# Top Bar
st.markdown('<div class="main-header"><h1>EquityDash 2026</h1><p>Inteligência em Dividendos & Preço Teto • por Fer</p></div>', unsafe_allow_html=True)

# 2. Configuração de Ativos
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout': 1.0, 'fallback': 0.65, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout': 0.5, 'fallback': 0.85, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout': 0.9, 'fallback': 1.40, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout': 0.4, 'fallback': 1.55, 'logo': f"{base_raw}Itausa.png"}
}

# 3. Sidebar
st.sidebar.title("⚙️ Filtros")
yield_valor = st.sidebar.select_slider("Objetivo de Yield Anual", options=[6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0], value=6.0)
yield_alvo = yield_valor / 100

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Sincronizar Mercado", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 4. Data Engine
@st.cache_data(ttl=600)
def fetch_data(tickers):
    data = {}
    for t in tickers + ['BOVA11.SA', 'DIVO11.SA']:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="10y")
            if hist.empty: continue
            data[t] = {
                'price': hist['Close'].iloc[-1],
                'lpa': tk.info.get('forwardEps') or tk.info.get('trailingEps'),
                'hist': hist
            }
        except: continue
    return data

market_data = fetch_data(list(acoes_config.keys()))

# 5. Grid de Cards
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in market_data:
        d = market_data[ticker]
        lpa = d['lpa'] if d['lpa'] and d['lpa'] > 0 else conf['fallback']
        dpa = lpa * conf['payout']
        teto = dpa / yield_alvo
        margem = ((teto - d['price']) / teto) * 100
        
        status_class = "badge-positive" if margem > 0 else "badge-negative"
        status_text = "OPORTUNIDADE" if margem > 0 else "ACIMA DO TETO"

        with cols[i]:
            st.markdown(f"""
                <div class="card-equity">
                    <div>
                        <img src="{conf['logo']}" class="logo-img">
                        <div class="label-text">{ticker}</div>
                        <div class="price-text">R$ {d['price']:.2f}</div>
                        <div style="margin-bottom: 20px;">
                            <span class="{status_class}">{status_text}: {margem:.1f}%</span>
                        </div>
                    </div>
                    <div>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 15px 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <div style="text-align: left;">
                                <div class="label-text">Preço Teto</div>
                                <div style="font-weight: 700; color: {conf['cor']}; font-size: 16px;">R$ {teto:.2f}</div>
                            </div>
                            <div style="text-align: right;">
                                <div class="label-text">Div. Est.</div>
                                <div style="font-weight: 700; color: #1e293b; font-size: 16px;">R$ {dpa:.2f}</div>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# 6. Gráfico de Performance (Com Correção de Legenda e Barra de Ferramentas)
st.markdown("<br>", unsafe_allow_html=True)
with st.container():
    st.markdown('<div style="background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.02); border: 1px solid #eef2f6;">', unsafe_allow_html=True)
    st.subheader("📊 Comparativo de Performance (10 Anos)")
    target = st.selectbox("Ativo para análise detalhada:", list(acoes_config.keys()), index=3, format_func=lambda x: x[:5])
    
    if target in market_data:
        fig = go.Figure()
        d_target = market_data[target]['hist']
        norm_target = (d_target['Close'] / d_target['Close'].iloc[0]) * 100
        
        fig.add_trace(go.Scatter(x=d_target.index, y=norm_target, name=f"<b>{target[:5]}</b>", 
                                 line=dict(color=acoes_config[target]['cor'], width=3.5)))
        
        for idx, color, name in [('DIVO11.SA', '#f1c40f', 'DIVO11'), ('BOVA11.SA', '#95a5a6', 'BOVA11')]:
            if idx in market_data:
                d_idx = market_data[idx]['hist']
                norm_idx = (d_idx['Close'] / d_idx['Close'].iloc[0]) * 100
                fig.add_trace(go.Scatter(x=d_idx.index, y=norm_idx, name=name, line=dict(width=1.5, dash='dot', color=color)))

        fig.update_layout(
            template="plotly_white",
            hovermode="x unified",
            height=500,
            yaxis=dict(ticksuffix="%", gridcolor='#f0f0f0'),
            xaxis=dict(gridcolor='#f0f0f0'),
            # SOLUÇÃO PARA O CONFLITO: Legenda abaixo do gráfico
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            ),
            margin=dict(l=0, r=0, t=20, b=100), # Espaço extra embaixo para a legenda
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        # Desativa a barra de ferramentas para garantir visual limpo
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown('</div>', unsafe_allow_html=True)
