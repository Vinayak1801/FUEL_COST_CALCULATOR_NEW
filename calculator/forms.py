from django import forms
from .models import Bike

class BikeForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = ['exhaust_type', 'air_filter_type', 'tire_size']
