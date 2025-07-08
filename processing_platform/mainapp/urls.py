import logging
from django.urls import path
from . import views

logger = logging.getLogger(__name__)
logger.debug("Loading mainapp.urls…")

urlpatterns = [
    path('', views.home_view, name='home'),
    path('sd-card/', views.sd_card_view, name='sd_card'),
    path('review_drone_flights/', views.review_drone_flights, name='review_drone_flights'),
    path('read-csv/', views.read_local_csv, name='read_local_csv'),
    path('weekly/', views.weekly_view, name='weekly'),
    path('details/', views.details_view, name='details'),
    path('add-routes/', views.add_routes_view, name='add_routes'),
]

logger.debug("Registered URL patterns: %s", [p.name for p in urlpatterns])
