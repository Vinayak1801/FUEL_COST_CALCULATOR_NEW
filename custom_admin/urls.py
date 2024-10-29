from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    
    # Bike Management URLs
    path('manage_bikes/', views.manage_bikes, name='manage_bikes'),
    path('manage_bikes/add/', views.add_bike_model, name='add_bike_model'),
    path('manage_bikes/edit/<int:bike_model_id>/', views.edit_bike_model, name='edit_bike_model'),
    path('manage_bikes/delete/<int:bike_model_id>/', views.delete_bike_model, name='delete_bike_model'),

    path('view_bikes_users/', views.view_bikes_users, name='view_bikes_users'),
    path('delete_bike/<int:bike_id>/', views.delete_bike, name='delete_bike'),
    
    # Fuel Price Management URLs
    path('manage_fuel_price/', views.manage_fuel_price, name='manage_fuel_price'),
    path('manage_fuel_price/add/', views.add_fuel_price, name='add_fuel_price'),
    path('manage_fuel_price/edit/<int:fuel_price_id>/', views.edit_fuel_price, name='edit_fuel_price'),
    path('manage_fuel_price/delete/<int:fuel_price_id>/', views.delete_fuel_price, name='delete_fuel_price'),


    # user management
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),


    path('manage_trips/', views.manage_trips, name='manage_trips'),
    path('delete_trip/<int:trip_id>/', views.delete_trip, name='delete_trip'), 
]
