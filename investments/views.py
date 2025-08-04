from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from investments.services.portfolio import get_asset_usd_amounts, get_weights_and_portfolio_value_time_series
from django.shortcuts import render
from investments.models import Portfolio, Price

class PortfolioUSDValuesView(APIView):
    def get(self, request):
        portfolio_name = request.GET.get('portfolio')
        date_str = request.GET.get('date')
        if not portfolio_name or not date_str:
            return Response({'error': 'portfolio and date are required'}, status=status.HTTP_400_BAD_REQUEST)
        amounts = get_asset_usd_amounts(portfolio_name, date_str)
        return Response(amounts)

class PortfolioTimeSeriesView(APIView):
    def get(self, request):
        portfolio_name = request.GET.get("portfolio")
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")

        if not portfolio_name or not fecha_inicio or not fecha_fin:
            return Response(
                {"error": "portfolio, fecha_inicio y fecha_fin son requeridos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parsear fechas
        try:
            fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if fi > ff:
            return Response(
                {"error": "fecha_inicio no puede ser posterior a fecha_fin"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = get_weights_and_portfolio_value_time_series(portfolio_name, fi, ff)
        if data is None:
            return Response(
                {"error": f"Portfolio '{portfolio_name}' no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data)

class AvailableDatesView(APIView):
    def get(self, request):
        # Obtiene todas las fechas únicas de precios ordenadas
        dates_qs = Price.objects.order_by('date').values_list('date', flat=True).distinct()
        dates = list(dates_qs)
        if not dates:
            return Response({"error": "No hay fechas de precios disponibles."}, status=status.HTTP_404_NOT_FOUND)
        available = [d.isoformat() for d in dates]
        return Response({
            "min": available[0],
            "max": available[-1],
            "available": available,
        })


def home(request):
    portfolios = Portfolio.objects.all()
    return render(request, 'investments/home.html', {'portfolios': portfolios})
