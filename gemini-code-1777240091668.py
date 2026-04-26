import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configurações da Página
st.set_page_config(page_title="App Preço Teto - Ações BR", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .card { padding: 20px; border-radius: 10px; background-color: white; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração das Ações
acoes_config = {
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'cor': '#005ca9', 'metodo': 'Bazin', 'link': 'https://investidor10.com.br/acoes/cxse3/'},
    'ITSA4.SA': {'nome': 'Itaúsa', 'cor': '#ec7000', 'metodo': 'Bazin', 'link': 'https://investidor10.com.br/acoes/itsa4/'},
    'CPLE3.SA': {'nome': 'Copel', 'cor': '#2d3e50', 'metodo': 'Bazin', 'link': 'https://investidor10.com.br/acoes/cple3/'},
    'AXIA6.SA': {'nome': 'Axia Energia', 'cor': '#3bb54a', 'metodo': 'Graham', 'link': 'https://investidor10.com.br/acoes/axia6/'}
}

# 3. Sidebar
st.sidebar.header("⚙️ Configurações")
yield_selecionado = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.09], format_func=lambda x: f"{int(x*100)}%")

if st.sidebar.button("🔄 Forçar Update de Valores"):
    st.cache_data.clear()
    st.rerun()

# 4. Função de Busca de Dados
@st.cache_data(ttl=3600)
def buscar_dados(tickers):
    resultados = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="1y") # Busca 1 ano para o gráfico
            if hist.empty: continue
            
            resultados[t] = {
                'preco_atual': hist['Close'].iloc[-1],
                'dpa': tk.info.get('trailingAnnualDividendRate', 0) or 0,
                'lpa': tk.info.get('trailingEps', 0) or 0,
                'vpa': tk.info.get('bookValue', 0) or 0,
                'historico': hist
            }
        except:
            continue
    return resultados

dados_br = buscar_dados(list(acoes_config.keys()))

# 5. Dashboard Principal
st.title("📊 Painel de Ações: Preço Teto & Tendência")

if dados_br:
    cols = st.columns(4)
    for i, (ticker, config) in enumerate(acoes_config.items()):
        if ticker in dados_br:
            with cols[i]:
                d = dados_br[ticker]
                
                # Cálculos
                if config['metodo'] == 'Bazin':
                    dividendos = d['dpa'] if d['dpa'] > 0 else 0.80
                    preco_teto = dividendos / yield_selecionado
                else:
                    preco_teto = (22.5 * d['lpa'] * d['vpa']) ** 0.5 if d['lpa'] > 0 else 0

                margem = ((preco_teto - d['preco_atual']) / preco_teto) * 100 if preco_teto > 0 else 0
                cor_m = "#28a745" if margem > 0 else "#dc3545"

                st.markdown(f"""
                    <div class="card" style="border-top: 8px solid {config['cor']};">
                        <h3 style="margin:0;">{ticker.replace('.SA', '')}</h3>
                        <small>{config['nome']}</small><hr>
                        Preço: <b>R$ {d['preco_atual']:.2f}</b><br>
                        Teto: <b>R$ {preco_teto:.2f}</b><br>
                        <span style="color:{cor_m};">Margem: <b>{margem:.2f}%</b></span>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # 6. Seção de Gráficos
    st.subheader("📈 Análise de Tendência (Último Ano)")
    selecionado = st.selectbox("Selecione a ação para detalhamento:", list(dados_br.keys()), format_func=lambda x: x.replace('.SA', ''))
    
    df_plot = dados_br[selecionado]['historico']
    
    fig = go.Figure()
    # Preço de Fechamento
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], name='Preço de Mercado', line=dict(color=acoes_config[selecionado]['cor'], width=2)))
    # Média Móvel 50 dias
    fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'].rolling(window=50).mean(), name='Tendência (Média 50d)', line=dict(color='gray', dash='dot')))

    fig.update_layout(template="plotly_white", height=450, hovermode="x unified", margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Aguardando carregamento de dados...")
