from django import forms
from django.forms import (
    formset_factory,
    BaseFormSet,
    ClearableFileInput,
)
from .models import Flight_Paths

class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class FlightForm(forms.Form):
    # track folder name (basename of DJI_… directory)
    folder_name      = forms.CharField(widget=forms.HiddenInput())
    flight_path_key  = forms.CharField(widget=forms.HiddenInput())
    flight_dir       = forms.CharField(widget=forms.HiddenInput())
    skyline_names    = forms.CharField(widget=forms.HiddenInput(), required=False)

    pilot = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full border-gray-300 rounded-md p-2 "
                         "focus:ring-nmbu-green focus:border-nmbu-green shadow-sm",
                "placeholder": "Pilot name",
            }
        ),
    )

    drone_model = forms.ChoiceField(
        required=False,
        choices=Flight_Paths.DRONE_MODEL_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "mt-1 block w-full border-gray-300 rounded-md p-2 "
                         "focus:ring-nmbu-green focus:border-nmbu-green shadow-sm bg-white",
            }
        ),
        label="Drone model",
    )

    wind_speed1 = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "w-1/3 p-2 border-gray-300 rounded-md shadow-sm "
                         "focus:ring-nmbu-green focus:border-nmbu-green",
                "step": "0.1",
            }
        ),
    )
    wind_speed2 = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "w-1/3 p-2 border-gray-300 rounded-md shadow-sm "
                         "focus:ring-nmbu-green focus:border-nmbu-green",
                "step": "0.1",
            }
        ),
    )
    wind_speed3 = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "w-1/3 p-2 border-gray-300 rounded-md shadow-sm "
                         "focus:ring-nmbu-green focus:border-nmbu-green",
                "step": "0.1",
            }
        ),
    )

    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "mt-1 block w-full border-gray-300 rounded-md p-2 h-24 resize-none "
                         "focus:ring-nmbu-green focus:border-nmbu-green shadow-sm",
            }
        ),
    )

    skyline_files = forms.FileField(
        required=False,
        error_messages={"required": ""},
        widget=MultiFileInput(
            attrs={
                "class": "mt-1 block w-full file:border file:border-gray-300 "
                         "file:rounded-md file:px-3 file:py-2 file:bg-nmbu-green "
                         "file:text-white hover:file:bg-nmbu-dark focus:ring-nmbu-green "
                         "focus:border-nmbu-green shadow-sm",
                "multiple": True,
                "accept": "image/jpeg",
                "webkitdirectory": True,    # open DJI folder
            }
        ),
    )

    reflectance_dir = forms.FileField(
        required=False,
        error_messages={"required": ""},
        widget=ClearableFileInput(
            attrs={
                "class": "mt-1 block w-full border-gray-300 rounded-md p-2 "
                         "focus:ring-nmbu-green focus:border-nmbu-green shadow-sm",
                "webkitdirectory": True,    # open DCIM folder
            }
        ),
        label="Reflectance panel folder",
    )

    def clean_skyline_files(self):
        """Return list of uploaded skyline files, defaulting to []"""
        prefix = self.add_prefix("skyline_files")
        return self.files.getlist(prefix)

    def clean(self):
        cleaned = super().clean()
        # suppress empty-file errors
        if "skyline_files" in self.errors:
            errs = self.errors.get("skyline_files")
            if errs and all("No file was submitted" in str(e) for e in errs):
                self.errors.pop("skyline_files")
        return cleaned

class CleanEmptyFilesFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if "skyline_files" in form.errors:
                errs = form.errors.get("skyline_files")
                if errs and all("No file was submitted" in str(e) for e in errs):
                    form.errors.pop("skyline_files")

FlightFormSet = formset_factory(
    FlightForm,
    formset=CleanEmptyFilesFormSet,
    extra=0,
)
