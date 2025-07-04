from django.db import models


class Flight_Log(models.Model):
    FLIGHT_TYPE_CHOICES = [
        ("MS", "MS"),
        ("3D", "3D"),
        ("Thermal", "Thermal"),
        ("RGB", "RGB"),
    ]

    DRONE_MODEL_CHOICES = [
        ("M3M-1", "M3M-1"),
        ("M3M-2", "M3M-2"),
        ("M4T", "M4T"),
    ]

    DRONE_PILOT_CHOICES = [
        ("Ivar", "Ivar"),
        ("Frederic", "Frederic"),
        ("Christopher", "Christopher"),
        ("Kristoffer", "Kristoffer"),
        ("Ludvik", "Ludvik"),
        ("Jorgen", "Jorgen"),
        ("Fahad", "Fahad"),
        ("Other", "Other"),
    ]

    REFLECTANCE_PANEL_CHOICES = [
        ("New", "New"),
        ("Old", "Old"),
        ("Carpet", "Carpet"),
    ]

    YES_NO_CHOICES = [
        ("Yes", "Yes"),
        ("No", "No"),
    ]

    foldername = models.CharField(max_length=100, null=True, blank=True)
    flight_field_id = models.CharField(max_length=100, null=True, blank=True)
    project = models.CharField(max_length=100, null=True, blank=True)
    flight_type = models.CharField(
        max_length=10, choices=FLIGHT_TYPE_CHOICES, null=True, blank=True
    )

    drone_type = models.CharField(
        max_length=20, choices=DRONE_MODEL_CHOICES, null=True, blank=True
    )
    drone_pilot = models.CharField(
        max_length=20, choices=DRONE_PILOT_CHOICES, null=True, blank=True
    )
    reflectance_panel = models.CharField(
        max_length=10, choices=REFLECTANCE_PANEL_CHOICES, null=True, blank=True
    )

    flight_date = models.DateField(null=True, blank=True)
    flight_start = models.CharField(max_length=10, null=True, blank=True)
    flight_endstart = models.CharField(max_length=10, null=True, blank=True)
    flight_comments = models.CharField(max_length=200, null=True, blank=True)

    p4d_step1 = models.CharField(max_length=100, null=True, blank=True)
    p4d_step1_done_by = models.CharField(
        max_length=20, choices=DRONE_PILOT_CHOICES, null=True, blank=True
    )
    p4d_step1_workable_data = models.CharField(
        max_length=10, choices=YES_NO_CHOICES, null=True, blank=True
    )

    p4d_processing = models.CharField(
        max_length=10, choices=YES_NO_CHOICES, null=True, blank=True
    )
    p4d_processing_done_by = models.CharField(
        max_length=20, choices=DRONE_PILOT_CHOICES, null=True, blank=True
    )
    p4d_processing_pc = models.CharField(max_length=100, null=True, blank=True)
    p4d_processing_comments = models.CharField(max_length=200, null=True, blank=True)

    flight_height = models.CharField(max_length=10, null=True, blank=True)
    flight_side_over = models.CharField(max_length=10, null=True, blank=True)
    flight_front_over = models.CharField(max_length=10, null=True, blank=True)
    flight_wind_speed = models.CharField(max_length=10, null=True, blank=True)
    flight_drone_type = models.CharField(max_length=10, null=True, blank=True)

    new_folder_name = models.CharField(max_length=200, null=True, blank=True)
    root_folder = models.CharField(max_length=200, null=True, blank=True)
    flight_path = models.CharField(max_length=200, null=True, blank=True)
    p4d_path = models.CharField(max_length=200, null=True, blank=True)


class Fields(models.Model):
    YES_NO_CHOICES = [
        ("Yes", "Yes"),
        ("No", "No"),
    ]
    project = models.CharField(max_length=100, null=True, blank=True)
    short_id = models.CharField(max_length=100, null=True, blank=True)
    long_id = models.CharField(max_length=100, null=True, blank=True)
    crop = models.CharField(max_length=100, null=True, blank=True)
    location_of_field_plot = models.CharField(max_length=100, null=True, blank=True)
    multispectral = models.CharField(
        max_length=100, choices=YES_NO_CHOICES, null=True, blank=True
    )
    three_dimensional = models.CharField(
        max_length=100, choices=YES_NO_CHOICES, null=True, blank=True
    )
    thermal = models.CharField(
        max_length=100, choices=YES_NO_CHOICES, null=True, blank=True
    )
    rgb = models.CharField(
        max_length=100, choices=YES_NO_CHOICES, null=True, blank=True
    )
    flying_frequency = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    submission_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    project_number = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=300, null=True, blank=True)
    data_delivery_method = models.CharField(max_length=100, null=True, blank=True)
    vollebekk_responsible = models.CharField(max_length=100, null=True, blank=True)
    sowing_date = models.CharField(max_length=100, null=True, blank=True)
    measuring_ground_level = models.CharField(max_length=100, null=True, blank=True)


class Pilot(models.Model):
    name = models.CharField(max_length=100)


class Flight(models.Model):
    title = models.CharField(max_length=200)
    scheduled_time = models.DateTimeField()
    end_time = models.DateTimeField()
    flown = models.BooleanField(default=False)
    pilot = models.ForeignKey(Pilot, on_delete=models.SET_NULL, null=True, blank=True)
    frequency_days = models.IntegerField(default=7)  # e.g. should be flown every X days
