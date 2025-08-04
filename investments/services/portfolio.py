from investments.models import Portfolio, Price, PortfolioAssetHolding
from collections import defaultdict
from investments.models import Portfolio, Price


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

def get_weights_and_portfolio_value_time_series(portfolio_name, fecha_inicio, fecha_fin):
    """
    Devuelve para cada fecha en el rango los w_{i,t} y V_t del portafolio dado,
    asumiendo cantidades c_{i,t} constantes igual a initial_quantity.
    """
    try:
        portfolio = Portfolio.objects.get(name=portfolio_name)
    except Portfolio.DoesNotExist:
        return None  # quien llame debe manejar error

    # Traer holdings con sus cantidades iniciales
    holdings = portfolio.holdings.select_related("asset").all()
    if not holdings:
        return []

    asset_ids = [h.asset.id for h in holdings]
    quantity_by_asset = {h.asset.id: h.initial_quantity for h in holdings}

    # Filtrar prices entre fechas para esos assets
    prices_qs = Price.objects.filter(
        asset_id__in=asset_ids,
        date__gte=fecha_inicio,
        date__lte=fecha_fin
    ).select_related("asset").order_by("date")

    # Organizar prices por fecha
    # fechas únicas ordenadas
    dates = sorted({p.date for p in prices_qs})
    # Map asset -> {date: price}
    price_map = defaultdict(dict)
    for p in prices_qs:
        price_map[p.asset.id][p.date] = p.price

    result = []
    for date in dates:
        x_it = {}
        # calcular x_{i,t} = c_{i,0} * p_{i,t}
        for asset_id in asset_ids:
            price = price_map.get(asset_id, {}).get(date)
            if price is None:
                x_it[asset_id] = None
            else:
                x_it[asset_id] = quantity_by_asset[asset_id] * price

        # V_t: suma de los x_{i,t} válidos
        V_t = sum(v for v in x_it.values() if v is not None)

        # w_{i,t}
        w_it = {}
        for asset_id, x in x_it.items():
            if x is None or V_t == 0:
                w_it[asset_id] = None
            else:
                w_it[asset_id] = x / V_t

        # Formatear por nombre de activo
        assets = []
        for h in holdings:
            aid = h.asset.id
            assets.append({
                "asset": h.asset.name,
                "x_it": x_it.get(aid),
                "w_it": w_it.get(aid)
            })

        result.append({
            "date": date,
            "V_t": V_t,
            "assets": assets
        })

    return result