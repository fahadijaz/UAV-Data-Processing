# mainapp/forms.py
from django import forms
from django.forms.widgets import ClearableFileInput, TextInput, NumberInput, Textarea, Select
from .models import Flight_Log

class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class FlightForm(forms.Form):
    # hidden fields
    flight_path_key = forms.CharField(widget=forms.HiddenInput())
    flight_dir      = forms.CharField(widget=forms.HiddenInput())

    # metadata
    pilot = forms.CharField(
        label="Pilot",
        widget=TextInput(attrs={
            "class": "mt-1 block w-full border-gray-300 rounded-md p-2 focus:ring-nmbu-green focus:border-nmbu-green"
        })
    )
    drone_model = forms.ChoiceField(
        label="Drone model",
        choices=Flight_Log.DRONE_MODEL_CHOICES,
        widget=Select(attrs={
            "class": "mt-1 block w-full border-gray-300 rounded-md p-2 focus:ring-nmbu-green focus:border-nmbu-green"
        })
    )
    wind_speed1 = forms.IntegerField(
        label="Wind speed 1 (m/s)",
        widget=NumberInput(attrs={
            "class": "w-1/3 border-gray-300 rounded-md p-2 focus:ring-nmbu-green focus:border-nmbu-green",
            "min": "0"
        })
    )
    wind_speed2 = forms.IntegerField(
        label="Wind speed 2 (m/s)",
        widget=NumberInput(attrs={
            "class": "w-1/3 border-gray-300 rounded-md p-2 focus:ring-nmbu-green focus:border-nmbu-green",
            "min": "0"
        })
    )
    wind_speed3 = forms.IntegerField(
        label="Wind speed 3 (m/s)",
        widget=NumberInput(attrs={
            "class": "w-1/3 border-gray-300 rounded-md p-2 focus:ring-nmbu-green focus:border-nmbu-green",
            "min": "0"
        })
    )
    comments = forms.CharField(
        required=False,
        label="Comments",
        widget=Textarea(attrs={
            "class": "mt-1 block w-full border-gray-300 rounded-md p-2 h-24 resize-none focus:ring-nmbu-green focus:border-nmbu-green"
        })
    )

    # file fields
    skyline_files = forms.FileField(
        required=False,
        label="Select skyline images",
        widget=MultiFileInput(attrs={
            "multiple": "multiple",
            "accept":   "image/jpeg",
            "class":    "mt-1 block w-full file:border file:border-gray-300 file:rounded-md file:px-3 file:py-2 file:bg-nmbu-green file:text-white hover:file:bg-nmbu-dark focus:ring-nmbu-green focus:border-nmbu-green"
        }),
    )
    skyline_names = forms.CharField(widget=forms.HiddenInput(), required=False)

    reflectance_dir = forms.FileField(
        required=False,
        label="Reflectance panel (MS only)",
        widget=forms.FileInput(attrs={
            "class": "mt-1 block w-full file:border file:border-gray-300 file:rounded-md file:px-3 file:py-2 hover:file:bg-gray-50 focus:ring-nmbu-green focus:border-nmbu-green"
        }),
    )
