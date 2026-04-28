import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# --- Configuração da Página ---
st.set_page_config(page_title="Monitor de Preço Teto", layout="wide")

st.title("📊 Monitor de Preço Teto em Tempo Real")
st.markdown("Cálculo baseado no Método Bazin (Soma dos Dividendos dos últimos 12 meses ÷ Taxa Desejada).")
st.markdown("---")

# --- Barra Lateral (Configurações) ---
st.sidebar.header("⚙️ Configurações")
st.sidebar.write("Insira os códigos das ações (adicione .SA para ativos brasileiros):")

acao1 = st.sidebar.text_input("Ação 1", value="BBAS3.SA").upper()
acao2 = st.sidebar.text_input("Ação 2", value="PETR4.SA").upper()
acao3 = st.sidebar.text_input("Ação 3", value="ITUB4.SA").upper()
acao4 = st.sidebar.text_input("Ação 4", value="VALE3.SA").upper()

taxa_desejada = st.sidebar.number_input("Taxa de Retorno Desejada (%)", value=6.0, step=0.5) / 100

if st.sidebar.button("🔄 Atualizar Cotações Agora"):
    st.rerun()

acoes = [acao1, acao2, acao3, acao4]

# --- Função para calcular Dividendos dos últimos 12 meses ---
@st.cache_data(ttl=3600) # Faz cache por 1 hora para não sobrecarregar o Yahoo Finance
def obter_dividendos_12m(ticker):
    try:
        acao = yf.Ticker(ticker)
        dividendos = acao.dividends
        if dividendos.empty:
            return 0.0
        
        # Filtra apenas os últimos 12 meses
        um_ano_atras = pd.Timestamp.today(tz='UTC') - pd.DateOffset(years=1)
        dividendos.index = pd.to_datetime(dividendos.index, utc=True)
        divs_recentes = dividendos[dividendos.index >= um_ano_atras]
        
        return divs_recentes.sum()
    except:
        return 0.0

# --- Exibição dos Dados ---
colunas = st.columns(4)

for i, ticker in enumerate(acoes):
    if not ticker:
        continue
        
    with colunas[i]:
        try:
            acao_obj = yf.Ticker(ticker)
            hist = acao_obj.history(period="1d")
            
            if hist.empty:
                st.warning(f"{ticker}: Sem dados.")
                continue
                
            preco_atual = hist['Close'].iloc[-1]
            div_12m = obter_dividendos_12m(ticker)
            
            # Cálculo do Preço Teto
            preco_teto = div_12m / taxa_desejada if taxa_desejada > 0 else 0
            
            # Cálculo da Margem de Segurança
            if preco_teto > 0:
                margem = ((preco_teto / preco_atual) - 1) * 100
            else:
                margem = 0.0
                
            # Formatação Visual
            st.subheader(ticker)
            st.metric("Preço Atual", f"R$ {preco_atual:.2f}")
            st.metric(f"Preço Teto ({taxa_desejada*100:.1f}%)", f"R$ {preco_teto:.2f}")
            
            # Cor da Margem de Segurança (Verde se estiver barato, Vermelho se estiver caro)
            cor = "normal" if margem >= 0 else "inverse"
            st.metric("Margem de Segurança", f"{margem:.2f}%", delta=f"{margem:.2f}%", delta_color=cor)
            
            st.caption(f"Dividendos (12m): R$ {div_12m:.2f}")
            
        except Exception as e:
            st.error(f"Erro ao carregar {ticker}")

st.markdown("---")
st.caption("Nota: Os dados são extraídos do Yahoo Finance. O mercado possui um pequeno delay inerente à plataforma de origem.")
