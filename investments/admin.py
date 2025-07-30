from django.contrib import admin
from .models import Asset, Portfolio, Price, PortfolioAssetHolding

admin.site.register(Asset)
admin.site.register(Portfolio)
admin.site.register(Price)
admin.site.register(PortfolioAssetHolding)
