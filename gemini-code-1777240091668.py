import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="EquityDash - Estável", layout="wide")

# 1. ATIVOS E CONFIGURAÇÕES
# Usamos um dicionário simples. Se precisar mudar, mude apenas aqui.
acoes_config = {
    'AXIA3.SA': {'nome': 'Axia Energia', 'logo': 'https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png', 'preco_base': 50.00},
    'CPLE3.SA': {'nome': 'Copel', 'logo': 'https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png', 'preco_base': 15.00},
    'CXSE3.SA': {'nome': 'Caixa Seguridade', 'logo': 'https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Caixa.png', 'preco_base': 18.00}
}

st.title("EquityDash - Versão Blindada")

# 2. BUSCA DE DADOS (Blindada contra erro)
@st.cache_data(ttl=600)
def buscar_dados_seguro(ticker):
    try:
        tk = yf.Ticker(ticker)
        # Tenta buscar o preço atual. Se falhar, retorna o preço base configurado.
        info = tk.fast_info
        preco = info.get('last_price', acoes_config[ticker]['preco_base'])
        hist = tk.history(period="1y")
        return preco, hist
    except:
        # Em qualquer falha, retorna o preço base e DataFrame vazio (não quebra o app)
        return acoes_config[ticker]['preco_base'], pd.DataFrame()

# 3. INTERFACE E LÓGICA (Cálculos isolados)
cols = st.columns(len(acoes_config))

for i, (ticker, conf) in enumerate(acoes_config.items()):
    preco_atual, historico = buscar_dados_seguro(ticker)
    
    with cols[i]:
        st.image(conf['logo'], width=60)
        st.subheader(ticker)
        # Campo para forçar o preço manualmente se a API errar
        preco_usuario = st.number_input(f"Preço {ticker}", value=float(preco_atual), step=0.1, key=f"p_{ticker}")
        st.write(f"Preço usado no cálculo: **R$ {preco_usuario:.2f}**")

# 4. GRÁFICOS (Somente se existirem dados)
st.markdown("---")
target = st.selectbox("Selecione o ativo para gráfico:", list(acoes_config.keys()))

_, hist_data = buscar_dados_seguro(target)
if not hist_data.empty:
    fig = go.Figure(go.Scatter(x=hist_data.index, y=hist_data['Close']))
    fig.update_layout(title=f"Histórico de {target}", height=300)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Histórico indisponível para este ativo.")

if st.button("Limpar cache e recarregar"):
    st.cache_data.clear()
    st.rerun()
