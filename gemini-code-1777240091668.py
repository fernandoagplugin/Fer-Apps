import streamlit as st
import yfinance as yf
import pandas as pd
import math

# 1. Configurações da Página
LOGO_SIDEBAR = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Logo.png"
LOGO_HEADER = "https://raw.githubusercontent.com/fernandoagplugin/Icone/104a1e5931da579a81ef961da034476ec3b8e82e/EquityDash%20Horizontal.png"

st.set_page_config(page_title="EquityDash Ultra v7.11", page_icon=LOGO_SIDEBAR, layout="wide")

# --- CSS Profissional ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; background-color: #f8f9fa; }}
    .main-header {{ background-color: #20B2AA; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; }}
    .header-logo {{ width: 500px; height: auto; display: block; margin: 0 auto; }}
    .card-equity {{ background: white; padding: 16px; border-radius: 20px; border: 1px solid #eef2f6; box-shadow: 0 4px 12px rgba(0,0,0,0.03); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }}
    .badge-buy {{ background-color: #dcfce7; color: #15803d; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }}
    .badge-wait {{ background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }}
    .badge-error {{ background-color: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 11px; }}
    .label-text {{ color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
    
    /* Box IPCA */
    .box-ipca {{ background: #f0f9ff; border-left: 4px solid #0284c7; padding: 8px 10px; border-radius: 8px; margin-top: 10px; font-size: 11px; text-align: left; }}
    
    /* Box Métricas Base */
    .box-base {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 8px; border-radius: 8px; margin-top: 8px; font-size: 10px; text-align: left; }}
    .grid-base {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; color: #475569; }}
    </style>
    """, unsafe_allow_html=True)

st.sidebar.image(LOGO_SIDEBAR, use_container_width=True)
st.markdown(f'<div class="main-header"><img src="{LOGO_HEADER}" class="header-logo"></div>', unsafe_allow_html=True)

# 2. Ativos Configurados
acoes_config = {
    'AXIA3.SA': {'cor': '#3bb54a', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png"},
    'CPLE3.SA': {'cor': '#2d3e50', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png"},
    'CXSE3.SA': {'cor': '#005ca9', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Caixa.png"},
    'ITSA4.SA': {'cor': '#ec7000', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/Itausa.png"},
    'PSSA3.SA': {'cor': '#0047bb', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/main/porto-seguro.png"},
    'VALE3.SA': {'cor': '#003366', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/b8d8683f36e3b1ebacbd6c99dec0065cd65b8ddd/VALE.png"},
    'TIMS3.SA': {'cor': '#002f6c', 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/b8d8683f36e3b1ebacbd6c99dec0065cd65b8ddd/TIM.png"}
}

# 3. Sidebar
st.sidebar.title("⚙️ Parâmetros de Valuation")
yield_valor_br = st.sidebar.select_slider("Yield Alvo BR (Bazin) %", options=[round(x*0.1, 1) for x in range(60, 125, 5)], value=6.0)
yield_alvo_br = yield_valor_br / 100

st.sidebar.markdown("---")
st.sidebar.title("🏛️ Renda Fixa (Benchmark)")
taxa_ntnb = st.sidebar.number_input("Tesouro IPCA+ 10 Anos (%)", min_value=0.0, max_value=15.0, value=6.20, step=0.1)

# 4. Engine de Dados Blindada (Com tratamento individual por ativo)
@st.cache_data(ttl=600)
def get_live_data():
    tickers = list(acoes_config.keys())
    results = {}
    um_ano_atras = pd.Timestamp.now(tz='UTC') - pd.DateOffset(years=1)

    for t in tickers:
        preco, lpa, vpa, divs_12m = 0, 0, 0, 0
        try:
            tk = yf.Ticker(t)
            
            # Tentar pegar o histórico de preços recentes
            hist = tk.history(period="5d")
            if not hist.empty:
                preco = hist['Close'].iloc[-1]
            
            # Tentar pegar dividendos dos últimos 12 meses
            divs = tk.dividends
            if not divs.empty:
                divs.index = pd.to_datetime(divs.index, utc=True)
                divs_12m = divs[divs.index >= um_ano_atras].sum()
                
            # Tentar pegar informações fundamentais
            info = tk.info
            lpa = info.get('trailingEps') or info.get('forwardEps') or 0
            vpa = info.get('bookValue') or 0
            
            # Fallback caso o yfinance falhe em retornar o LPA mas traga o P/L
            if lpa == 0 and preco > 0:
                pe = info.get('trailingPE')
                if pe and pe > 0:
                    lpa = preco / pe
                    
            # Fallback para VPA caso venha zero
            if vpa == 0 and preco > 0:
                pb = info.get('priceToBook')
                if pb and pb > 0:
                    vpa = preco / pb

        except Exception as e:
            print(f"Erro ao buscar {t}: {e}")
            
        results[t] = {'p': preco, 'lpa': lpa, 'vpa': vpa, 'div_pagos': divs_12m}
            
    return results

market_data = get_live_data()

# 5. Renderização dos Cards
cols = st.columns(len(acoes_config))

for i, ticker in enumerate(acoes_config.keys()):
    conf = acoes_config[ticker]
    dados = market_data[ticker]
    
    price = dados['p']
    lpa = dados['lpa']
    vpa = dados['vpa']
    div_pagos = dados['div_pagos']
    
    if price > 0 and (lpa > 0 or vpa > 0 or div_pagos > 0):
        # Valuation (Tratando caso o LPA ou VPA venham zerados isoladamente para não quebrar Graham/Bazin)
        t_bazin = (div_pagos / yield_alvo_br) if (yield_alvo_br > 0 and div_pagos > 0) else 0
        t_graham = math.sqrt(max(0, 22.5 * lpa * vpa)) if (lpa > 0 and vpa > 0) else 0
        
        # Pesos para o Preço Teto Híbrido
        peso_b = 0.8 if ticker in ['CXSE3.SA', 'PSSA3.SA', 'CPLE3.SA', 'VALE3.SA', 'TIMS3.SA'] else 0.5
        
        if t_bazin > 0 and t_graham > 0:
            teto = (t_bazin * peso_b) + (t_graham * (1 - peso_b))
        elif t_bazin > 0:
            teto = t_bazin
        else:
            teto = t_graham
            
        margem = ((teto - price) / teto) * 100 if teto > 0 else 0
        badge_html = f'<span class="badge-buy">{margem:.1f}%</span>' if margem > 0 else f'<span class="badge-wait">{margem:.1f}%</span>'
        
        # IPCA+ (Earnings Yield)
        ey_real = (lpa / price) * 100 if lpa > 0 and price > 0 else 0
        spread_ntnb = ey_real - taxa_ntnb
        cor_spread = "#15803d" if spread_ntnb >= 0 else "#b91c1c"
        sinal_spread = "+" if spread_ntnb >= 0 else ""
        
        # Múltiplos
        pl = price / lpa if lpa > 0 else 0
        pvp = price / vpa if vpa > 0 else 0
        
        card_html = f"""<div class="card-equity">
<div>
<img src="{conf['logo']}" style="max-width:100px; height:38px; margin:auto; object-fit:contain;">
<div class="label-text" style="margin-top:8px;">{ticker}</div>
<div style="font-size:20px; font-weight:700;">R$ {price:.2f}</div>
{badge_html}
</div>
<div>
<div style="margin-top:10px; text-align: left; background: #fdfdfd; padding: 6px 8px; border-radius: 8px; font-size:11px; border:1px solid #f1f5f9;">
Bazin: <b>R$ {t_bazin:.2f}</b><br>
Graham: <b>R$ {t_graham:.2f}</b><br>
Teto: <b style="color:#1e3a8a">R$ {teto:.2f}</b>
</div>
<div class="box-base">
<div style="font-weight:700; color:#334155; margin-bottom:4px; border-bottom:1px solid #e2e8f0; padding-bottom:2px;">📋 Métricas Base</div>
<div class="grid-base">
<div>LPA: <b>R$ {lpa:.2f}</b></div>
<div>VPA: <b>R$ {vpa:.2f}</b></div>
<div>Provento 12M: <b>R$ {div_pagos:.2f}</b></div>
<div>P/L: <b>{pl:.1f}x</b> | P/VP: <b>{pvp:.2f}x</b></div>
</div>
</div>
<div class="box-ipca">
<div style="color: #0369a1; font-weight: 700; margin-bottom: 1px;">📊 Retorno Implícito</div>
<div style="font-size: 12px; font-weight: 700; color: #0f172a;">IPCA + {ey_real:.2f}%</div>
<div style="color: {cor_spread}; font-size: 10px; font-weight: 600; margin-top: 2px;">{sinal_spread}{spread_ntnb:.2f}% vs NTN-B</div>
</div>
</div>
</div>"""

    else:
        card_html = f"""<div class="card-equity">
<div>
<img src="{conf['logo']}" style="max-width:100px; height:38px; margin:auto; object-fit:contain;">
<div class="label-text" style="margin-top:8px;">{ticker}</div>
<div style="font-size:20px; font-weight:700;">R$ {price:.2f}</div>
<span class="badge-error">Sem Dados</span>
</div>
<div>
<div class="box-base" style="color:#64748b;">Aguardando dados...</div>
<div class="box-ipca" style="color:#64748b;">Aguardando preço...</div>
</div>
</div>"""

    with cols[i]:
        st.markdown(card_html, unsafe_allow_html=True)
