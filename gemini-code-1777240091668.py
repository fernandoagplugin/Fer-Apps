import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configurações da Página
st.set_page_config(page_title="App Preço Teto - Ações BR", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .card { padding: 15px; border-radius: 10px; background-color: white; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .proj-text { color: #007bff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração das Ações
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout_est': 0.90},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout_est': 0.35},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout_est': 0.50},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout_est': 0.25}
}

# 3. Sidebar - Projeções
st.sidebar.header("⚙️ Configurações Base")
yield_selecionado = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.09], format_func=lambda x: f"{int(x*100)}%")

st.sidebar.header("🔮 Projeções de Lucro (LPA)")
lpa_projs = {}
for ticker in acoes_config:
    lpa_projs[ticker] = st.sidebar.number_input(f"LPA Estimado {ticker.replace('.SA','')}", value=1.20, step=0.10)

if st.sidebar.button("🔄 Atualizar Tudo"):
    st.cache_data.clear()
    st.rerun()

# 4. Busca de Dados
@st.cache_data(ttl=3600)
def buscar_dados(tickers):
    resultados = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="1y")
            if hist.empty: continue
            
            resultados[t] = {
                'preco_atual': hist['Close'].iloc[-1],
                'dpa_hist': tk.info.get('trailingAnnualDividendRate', 0) or 0.80,
                'lpa_atual': tk.info.get('trailingEps', 0) or 1.0,
                'historico': hist
            }
        except: continue
    return resultados

dados_br = buscar_dados(list(acoes_config.keys()))

# 5. Dashboard
st.title("📊 Preço Teto: Histórico vs. Projetivo")

if dados_br:
    cols = st.columns(4)
    for i, (ticker, config) in enumerate(acoes_config.items()):
        if ticker in dados_br:
            with cols[i]:
                d = dados_br[ticker]
                
                # Teto Histórico (Bazin)
                teto_hist = d['dpa_hist'] / yield_selecionado
                
                # Teto Projetivo
                dpa_proj = lpa_projs[ticker] * config['payout_est']
                teto_proj = dpa_proj / yield_selecionado
                
                margem_proj = ((teto_proj - d['preco_atual']) / teto_proj) * 100
                cor_m = "#28a745" if margem_proj > 0 else "#dc3545"

                st.markdown(f"""
                    <div class="card" style="border-top: 8px solid {config['cor']};">
                        <h3 style="margin:0;">{ticker.replace('.SA', '')}</h3>
                        <hr>
                        <p style="margin:0; font-size:0.9em;">Preço Atual: <b>R$ {d['preco_atual']:.2f}</b></p>
                        <p style="margin:0; font-size:0.9em;">Teto Histórico: <b>R$ {teto_hist:.2f}</b></p>
                        <p style="margin:0; font-size:1em;" class="proj-text">Teto Projetivo: R$ {teto_proj:.2f}</p>
                        <div style="background-color:{cor_m}; color:white; text-align:center; border-radius:5px; margin-top:10px;">
                            Margem Proj: {margem_proj:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # 6. Gráfico de Tendência (Mantido)
    st.markdown("---")
    st.subheader("📈 Análise de Tendência")
    selecionado = st.selectbox("Ver gráfico detalhado:", list(dados_br.keys()))
    df_plot = dados_br[selecionado]['historico']
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], name='Preço', line=dict(color=acoes_config[selecionado]['cor'])))
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'].rolling(50).mean(), name='Média 50d', line=dict(color='gray', dash='dot')))
    st.plotly_chart(fig, use_container_width=True)
