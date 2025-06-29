from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('sd-card/', views.sd_card_view, name='sd_card'),
    
    
]
