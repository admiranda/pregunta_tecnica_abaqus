from investments.models import Portfolio, Price, PortfolioAssetHolding

def get_asset_usd_amounts(portfolio_name, date):
    """
    Devuelve el monto en dólares invertido en cada activo para el portafolio y fecha dados.
    Considera la cantidad inicial constante (no hay trades).
    """
    result = []
    try:
        portfolio = Portfolio.objects.get(name=portfolio_name)
    except Portfolio.DoesNotExist:
        return []  # o podrías lanzar una excepción o devolver un error

    holdings = PortfolioAssetHolding.objects.filter(portfolio=portfolio)
    for holding in holdings:
        asset = holding.asset
        quantity = holding.initial_quantity
        # Busca el precio para ese activo y fecha
        try:
            price = Price.objects.get(asset=asset, date=date).price
        except Price.DoesNotExist:
            price = None
        usd_amount = quantity * price if price is not None else None
        result.append({
            'asset': asset.name,
            'quantity': quantity,
            'price': price,
            'usd_amount': usd_amount,
            'portfolio': portfolio.name,
            'date': date
        })
    return result
