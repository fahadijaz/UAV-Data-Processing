# In your forms.py file
from django import forms
from .models import Flight_Log

class FlightForm(forms.Form):
    folder_name = forms.CharField(widget=forms.HiddenInput())
    flight_path_key = forms.CharField(widget=forms.HiddenInput())
    flight_dir = forms.CharField(widget=forms.HiddenInput())
    
    # Skyline images field - users can enter comma or space separated filenames
    skyline_names = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. DJI_0001.JPG, DJI_0002.JPG',
            'class': 'form-control',
        }),
        help_text='Enter image filenames separated by commas or spaces (optional)'
    )

    reflectance_dir = forms.CharField(
        required=False,
        widget=forms.HiddenInput(), 
        help_text='Select the reflectance panel folder (optional)'
    )
    
    pilot = forms.ChoiceField(
        choices=[('', 'Select Pilot')] + Flight_Log.DRONE_PILOT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    drone_model = forms.ChoiceField(
        choices=[('', 'Select Model')] + Flight_Log.DRONE_MODEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    wind_speed1 = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    wind_speed2 = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    wind_speed3 = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    
    def clean_skyline_names(self):
        """Clean and validate skyline image names"""
        skyline_names = self.cleaned_data.get('skyline_names', '')
        if not skyline_names:
            return ''
        
        valid_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.dng'}
        names = []
        
        for name in skyline_names.replace(',', ' ').split():
            name = name.strip()
            if name:
                if any(name.lower().endswith(ext) for ext in valid_extensions):
                    names.append(name)
                else:
                    if '.' not in name:
                        names.append(f"{name}.JPG")
                    else:
                        names.append(name)
        
        return ', '.join(names)