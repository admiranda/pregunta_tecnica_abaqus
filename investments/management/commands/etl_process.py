import pandas as pd
from django.core.management.base import BaseCommand
from investments.models import Asset, Portfolio, Price, PortfolioAssetHolding

class Command(BaseCommand):
    help = "Importa datos desde datos.xlsx a la base de datos."

    def handle(self, *args, **options):
        weights = pd.read_excel("abaqus_portfolio/data/datos.xlsx", sheet_name="weights")
        prices = pd.read_excel("abaqus_portfolio/data/datos.xlsx", sheet_name="Precios", index_col=0)
        portfolio_cols = [col for col in weights.columns if col.lower().startswith('portafolio')]
        unpivoted_weights = weights.melt(
            id_vars=['Fecha', 'activos'],
            value_vars=portfolio_cols,   # portfolio_cols = ['portafolio 1', 'portafolio 2']
            var_name='Portfolio',
            value_name='Weight'
        )
        unpivoted_weights.rename(columns={'activos': 'Asset', 'Fecha': 'Date'}, inplace=True)
        unpivoted_prices = prices.melt(ignore_index=False, var_name='Asset', value_name='Price')
        unpivoted_prices.index.name = 'Date'

        # Assets
        for asset_name in unpivoted_prices['Asset'].unique():
            asset, created = Asset.objects.get_or_create(name=asset_name)
            self.stdout.write(f"{'Created' if created else 'Exists'} asset: {asset_name}")

        # Portfolios
        for portfolio_name in unpivoted_weights['Portfolio'].unique():
            portfolio, created = Portfolio.objects.get_or_create(name=portfolio_name, defaults={'initial_value': 1_000_000_000})
            self.stdout.write(f"{'Created' if created else 'Exists'} portfolio: {portfolio_name}")

        # Prices
        for index, row in unpivoted_prices.iterrows():
            asset = Asset.objects.get(name=row['Asset'])
            price, created = Price.objects.get_or_create(asset=asset, date=index, defaults={'price': row['Price']})
            self.stdout.write(f"{'Created' if created else 'Exists'} price for {asset.name} on {index}: {row['Price']}")

        self.stdout.write(self.style.SUCCESS('Importación completada.'))
        start_date = unpivoted_weights['Date'].min()
        V0 = 1_000_000_000
        
        # Since the portfolios are already created, we can now query them directly and then populate the holdings
        for portfolio in Portfolio.objects.all():
            for asset in Asset.objects.all():
                weight_row = unpivoted_weights[
                    (unpivoted_weights['Date'] == start_date) & 
                    (unpivoted_weights['Portfolio'] == portfolio.name) &
                    (unpivoted_weights['Asset'] == asset.name)
                ]
                if weight_row.empty:
                    continue

                w = weight_row['Weight'].iloc[0] or 0

                price_row = unpivoted_prices[
                    (unpivoted_prices.index == start_date) &
                    (unpivoted_prices['Asset'] == asset.name)
                ]
                if price_row.empty or price_row['Price'].isnull().all():
                    continue

                p = price_row['Price'].iloc[0]

                if p == 0 or w == 0 or pd.isnull(p) or pd.isnull(w):
                    continue

                quantity = w * V0 / p

                holding, created = PortfolioAssetHolding.objects.get_or_create(
                    portfolio=portfolio,
                    asset=asset,
                    defaults={
                        'initial_weight': w,
                        'initial_quantity': quantity
                    }
                )
                if not created:
                    holding.initial_weight = w
                    holding.initial_quantity = quantity
                    holding.save()
                self.stdout.write(
                    f"{'Created' if created else 'Updated'} holding for {portfolio.name} - {asset.name}: {w:.2%}, {quantity:.2f}"
                )
                        # --- Validación: Suma total invertida por portafolio ---
        print("\nVALIDACIÓN DE MONTO INVERTIDO (debe ser $1,000,000,000):\n")
        for portfolio in Portfolio.objects.all():
            total_invertido = 0
            print(f"Portafolio: {portfolio.name}")
            for holding in PortfolioAssetHolding.objects.filter(portfolio=portfolio):
                price = Price.objects.get(asset=holding.asset, date=start_date).price
                usd = holding.initial_quantity * price
                print(f"\t{holding.asset.name}: {holding.initial_weight:.2%} ({holding.initial_quantity:.4f}) × {price:.2f} = {usd:,.2f}")
                total_invertido += usd
            print(f"  TOTAL INVERTIDO: {total_invertido:,.2f}\n")

