from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('sd-card/', views.sd_card_view, name='sd_card'),
    path('weekly/', views.weekly_view, name='weekly'),
    path('details/', views.details_view, name='details'),
    path('add-routes/', views.add_routes_view, name='add_routes'),
]
