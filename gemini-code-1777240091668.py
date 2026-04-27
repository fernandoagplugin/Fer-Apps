import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configurações Iniciais
st.set_page_config(page_title="App Preço Teto Blindado", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .card { padding: 15px; border-radius: 10px; background-color: white; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Definição das Ações e Parâmetros Base
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'payout': 0.90},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'payout': 0.35},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'payout': 0.50},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'payout': 0.25}
}

# 3. Sidebar - Ajustes de Projeção
st.sidebar.header("⚙️ Configurações")
yield_alvo = st.sidebar.selectbox("Yield Desejado", [0.06, 0.08, 0.09], index=1, format_func=lambda x: f"{int(x*100)}%")

st.sidebar.markdown("---")
st.sidebar.header("🔮 Ajustar LPA Estimado")
lpa_manual = {}
for ticker in acoes_config:
    # Valor padrão baseado em estimativas de mercado para 2024/2025
    val_padrao = 1.30 if "CXSE" in ticker else 1.15
    lpa_manual[ticker] = st.sidebar.number_input(f"LPA {ticker[:5]}", value=val_padrao, step=0.05)

if st.sidebar.button("🔄 Atualizar Cotações"):
    st.cache_data.clear()
    st.rerun()

# 4. Busca de Dados (Yahoo Finance - Mais estável que Scraping)
@st.cache_data(ttl=3600)
def buscar_cotacoes(tickers):
    dados = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            # Tenta pegar o preço atual
            info = tk.info
            preco = info.get('currentPrice') or info.get('regularMarketPrice')
            
            # Se falhar o info, pega pelo histórico
            if not preco:
                hist = tk.history(period="1d")
                preco = hist['Close'].iloc[-1]
                
            dados[t] = {'preco': preco, 'hist': tk.history(period="1y")}
        except:
            dados[t] = {'preco': 0.01, 'hist': pd.DataFrame()}
    return dados

dados_mercado = buscar_cotacoes(list(acoes_config.keys()))

# 5. Dashboard
st.title("📈 Preço Teto: Projeção de Dividendos")

cols = st.columns(4)
for i, (ticker, config) in enumerate(acoes_config.items()):
    with cols[i]:
        d = dados_mercado.get(ticker)
        p_atual = d['preco']
        
        # CÁLCULO: LPA Estimado (Lateral) * Payout / Yield
        dpa_projetado = lpa_manual[ticker] * config['payout']
        teto = dpa_projetado / yield_alvo
        
        # Margem de Segurança
        margem = ((teto - p_atual) / teto) * 100 if teto > 0 else 0
        cor_m = "#28a745" if margem > 0 else "#dc3545"

        st.markdown(f"""
            <div class="card" style="border-top: 8px solid {config['cor']};">
                <h3 style="margin:0;">{ticker.replace('.SA', '')}</h3>
                <p style="color:gray; font-size:0.8em; margin:0;">{config['nome']}</p>
                <hr>
                <small>Preço Atual:</small> <b>R$ {p_atual:.2f}</b><br>
                <small>LPA Est.:</small> <b>R$ {lpa_manual[ticker]:.2f}</b><br>
                <small>Dividendos Est.:</small> <b>R$ {dpa_projetado:.2f}</b><br>
                <p style="margin-top:10px; margin-bottom:5px;">Preço Teto:</p>
                <b style="font-size:1.4em; color:#007bff;">R$ {teto:.2f}</b>
                <div style="margin-top:10px; padding:5px; background-color:{cor_m}; color:white; text-align:center; border-radius:5px; font-weight:bold;">
                    Margem: {margem:.1f}%
                </div>
            </div>
        """, unsafe_allow_html=True)

# 6. Gráfico de Tendência
st.markdown("---")
ticker_sel = st.selectbox("Selecione para ver o gráfico:", list(acoes_config.keys()))
df_hist = dados_mercado[ticker_sel]['hist']

if not df_hist.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['Close'], name='Preço', line=dict(color=acoes_config[ticker_sel]['cor'])))
    fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['Close'].rolling(50).mean(), name='Média 50d', line=dict(color='gray', dash='dot')))
    fig.update_layout(template="plotly_white", height=400, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)
