import pandas as pd
from django.core.management.base import BaseCommand
from investments.models import Asset, Portfolio, Price

class Command(BaseCommand):
    help = "Importa datos desde datos.xlsx a la base de datos."

    def handle(self, *args, **options):
        weights = pd.read_excel("abaqus_portfolio/data/datos.xlsx", sheet_name="weights")
        prices = pd.read_excel("abaqus_portfolio/data/datos.xlsx", sheet_name="Precios", index_col=0)
        portfolio_cols = [col for col in weights.columns if col.lower().startswith('portafolio')]
        unpivoted_weights = weights.melt(id_vars=['Fecha'], value_vars=portfolio_cols, var_name='Portfolio', value_name='Weight')
        unpivoted_weights.rename(columns={'Fecha': 'Date'}, inplace=True)
        unpivoted_prices = prices.melt(ignore_index=False, var_name='Asset', value_name='Price')
        unpivoted_prices.index.name = 'Date'

        # Assets
        for asset_name in unpivoted_prices['Asset'].unique():
            asset, created = Asset.objects.get_or_create(name=asset_name)
            self.stdout.write(f"{'Created' if created else 'Exists'} asset: {asset_name}")

        # Portfolios
        for portfolio_name in unpivoted_weights['Portfolio'].unique():
            portfolio, created = Portfolio.objects.get_or_create(name=portfolio_name)
            self.stdout.write(f"{'Created' if created else 'Exists'} portfolio: {portfolio_name}")

        # Prices
        for index, row in unpivoted_prices.iterrows():
            asset = Asset.objects.get(name=row['Asset'])
            price, created = Price.objects.get_or_create(asset=asset, date=index, defaults={'price': row['Price']})
            self.stdout.write(f"{'Created' if created else 'Exists'} price for {asset.name} on {index}: {row['Price']}")

        self.stdout.write(self.style.SUCCESS('Importación completada.'))
