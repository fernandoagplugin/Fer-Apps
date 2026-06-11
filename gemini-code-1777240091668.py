# Substitua seu dicionário acoes_config por este:
acoes_config = {
    'AXIA3.SA': {'tipo': 'Acao', 'cor': '#3bb54a', 'payout': 0.70, 'lpa': 3.50, 'vpa': 52.10, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/AXIA.png", 'moeda': 'R$'},
    'CPLE3.SA': {'tipo': 'Acao', 'cor': '#2d3e50', 'payout': 0.5, 'lpa': 0.85, 'vpa': 10.40, 'logo': "https://raw.githubusercontent.com/fernandoagplugin/LOGOS/0261825cda3f92616b4c36e82cf5201588429c74/COPEL.png", 'moeda': 'R$'},
    # ... (mantenha os outros)
}

# No loop dos cards, altere a busca de preço para:
# Se o preço for None, ele não exibirá um valor errado, forçando você a ver o erro e corrigir a fonte
price = market_data.get(ticker, {}).get('p')

if price is None:
    st.error(f"Erro: Cotação {ticker} não encontrada.")
else:
    # ... resto do seu código de cálculo
