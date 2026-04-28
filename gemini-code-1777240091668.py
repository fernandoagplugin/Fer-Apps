import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json
import os

# --- Sistema de Salvamento de Configurações ---
ARQUIVO_CONFIG = "config_acoes.json"

def carregar_configuracoes():
    """Carrega as configurações salvas ou define valores padrão."""
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r") as f:
            return json.load(f)
    return {
        "acao1": "BBAS3.SA", "acao2": "PETR4.SA", 
        "acao3": "ITUB4.SA", "acao4": "VALE3.SA", 
        "taxa_desejada": 6.0
    }

def salvar_configuracoes():
    """Salva os valores atuais no arquivo JSON sempre que algo é alterado."""
    config = {
        "acao1": st.session_state.acao1.upper(),
        "acao2": st.session_state.acao2.upper(),
        "acao3": st.session_state.acao3.upper(),
        "acao4": st.session_state.acao4.upper(),
        "taxa_desejada": st.session_state.taxa_desejada
    }
    with open(ARQUIVO_CONFIG, "w") as f:
        json.dump(config, f)

# Inicializando a memória do Streamlit para corrigir o bug do valor retornando
if "inicializado" not in st.session_state:
    config_salva = carregar_configuracoes()
    for chave, valor in config_salva.items():
        st.session_state[chave] = valor
    st.session_state.inicializado = True

# --- Configuração da Página ---
st.set_page_config(page_title="Monitor de Preço Teto", layout="wide")

st.title("📊 Monitor de Preço Teto em Tempo Real")
st.markdown("Cálculo baseado no Método Bazin (Soma dos Dividendos dos últimos 12 meses ÷ Taxa Desejada).")
st.markdown("---")

# --- Barra Lateral (Configurações) ---
st.sidebar.header("⚙️ Configurações")
st.sidebar.write("Insira os códigos das ações (adicione .SA para ativos brasileiros):")

# Os campos agora usam 'key' (ligados diretamente à memória) e acionam o salvamento ao mudar
st.sidebar.text_input("Ação 1", key="acao1", on_change=salvar_configuracoes)
st.sidebar.text_input("Ação 2", key="acao2", on_change=salvar_configuracoes)
st.sidebar.text_input("Ação 3", key="acao3", on_change=salvar_configuracoes)
st.sidebar.text_input("Ação 4", key="acao4", on_change=salvar_configuracoes)

st.sidebar.number_input("Taxa de Retorno Desejada (%)", step=0.5, key="taxa_desejada", on_change=salvar_configuracoes)

# Converte a taxa para decimal para o cálculo matemático
taxa_calc = st.session_state.taxa_desejada / 100

if st.sidebar.button("🔄 Atualizar Cotações Agora"):
    st.rerun()

acoes = [
    st.session_state.acao1.upper(), 
    st.session_state.acao2.upper(), 
    st.session_state.acao3.upper(), 
    st.session_state.acao4.upper()
]

# --- Função para calcular Dividendos dos últimos 12 meses ---
@st.cache_data(ttl=3600)
def obter_dividendos_12m(ticker):
    try:
        acao = yf.Ticker(ticker)
        dividendos = acao.dividends
        if dividendos.empty:
            return 0.0
        
        um_ano_atras = pd.Timestamp.today(tz='UTC') - pd.DateOffset(years=1)
        dividendos.index = pd.to_datetime(dividendos.index, utc=True)
        divs_recentes = dividendos[dividendos.index >= um_ano_atras]
        
        return divs_recentes.sum()
    except:
        return 0.0

# --- Exibição dos Dados ---
colunas = st.columns(4)

for i, ticker in enumerate(acoes):
    if not ticker.strip():
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
            preco_teto = div_12m / taxa_calc if taxa_calc > 0 else 0
            
            # Cálculo da Margem de Segurança
            if preco_teto > 0:
                margem = ((preco_teto / preco_atual) - 1) * 100
            else:
                margem = 0.0
                
            # Formatação Visual
            st.subheader(ticker)
            st.metric("Preço Atual", f"R$ {preco_atual:.2f}")
            st.metric(f"Preço Teto ({st.session_state.taxa_desejada:.1f}%)", f"R$ {preco_teto:.2f}")
            
            cor = "normal" if margem >= 0 else "inverse"
            st.metric("Margem de Segurança", f"{margem:.2f}%", delta=f"{margem:.2f}%", delta_color=cor)
            
            st.caption(f"Dividendos (12m): R$ {div_12m:.2f}")
            
        except Exception as e:
            st.error(f"Erro ao carregar {ticker}")

st.markdown("---")
st.caption("Nota: Os dados são extraídos do Yahoo Finance. O mercado possui um pequeno delay inerente à plataforma de origem.")
