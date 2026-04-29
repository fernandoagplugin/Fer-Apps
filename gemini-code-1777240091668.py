import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configurações da Página
st.set_page_config(page_title="Preço Teto Automático", layout="wide")

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

# 2. Configuração de Ativos (Dados Base de Segurança)
base_raw = "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/"
acoes_config = {
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout': 1.0, 'lpa_fallback': 0.65, 'logo': f"{base_raw}AXIA.png"},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout': 0.5, 'lpa_fallback': 0.85, 'logo': f"{base_raw}COPEL.png"},
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout': 0.9, 'lpa_fallback': 1.40, 'logo': f"{base_raw}Caixa.png"},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout': 0.4, 'lpa_fallback': 1.55, 'logo': f"{base_raw}Itausa.png"}
}

# 3. Busca de Dados (Preço, Índices e Consenso)
@st.cache_data(ttl=300)
def buscar_dados_mercado(tickers):
    todos = tickers + ['BOVA11.SA', 'DIVO11.SA']
    dados = {}
    for t in todos:
        try:
            tk = yf.Ticker(t)
            # Busca histórico para gráfico e preço atual
            hist = tk.history(period="10y")
            if hist.empty: continue
            
            # Busca LPA projetado (Consenso)
            info = tk.info
            lpa_proj = info.get('forwardEps') or info.get('trailingEps')
            
            dados[t] = {
                'preco': hist['Close'].iloc[-1],
                'lpa_mercado': lpa_proj,
                'datas': hist.index,
                'hist_norm': (hist['Close'] / hist['Close'].iloc[0]) * 100
            }
        except: continue
    return dados

dados_mercado = buscar_dados_mercado(list(acoes_config.keys()))

# 4. Sidebar - Parâmetros Diretos
st.sidebar.header("⚙️ Configurações")

# Yield agora atualiza instantaneamente (sem precisar de Update para o cálculo)
yield_valor = st.sidebar.slider("Yield Mínimo Desejado (%)", 6.0, 12.0, value=6.0, step=0.5, format="%.1f")
yield_alvo = yield_valor / 100

if st.sidebar.button("🔄 Update (Preços e Lucros)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.info("As projeções de Lucro (LPA) e Payout são obtidas automaticamente via Consenso de Mercado e políticas vigentes das empresas.")

# 5. Interface de Cards
cols = st.columns(4)
for i, (ticker, conf) in enumerate(acoes_config.items()):
    if ticker in dados_mercado:
        d = dados_mercado[ticker]
        
        # Lógica: Usa Consenso de Mercado. Se falhar, usa o valor de segurança (fallback).
        lpa_usado = d['lpa_mercado'] if d['lpa_mercado'] and d['lpa_mercado'] > 0 else conf['lpa_fallback']
        payout_usado = conf['payout']
        
        dpa = lpa_usado * payout_usado
        teto = dpa / yield_alvo if yield_alvo > 0 else 0
        margem = ((teto - d['preco']) / teto) * 100 if teto > 0 else -100
        cor = "#28a745" if margem > 0 else "#dc3545"
        
        with cols[i]:
            st.markdown(f"""
                <div class="card" style="border-top: 5px solid {conf['cor']};">
                    <div class="logo-container"><img src="{conf['logo']}" class="logo-img"></div>
                    <b>{ticker[:5]}</b><br>
                    <p style="margin:5px 0; font-size:14px;">Preço Atual: <b>R$ {d['preco']:.2f}</b></p>
                    <p style="margin:5px 0; font-size:14px;">LPA Est.: <b>R$ {lpa_usado:.2f}</b></p>
                    <p style="margin:5px 0; font-size:14px;">Div. Projetado: <b>R$ {dpa:.2f}</b></p>
                    <p style="font-size:18px; color:{cor}; margin:10px 0;"><b>Teto: R$ {teto:.2f}</b></p>
                    <div style="background:{cor}; color:white; padding:5px; border-radius:5px; width:100%;"><b>{margem:.1f}%</b></div>
                </div>
            """, unsafe_allow_html=True)

# 6. Gráfico Comparativo
st.markdown("---")
st.subheader("📊 Performance Acumulada vs Índices (10 Anos)")
ticker_sel = st.selectbox("Selecione para comparar:", list(acoes_config.keys()), format_func=lambda x: x[:5])

if ticker_sel in dados_mercado:
    d = dados_mercado[ticker_sel]
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=d['datas'], y=d['hist_norm'], name=f"{ticker_sel[:5]}", 
                             line=dict(color=acoes_config[ticker_sel]['cor'], width=3)))
    
    if 'DIVO11.SA' in dados_mercado:
        fig.add_trace(go.Scatter(x=dados_mercado['DIVO11.SA']['datas'], y=dados_mercado['DIVO11.SA']['hist_norm'], 
                                 name='DIVO11', line=dict(color='#f1c40f', width=2, dash='dash')))
    
    if 'BOVA11.SA' in dados_mercado:
        fig.add_trace(go.Scatter(x=dados_mercado['BOVA11.SA']['datas'], y=dados_mercado['BOVA11.SA']['hist_norm'], 
                                 name='BOVA11', line=dict(color='#95a5a6', width=2, dash='dot')))

    fig.update_layout(template="plotly_white", hovermode="x unified", height=450, margin=dict(l=0, r=0, t=30, b=0),
                      yaxis=dict(ticksuffix="%"), legend=dict(orientation="h", y=1.1, x=1, xanchor='right'))
    st.plotly_chart(fig, use_container_width=True)
