from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date
from investments.services.portfolio import get_asset_usd_amounts
from django.shortcuts import render
from investments.models import Portfolio

class PortfolioUSDValuesView(APIView):
    def get(self, request):
        portfolio_name = request.GET.get('portfolio')
        date_str = request.GET.get('date')
        if not portfolio_name or not date_str:
            return Response({'error': 'portfolio and date are required'}, status=status.HTTP_400_BAD_REQUEST)
        amounts = get_asset_usd_amounts(portfolio_name, date_str)
        return Response(amounts)

# create view for home.html


def home(request):
    portfolios = Portfolio.objects.all()
    return render(request, 'investments/home.html', {'portfolios': portfolios})
