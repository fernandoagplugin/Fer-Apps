import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Configurações da Página
st.set_page_config(page_title="App Preço Teto - Investidor10", layout="wide")

# Estilos Visuais
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .card { padding: 20px; border-radius: 10px; background-color: white; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. Configuração das Ações e Links Reais do Investidor 10
acoes_config = {
    'CXSE3.SA': {
        'nome': 'Caixa Seguridade', 
        'cor': '#005ca9', 
        'metodo': 'Bazin',
        'link': 'https://investidor10.com.br/acoes/cxse3/'
    },
    'ITSA4.SA': {
        'nome': 'Itaúsa', 
        'cor': '#ec7000', 
        'metodo': 'Bazin',
        'link': 'https://investidor10.com.br/acoes/itsa4/'
    },
    'CPLE3.SA': {
        'nome': 'Copel', 
        'cor': '#2d3e50', 
        'metodo': 'Bazin',
        'link': 'https://investidor10.com.br/acoes/cple3/'
    },
    'AXIA6.SA': {
        'nome': 'Axia Energia', 
        'cor': '#3bb54a', 
        'metodo': 'Graham',
        'link': 'https://investidor10.com.br/acoes/axia6/'
    }
}

# 3. Sidebar e Botão de Update
st.sidebar.header("⚙️ Configurações")
yield_selecionado = st.sidebar.selectbox("Yield Mínimo Desejado", [0.06, 0.08, 0.09], format_func=lambda x: f"{int(x*100)}%")

# Botão que força a atualização limpando o cache
if st.sidebar.button("🔄 Forçar Update de Valores"):
    st.cache_data.clear()
    st.rerun()

# 4. Função de Busca de Dados (Com Cache para não travar o app)
@st.cache_data(ttl=3600)
def buscar_dados(tickers):
    resultados = {}
    for t in tickers:
        try:
            ticker_data = yf.Ticker(t)
            # Pegando o preço mais recente (ajustado para ITSA4.SA)
            hist = ticker_data.history(period="1d")
            preco = hist['Close'].iloc[-1] if not hist.empty else 0
            
            resultados[t] = {
                'preco_atual': preco,
                'dpa': ticker_data.info.get('trailingAnnualDividendRate', 0) or 0,
                'lpa': ticker_data.info.get('trailingEps', 0) or 0,
                'vpa': ticker_data.info.get('bookValue', 0) or 0
            }
        except:
            resultados[t] = {'preco_atual': 0, 'dpa': 0, 'lpa': 0, 'vpa': 0}
    return resultados

dados_mercado = buscar_dados(list(acoes_config.keys()))

# 5. Exibição na Tela Única
st.title("📈 Calculadora de Preço Teto")
st.write("Dados atualizados via Yahoo Finance. Clique nos links para conferir no Investidor 10.")

cols = st.columns(4)

for i, (ticker, config) in enumerate(acoes_config.items()):
    with cols[i]:
        d = dados_mercado[ticker]
        
        # Lógica de Cálculo
        if config['metodo'] == 'Bazin':
            # Se o DPA for 0 no Yahoo, colocamos um valor base para não zerar (ex: CXSE3 paga bem)
            dividendos = d['dpa'] if d['dpa'] > 0 else 0.80 
            preco_teto = dividendos / yield_selecionado
        else:
            preco_teto = (22.5 * d['lpa'] * d['vpa']) ** 0.5 if d['lpa'] > 0 else 0

        # Margem de Segurança
        if preco_teto > 0:
            margem = ((preco_teto - d['preco_atual']) / preco_teto) * 100
        else:
            margem = 0
            
        cor_margem = "#28a745" if margem > 0 else "#dc3545" # Verde ou Vermelho

        # Card Visual
        st.markdown(f"""
            <div class="card" style="border-top: 8px solid {config['cor']};">
                <h3 style="margin-bottom:0;">{ticker.replace('.SA', '')}</h3>
                <p style="color:gray; font-size:0.9em;">{config['nome']}</p>
                <hr>
                <p>Preço Atual: <b>R$ {d['preco_atual']:.2f}</b></p>
                <p>Preço Teto: <b style="font-size:1.1em;">R$ {preco_teto:.2f}</b></p>
                <p style="color:{cor_margem};">Margem: <b>{margem:.2f}%</b></p>
                <a href="{config['link']}" target="_blank" style="text-decoration:none;">
                    <button style="width:100%; padding:5px; cursor:pointer; border:1px solid #ddd; border-radius:5px;">
                        Ver no Investidor 10 🔗
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)
