import pandas as pd
import os
import sys
import django



PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))  # scripts/
PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)               # abaqus_portfolio/
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abaqus_portfolio.settings')
django.setup()


#The task is to read an Excel file with weights and prices, calculate the portfolio values, and save the results to the django database.
#I dont want to calculate the porfolio values everyday, they will be calculated on run time when asked I just want to populate the database.



#Read the data
weights = pd.read_excel("datos.xlsx", sheet_name="weights")
prices = pd.read_excel("datos.xlsx", sheet_name="Precios", index_col=0)

#Separate the portfolio columns, assuming they are always name like portafolio {number} (optional)
portfolio_cols = [col for col in weights.columns if col.lower().startswith('portafolio')]

#unpivot the weights DataFrame, name it unpivoted_weights
unpivoted_weights = weights.melt(id_vars=['Fecha'], value_vars=portfolio_cols, var_name='Portfolio', value_name='Weight')

#changhe the column name 'Fecha' to 'Date'
unpivoted_weights.rename(columns={'Fecha': 'Date'}, inplace=True)

#unpivot the prices DataFrame, keep  it as long format
unpivoted_prices = prices.melt(ignore_index=False, var_name='Asset', value_name='Price')
unpivoted_prices.index.name = 'Date'

#populate the database with the data
from investments.models import Asset, Portfolio, Price, PortfolioAssetHolding
for asset_name in unpivoted_prices['Asset'].unique():
    asset, created = Asset.objects.get_or_create(name=asset_name)
    if created:
        print(f"Created asset: {asset_name}")
    else:
        print(f"Asset already exists: {asset_name}")

for portfolio_name in unpivoted_weights['Portfolio'].unique():
    portfolio, created = Portfolio.objects.get_or_create(name=portfolio_name)
    if created:
        print(f"Created portfolio: {portfolio_name}")
    else:
        print(f"Portfolio already exists: {portfolio_name}")

for index, row in unpivoted_prices.iterrows():
    asset = Asset.objects.get(name=row['Asset'])
    price, created = Price.objects.get_or_create(asset=asset, date=index, defaults={'price': row['Price']})
    if created:
        print(f"Created price for {asset.name} on {index}: {row['Price']}")
    else:
        print(f"Price already exists for {asset.name} on {index}")