import pandas as pd
from django.core.management.base import BaseCommand
from investments.models import Asset, Portfolio, PortfolioAssetHolding, Price
from django.db import transaction
from datetime import datetime

class Command(BaseCommand):
    help = "Load portfolios, assets, weights, and prices from datos.xlsx"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='datos.xlsx')

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file']
        print(f"Reading from {file_path}...")

        # Leer hojas de Excel
        df_weights = pd.read_excel(file_path, sheet_name='Weights')
        df_prices = pd.read_excel(file_path, sheet_name='Precios', index_col=0)

        # Normalizar nombres de activos
        asset_names = list(df_weights['Asset'])
        assets = {}
        for name in asset_names:
            asset, _ = Asset.objects.get_or_create(name=name)
            assets[name] = asset

        # Crear portafolios
        portfolios = {}
        for i in [1, 2]:
            pf, _ = Portfolio.objects.get_or_create(
                name=f"Portfolio {i}",
                defaults={"initial_value": 1_000_000_000}
            )
            portfolios[i] = pf

        # Crear holdings (pesos iniciales)
        for idx, row in df_weights.iterrows():
            for i in [1, 2]:
                asset = assets[row['Asset']]
                weight = row[f'Portfolio_{i}']
                holding, _ = PortfolioAssetHolding.objects.get_or_create(
                    portfolio=portfolios[i],
                    asset=asset,
                    defaults={
                        "initial_weight": weight,
                        "initial_quantity": None,
                    }
                )
                # Si ya existe, actualiza peso
                if not holding.initial_weight == weight:
                    holding.initial_weight = weight
                    holding.save()

        # Cargar precios
        for asset_name in df_prices.columns:
            asset = assets[asset_name]
            for date_str, price in df_prices[asset_name].items():
                if pd.isna(price):
                    continue
                # Si la fecha viene como string, conviértela
                if not isinstance(date_str, datetime):
                    date = pd.to_datetime(date_str).date()
                else:
                    date = date_str.date()
                Price.objects.update_or_create(
                    asset=asset, date=date, defaults={'price': price}
                )

        # Calcular cantidades iniciales usando precios al 15/02/2022
        price_date = datetime.strptime('2022-02-15', '%Y-%m-%d').date()
        for i in [1, 2]:
            pf = portfolios[i]
            for holding in PortfolioAssetHolding.objects.filter(portfolio=pf):
                price_obj = Price.objects.get(asset=holding.asset, date=price_date)
                # Formula: C_{i,0} = (w_{i,0} * V_0) / P_{i,0}
                qty = (holding.initial_weight * pf.initial_value) / price_obj.price
                holding.initial_quantity = qty
                holding.save()

        print("Data import completed successfully!")
