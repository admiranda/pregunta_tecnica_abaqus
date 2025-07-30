import pandas as pd
import os
import sys
import django


# Asegúrate que PROJECT_ROOT apunta a la carpeta donde está manage.py
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))  # scripts/
PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)               # abaqus_portfolio/
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abaqus_portfolio.settings')
django.setup()

#Read the data
weights = pd.read_excel("datos.xlsx", sheet_name="weights")
prices = pd.read_excel("datos.xlsx", sheet_name="Precios", index_col=0)



#Separate the portfolio columns, assuming they are always name like portafolio {number} (optional)
portfolio_cols = [col for col in weights.columns if col.lower().startswith('portafolio')]
print(portfolio_cols)

# Unpivot the data
weights_long = pd.melt(
    weights,
    id_vars=['activos'],
    value_vars=portfolio_cols,
    var_name='Portfolio',
    value_name='Initial Weight'
)

# 3. Prices: Wide to long
prices_long = prices.reset_index().melt(
    id_vars=prices.index.name,
    var_name='activos',
    value_name='price'
)   
prices_long = prices_long.rename(columns={prices.index.name: 'date'})

# 4. Initial quantities
initial_value = 1_000_000_000
initial_prices = prices_long[prices_long['date'] == '2022-02-15']

df_init = pd.merge(
    weights_long,
    initial_prices[['activos', 'price']],
    left_on='activos',
    right_on='activos',
    how='left'
)
df_init['initial_quantity'] = (df_init['Initial Weight'] * initial_value) / df_init['price']

print(df_init[['activos', 'Portfolio', 'Initial Weight', 'price', 'initial_quantity']])


from investments.models import Asset, Portfolio, PortfolioAssetHolding, Price
# Cargar activos
for asset_name in weights_long['activos'].unique():
    Asset.objects.get_or_create(name=asset_name)

# Cargar portafolios
for portfolio_name in weights_long['portfolio'].unique():
    Portfolio.objects.get_or_create(name=portfolio_name, defaults={'initial_value': 1_000_000_000})


for idx, row in weights_long.iterrows():
    asset = Asset.objects.get(name=row['activos'])
    portfolio = Portfolio.objects.get(name=row['portfolio'])
    PortfolioAssetHolding.objects.get_or_create(
        asset=asset,
        portfolio=portfolio,
        defaults={'initial_weight': row['initial_weight'], 'initial_quantity': None}
    )


for idx, row in prices_long.iterrows():
    asset = Asset.objects.get(name=row['activos'])
    Price.objects.get_or_create(
        asset=asset,
        date=row['date'],
        defaults={'price': row['price']}
    )

