from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('admin_panel', views.admin_panel, name ='admin_panel'),
    path('sd-card/', views.sd_card_view, name='sd_card'),
    path('weekly/', views.weekly_view, name='weekly'),
    re_path(r"^weekly/(?P<week_offset>-?\d+)/$", views.weekly_view, name="weekly_with_offset"),
    path('details/', views.details_view, name='details'),
    path('add-routes/', views.add_routes_view, name='add_routes'),
]
