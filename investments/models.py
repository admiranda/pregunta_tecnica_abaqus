from django.db import models

class Asset(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

class Portfolio(models.Model):
    name = models.CharField(max_length=64, unique=True)
    initial_value = models.FloatField(help_text="Initial value of the portfolio in USD")

    def __str__(self):
        return self.name

class Price(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="prices")
    date = models.DateField()
    price = models.FloatField(help_text="Asset price in USD at given date")

    class Meta:
        unique_together = ('asset', 'date')
        ordering = ['asset', 'date']

    def __str__(self):
        return f"{self.asset.name} - {self.date}: {self.price}"

class PortfolioAssetHolding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="holdings")
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="holdings")
    initial_weight = models.FloatField(help_text="Initial portfolio weight, value must be between 0 and 1)")
    initial_quantity = models.FloatField(help_text="Initial quantity (to be calculated based on price and weight)")

    class Meta:
        unique_together = ('portfolio', 'asset')

    def __str__(self):
        return f"{self.portfolio.name} - {self.asset.name}: {self.initial_weight:.2%} ({self.initial_quantity:.4f})"