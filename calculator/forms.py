from django import forms
from .models import Bike

class BikeForm(forms.ModelForm):
    TIRE_SIZE_CHOICES = [
        ("3.00-17", "3.00-17"),
        ("3.25-17", "3.25-17"),
        ("3.50-17", "3.50-17"),
        ("120/80-17", "120/80-17"),
        ("130/90-15", "130/90-15"),
        ("130/70-17", "130/70-17"),
        ("140/70-17", "140/70-17"),
        ("150/60-17", "150/60-17"),
        ("160/60-17", "160/60-17"),
    ]

    tire_size = forms.ChoiceField(choices=TIRE_SIZE_CHOICES)

    class Meta:
        model = Bike
        fields = ['exhaust_type', 'air_filter_type', 'tire_size']
