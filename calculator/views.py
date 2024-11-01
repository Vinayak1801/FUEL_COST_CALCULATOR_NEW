from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Import messages for user feedback
from .models import Bike, Trip, MaintenanceSchedule, BikeModel, FuelPrice,BikeBrand  
from django.utils import timezone
import requests
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from .forms import BikeForm
import re

# Registration View
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        email = request.POST['email']

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken. Please choose another one.")
            return render(request, 'calculator/register.html', {'show_signup': True})
        
        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken. Please choose another one.")
            return render(request, 'calculator/register.html', {'show_signup': True})

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
            return render(request, 'calculator/register.html', {'show_signup': True, 'username': username, 'email': email})

        # Validate password strength
        if not is_valid_password(password):
            messages.error(request, "Password must be at least 8 characters long and include uppercase, lowercase, digits, and special characters.")
            return render(request, 'calculator/register.html', {'show_signup': True, 'username': username, 'email': email})

        # Create the user
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        return redirect('calculator:login')
    
    return render(request, 'calculator/login.html')



def is_valid_password(password):
    # Password must be at least 8 characters long
    if len(password) < 8:
        return False
    # At least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False
    # At least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False
    # At least one digit
    if not re.search(r'\d', password):
        return False
    # At least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

# Login View
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

def user_login(request):
    if request.method == 'POST':
        identifier = request.POST['username']  # This can be either username or email
        password = request.POST['password']

        # Check if the identifier is an email by looking up the User model
        try:
            if '@' in identifier:
                user_obj = User.objects.get(email=identifier)
                username = user_obj.username
            else:
                username = identifier
        except User.DoesNotExist:
            return render(request, 'calculator/login.html', {'error': 'Invalid username or password'})

        # Authenticate using the determined username
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            # Check if the user is an admin (staff)
            if user.is_staff:
                return redirect('custom_admin:admin_dashboard')  # Redirect to custom admin dashboard
            else:
                return redirect('calculator:dashboard')  # Redirect to user dashboard
        else:
            return render(request, 'calculator/login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'calculator/login.html')


# Logout View
@login_required
def user_logout(request):
    logout(request)
    return redirect('calculator:login')

# Dashboard View
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def dashboard(request):
    bikes = Bike.objects.filter(owner=request.user).order_by('-id')[:3]
    trips = Trip.objects.filter(owner=request.user).order_by('-id')[:3]
    fuel_cost_per_liter = float(get_current_fuel_price())
    b = Bike.objects.filter(owner=request.user)
    t = Trip.objects.filter(owner=request.user)
    fuel_data = FuelPrice.objects.all().order_by('effective_date')
    # Convert data into JSON format for the JavaScript chart
    history_data = json.dumps({
        "dates": [fp.effective_date.strftime('%Y-%m-%d') for fp in fuel_data],
        "prices": [float(fp.price) for fp in fuel_data],
    })
    
    return render(request, 'calculator/dashboard.html', {'bikes': bikes, 'trips': trips,'b':b,'t':t,'fc':fuel_cost_per_liter,'history_data': history_data})

@login_required
def add_bike(request):
    if request.method == 'POST':
        model_id = request.POST['model']  # Get bike model ID from the form
        exhaust_type = request.POST['exhaust_type']
        air_filter_type = request.POST['air_filter_type']
        tire_size = request.POST['tire_size']
        vehicle_number = request.POST['vehicle_number']  # Get vehicle number from form
        
        last_service_date = request.POST.get('last_service_date')
        if not last_service_date:  # If the field is empty, set default date (or None)
            last_service_date = timezone.now().date()
        # Check if the vehicle number already exists
        if Bike.objects.filter(vehicle_number=vehicle_number).exists():
            messages.error(request, 'This vehicle number is already registered.')
            return redirect('calculator:add_bike')

        try:
            bike_model = BikeModel.objects.get(id=model_id)
        except BikeModel.DoesNotExist:
            messages.error(request, 'Bike model does not exist.')
            return redirect('calculator:add_bike')

        # Create the bike object
        bike = Bike(
            owner=request.user,
            model=bike_model,
            exhaust_type=exhaust_type,
            air_filter_type=air_filter_type,
            tire_size=tire_size,
            vehicle_number=vehicle_number,
            last_service_date=last_service_date
        )
        bike.save()
        messages.success(request, 'Bike successfully added!')
        return redirect('calculator:dashboard')

    # Get all available bike brands
    brands = BikeBrand.objects.all()
    return render(request, 'calculator/add_bike.html', {'brands': brands})

def get_bike_models(request):
    brand_id = request.GET.get('brand_id')
    models = BikeModel.objects.filter(brand_id=brand_id)
    model_options = '<option value="" disabled selected>Select a bike model</option>'
    for model in models:
        model_options += f'<option value="{model.id}">{model.model_name}</option>'
    return JsonResponse(model_options, safe=False)

# View Bike Details
@login_required
def view_bike(request, bike_id):
    bike = Bike.objects.get(id=bike_id, owner=request.user)
    return render(request, 'calculator/view_bike.html', {'bike': bike})

#both above and below are 2 different functions
@login_required
def view_bikes(request):
    # Fetch all bikes owned by the user
    bikes = Bike.objects.filter(owner=request.user)
    return render(request, 'calculator/view_bikes.html', {'bikes': bikes})


# Delete Bike
@login_required
def delete_bike(request, bike_id):
    bike = Bike.objects.get(id=bike_id, owner=request.user)
    bike.delete()
    return redirect('calculator:dashboard')

# Calculate Fuel Cost View
@login_required
def calculate_fuel_cost(request):
    if request.method == 'POST':
        print("POST Data:", request.POST)
        start_location = request.POST.get('start_location')
        end_location = request.POST.get('end_location')
        selected_bike_id = request.POST.get('bike')
        
        print("uw")
        user_weight = float(request.POST.get('user_weight', 60))  # Get user weight, default to 60

        # Check if selected_bike_id exists in POST data
        if not selected_bike_id:
            print("No bike selected")
            return render(request, 'calculator/calculate_fuel.html', {'error': 'Please select a bike.'})

        try:
            print("bike not selected")
            selected_bike = Bike.objects.get(id=selected_bike_id)
            print("bike selected")
        except Bike.DoesNotExist:
            print("4")
            return render(request, 'calculator/calculate_fuel.html', {'error': 'Selected bike does not exist.'})

        # Get latitude and longitude for the start and end locations
        start_lat, start_lon = get_lat_lon(start_location)
        end_lat, end_lon = get_lat_lon(end_location)
        print(f"Start Coordinates: {start_lat}, {start_lon}")
        print(f"End Coordinates: {end_lat}, {end_lon}")

        if start_lat is None or end_lat is None:
            print("location error")
            return render(request, 'calculator/calculate_fuel.html', {'error': 'Could not find one or both locations. Please check and try again.'})

        # Get the distance between the two locations 
        distance = get_distance_google(start_lat, start_lon, end_lat, end_lon)
        if distance is None:
            print("fetching distance error")
            return render(request, 'calculator/calculate_fuel.html', {'error': 'Could not calculate distance. Please try again.'})

       
        # Fetch the default fuel efficiency from the bike model
        default_fuel_efficiency = selected_bike.model.fuel_efficiency

        # Calculate the adjusted fuel efficiency based on rider weight and other factors
        fuel_efficiency = calculate_fuel_efficiency(selected_bike, default_fuel_efficiency, user_weight)  # Adjusted

        print(f"Start Location: {start_location}, End Location: {end_location}, Distance: {distance}")
        print(f"Default Fuel Efficiency: {default_fuel_efficiency}, User Weight: {user_weight}, Calculated Fuel Efficiency: {fuel_efficiency}")

        # Get the current fuel price
        fuel_cost_per_liter = float(get_current_fuel_price())  # Convert Decimal to float

        # Calculate total fuel needed and total cost
        total_fuel_needed = distance / fuel_efficiency
        total_cost = total_fuel_needed * fuel_cost_per_liter

        trip_date= timezone.now().date()

        print(f"Total Fuel Needed: {total_fuel_needed}, Total Cost: {total_cost}")

       
        return render(request, 'calculator/trip_result.html', {
            'owner':request.user,
            'bike':selected_bike,
            'start_location': start_location,
            'end_location': end_location,
            'distance': distance,
            'total_cost': total_cost,
            'rider_weight': user_weight,
            'calculated_FE':fuel_efficiency,
            'trip_date':trip_date,
        })

    # If not POST, or after processing the POST request
    bikes = Bike.objects.filter(owner=request.user)
    return render(request, 'calculator/calculate_fuel.html', {'bikes': bikes})

# Function to calculate adjusted fuel efficiency
def calculate_fuel_efficiency(bike, default_fuel_efficiency, rider_weight):
    # Start with the default fuel efficiency
    fuel_efficiency = default_fuel_efficiency

    # Adjust based on rider weight (if the weight exceeds 60 kg, reduce fuel efficiency)
    if rider_weight > 60:
        fuel_efficiency -= (rider_weight - 60) * 0.05  # Reduce 0.05 km/l for every kg above 60

    # Further adjustments based on bike exhaust type and air filter type
    if bike.exhaust_type == 'Aftermarket':
        fuel_efficiency -= 1  # Aftermarket exhaust reduces fuel efficiency
    if bike.air_filter_type == 'High Performance':
        fuel_efficiency += 1  # High-performance air filter increases fuel efficiency

    # Adjust based on tire size
    tire_size_adjustments = {
        "3.00-17": 0,
        "3.25-17": 0,
        "3.50-17": 0,
        "120/80-17": -1,
        "130/90-15": -1,
        "130/70-17": -1,
        "140/70-17": -1,
        "150/60-17": -1,
        "160/60-17": -1,
    }

    # Apply adjustments based on the selected tire size
    if bike.tire_size in tire_size_adjustments:
        fuel_efficiency += tire_size_adjustments[bike.tire_size]


    # Ensure fuel efficiency does not go below a certain minimum threshold
    if fuel_efficiency < 20:
        fuel_efficiency = 20  # Minimum fuel efficiency threshold

    return fuel_efficiency

#Trip save function
from datetime import datetime
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

@login_required
def save_trip(request):
    if request.method == 'POST':
        start_location = request.POST.get('start_location')
        end_location = request.POST.get('end_location')
        distance = float(request.POST.get('distance'))
        total_cost = float(request.POST.get('total_cost'))
        rider_weight = float(request.POST.get('rider_weight'))
        calculated_FE = float(request.POST.get('calculated_FE'))
        bike_id = request.POST.get('bike')  # Make sure you also send the bike ID
        trip_date_str = request.POST.get('trip_date')

        # Convert the trip_date to the correct format
        try:
            trip_date = datetime.strptime(trip_date_str, '%b.  %d, %Y').date()  # Expecting format "Oct. 22, 2024"
        except ValueError:
            messages.error(request, 'Invalid date format. Please use "Oct. 22, 2024" format.')
            return redirect('calculator:calculate_fuel')

        selected_bike = get_object_or_404(Bike, id=bike_id, owner=request.user)
        
        trip = Trip(
            owner=request.user,
            bike=selected_bike,
            start_location=start_location,
            end_location=end_location,
            distance=distance,
            fuel_cost=total_cost,
            rider_weight=rider_weight,
            trip_date=trip_date
        )
        trip.save()

        messages.success(request, 'Trip saved successfully!')
        return redirect('calculator:dashboard')

    return redirect('calculator:calculate_fuel')


GOOGLE_MAPS_API_KEY = 'AlzaSySd6mOQXEqrTycBAPUbAri-aTAomUQ4O_v'  # Replace with your API key

# Get latitude and longitude using Google Maps Geocoding API
def get_lat_lon(location):
    url = f'https://maps.gomaps.pro/maps/api/geocode/json?address={location}&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            lat = data['results'][0]['geometry']['location']['lat']
            lon = data['results'][0]['geometry']['location']['lng']
            return lat, lon
    return None, None  # Return None if location is not found




# Fetch distance using Google Maps Distance Matrix API
def get_distance_google(start_lat, start_lon, end_lat, end_lon):
    url = f'https://maps.gomaps.pro/maps/api/distancematrix/json?units=metric&origins={start_lat},{start_lon}&destinations={end_lat},{end_lon}&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'rows' in data and data['rows']:
            distance = data['rows'][0]['elements'][0]['distance']['value'] / 1000  # Convert meters to kilometers
            return distance
    return None


# Simple function to calculate fuel efficiency based on bike attributes
# Simple function to calculate fuel efficiency based on bike attributes and user weight



# Get current fuel price (can be static for demo purposes)
def get_current_fuel_price():
    fuel_price = FuelPrice.objects.order_by('-effective_date', '-id').first()  # Get the most recent fuel price
    print(f"fuelprice:{fuel_price}")
    return fuel_price.price if fuel_price else 100.0  # Default to 100 if no price exists

# Maintenance Reminder View
# @login_required
# def maintenance_reminder(request):
#     bikes = Bike.objects.filter(owner=request.user)
#     upcoming_services = []
#     for bike in bikes:
#         schedules = MaintenanceSchedule.objects.filter(bike=bike, service_date__gte=timezone.now())
#         for schedule in schedules:
#             if not schedule.reminder_sent:
#                 upcoming_services.append(schedule)
#                 schedule.reminder_sent = True
#                 schedule.save()
#     return render(request, 'calculator/maintenance_reminder.html', {'services': upcoming_services})

from datetime import timedelta

@login_required
def maintenance_reminder(request):
    bikes = Bike.objects.filter(owner=request.user)
    upcoming_services = []
    today = timezone.now().date()  # Get the current date

    for bike in bikes:
        # Get the last service date or bike's addition date
        last_service_date = bike.last_service_date 

        # Calculate the next service due date (every 3 months)
        next_service_due = last_service_date + timedelta(days=90)

        # Check if the service is overdue or upcoming
        if today > next_service_due:
            status = 'Overdue'
        else:
            status = 'Upcoming'

        upcoming_services.append({
            'bike': bike,
            'due_date': next_service_due,
            'status': status
        })

    return render(request, 'calculator/maintenance_reminder.html', {'services': upcoming_services})

@login_required
def mark_service_done(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id, owner=request.user)
    
    # Update the last_service_date to today
    bike.last_service_date = timezone.now().date()
    bike.save()
    
    messages.success(request, f"Service for {bike.model.model_name} marked as done.")
    return redirect('calculator:maintenance_reminder')
#tripssss
@login_required
def view_trips(request):
    # Fetch all trips by the user
    trips = Trip.objects.filter(owner=request.user).order_by('-trip_date', '-id')
    return render(request, 'calculator/view_trips.html', {'trips': trips})

def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    trip.delete()  # Delete the trip
    return redirect('calculator:view_trips')


@login_required
def edit_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id, owner=request.user)

    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES, instance=bike)
        if form.is_valid():
            form.save()
            return redirect('calculator:dashboard')
    else:
        form = BikeForm(instance=bike)

    return render(request, 'calculator/edit_bike.html', {'form': form, 'bike': bike})

import json

@login_required
def fuel_history(request):
    # Fetch fuel history data, ordering by the effective date
    fuel_data = FuelPrice.objects.all().order_by('effective_date')
    # Convert data into JSON format for the JavaScript chart
    history_data = json.dumps({
        "dates": [fp.effective_date.strftime('%Y-%m-%d') for fp in fuel_data],
        "prices": [float(fp.price) for fp in fuel_data],
    })
    
    return render(request, 'calculator/fuel_history.html', {'history_data': history_data})