from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('sd-card/', views.sd_card_view, name='sd_card'),
    path('review_drone_flights/', views.review_drone_flights, name='review_drone_flights'),
    path("read-csv/", views.read_local_csv),
    path('weekly/', views.weekly_view, name='weekly'),
    path('details/', views.details_view, name='details'),
    path('add-routes/', views.add_routes_view, name='add_routes'),
    path('visualise/', views.data_visualisation, name='data_visualisation'),
]
