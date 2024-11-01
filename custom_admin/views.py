from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from calculator.models import BikeModel, FuelPrice, BikeBrand 
from django.contrib.auth.models import User
from django import forms
from django.contrib import messages
from decimal import Decimal
import json

from calculator.models import Trip,Bike


# Restrict access to superusers only
def admin_only(user):
    return user.is_superuser

@user_passes_test(admin_only)
def dashboard(request):
    bikes = BikeModel.objects.all()  # Assuming this is what you want to show
    users = User.objects.all()
    bikes = Bike.objects.select_related('owner').all()
    return render(request, 'custom_admin/dashboard.html', {'bikes': bikes, 'users': users})


def view_bikes_users(request):
    bikes = Bike.objects.select_related('owner').all()  # Fetch all bikes with user details
    return render(request, 'custom_admin/view_bikes_users.html', {'bikes': bikes})

def delete_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id)
    bike.delete()
    return redirect('custom_admin:view_bikes_users')

@user_passes_test(admin_only)
def manage_bikes(request):
    bike_models = BikeModel.objects.all()
    bike_brands = BikeBrand.objects.all()  # Fetch all bike brands

    if request.method == 'POST':
        # Check for adding a bike model
        if 'model_name' in request.POST:
            model_name = request.POST.get('model_name')
            brand_id = request.POST.get('brand')
            fuel_efficiency = request.POST.get('fuel_efficiency')
            image = request.FILES.get('image')

            BikeModel.objects.create(
                model_name=model_name,
                brand_id=brand_id,
                fuel_efficiency=fuel_efficiency,
                image=image
            )
            return redirect('custom_admin:manage_bikes')

        # Check for adding a bike brand
        elif 'brand_name' in request.POST:
            brand_name = request.POST.get('brand_name')
            BikeBrand.objects.create(brand_name=brand_name)
            return redirect('custom_admin:manage_bikes')

    return render(request, 'custom_admin/manage_bikes.html', {
        'bike_models': bike_models,
        'bike_brands': bike_brands
    })
@user_passes_test(admin_only)
def add_bike_model(request):
    if request.method == 'POST':
        name = request.POST.get('model_name')  # Ensure this matches your form field name
        brand_id = request.POST.get('brand')  # Assume you have a dropdown for brand
        fuel_efficiency = request.POST.get('fuel_efficiency')
        image = request.FILES.get('image')  # For image upload

        # Create new BikeModel
        BikeModel.objects.create(
            model_name=name,
            brand_id=brand_id,
            fuel_efficiency=fuel_efficiency,
            image=image
        )
        return redirect('custom_admin:manage_bikes')

    return render(request, 'custom_admin/add_bike_model.html')  # Create this template for the form

@user_passes_test(admin_only)
def edit_bike_model(request, bike_model_id):
    bike_model = get_object_or_404(BikeModel, id=bike_model_id)
    bike_brands = BikeBrand.objects.all()  # Get all bike brands
    
    if request.method == 'POST':
        bike_model.model_name = request.POST.get('model_name')
        bike_model.brand_id = request.POST.get('brand')
        bike_model.fuel_efficiency = request.POST.get('fuel_efficiency')
        
        if 'image' in request.FILES:  # Check if an image is uploaded
            bike_model.image = request.FILES['image']
        
        bike_model.save()
        return redirect('custom_admin:manage_bikes')

    return render(request, 'custom_admin/edit_bike_model.html', {
        'bike_model': bike_model,
        'bike_brands': bike_brands  # Pass bike brands to the template
    })

@user_passes_test(admin_only)
def delete_bike_model(request, bike_model_id):
    bike_model = get_object_or_404(BikeModel, id=bike_model_id)
    bike_model.delete()
    return redirect('custom_admin:manage_bikes')

@user_passes_test(admin_only)
def manage_fuel_price(request):
    fuel_prices = FuelPrice.objects.all().order_by('-id')
    fuel_data = FuelPrice.objects.all().order_by('effective_date')
    # Convert data into JSON format for the JavaScript chart
    history_data = json.dumps({
        "dates": [fp.effective_date.strftime('%Y-%m-%d') for fp in fuel_data],
        "prices": [float(fp.price) for fp in fuel_data],
    })
    return render(request, 'custom_admin/manage_fuel_price.html', {'fuel_prices': fuel_prices,'history_data':history_data})

@user_passes_test(admin_only)
def add_fuel_price(request):
    if request.method == 'POST':
        price = request.POST.get('price')
        print(f"Received price: {price}") 
        if price:  # Check if price is provided
            try:
                # Convert price to Decimal and create FuelPrice instance
                fuel_price = FuelPrice.objects.create(price=Decimal(price))
                return redirect('custom_admin:manage_fuel_price')
            except Exception as e:
                # Handle any exceptions (e.g., invalid input)
                messages.error(request, f"Error adding price: {str(e)}")
        else:
            messages.error(request, "Please enter a valid price.")
    
    return render(request, 'custom_admin')  # Create this template for the form


@user_passes_test(admin_only)
def edit_fuel_price(request, fuel_price_id):
    fuel_price = get_object_or_404(FuelPrice, id=fuel_price_id)
    
    
    if request.method == 'POST':
        fuel_price.price = request.POST.get('price')
        fuel_price.save()
        return redirect('custom_admin:manage_fuel_price')

    return render(request, 'custom_admin/edit_fuel_price.html', {'fuel_price': fuel_price})

@user_passes_test(admin_only)
def delete_fuel_price(request, fuel_price_id):
    fuel_price = get_object_or_404(FuelPrice, id=fuel_price_id)
    fuel_price.delete()
    return redirect('custom_admin:manage_fuel_price')


@user_passes_test(admin_only)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('custom_admin:admin_dashboard')


@user_passes_test(admin_only)
def manage_trips(request):
    # Fetch all trips
    trips = Trip.objects.all().order_by('-trip_date')  # Order trips by trip_date, latest first
    return render(request, 'custom_admin/manage_trips.html', {'trips': trips})


@user_passes_test(admin_only)
def delete_trip(request, trip_id):
    # Fetch the trip using the trip_id
    trip = get_object_or_404(Trip, id=trip_id)
    trip.delete()  # Delete the trip
    return redirect('custom_admin:manage_trips')
