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
        ("Mia", "Mia"),
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
        max_length=100, choices=FLIGHT_TYPE_CHOICES, null=True, blank=True
    )

    drone_type = models.CharField(
        max_length=20, choices=DRONE_MODEL_CHOICES, null=True, blank=True
    )
    drone_pilot = models.CharField(
        max_length=20, choices=DRONE_PILOT_CHOICES, null=True, blank=True
    )
    reflectance_panel = models.CharField(
        max_length=100, choices=REFLECTANCE_PANEL_CHOICES, null=True, blank=True
    )

    flight_date = models.DateField(null=True, blank=True)
    flight_start = models.CharField(max_length=100, null=True, blank=True)
    flight_endstart = models.CharField(max_length=100, null=True, blank=True)
    flight_date = models.DateField(null=True, blank=True)
    flight_comments = models.CharField(max_length=200, null=True, blank=True)

    p4d_step1 = models.CharField(max_length=100, null=True, blank=True)
    p4d_step1_done_by = models.CharField(
        max_length=20, choices=DRONE_PILOT_CHOICES, null=True, blank=True
    )
    p4d_step1_workable_data = models.CharField(
        max_length=100, choices=YES_NO_CHOICES, null=True, blank=True
    )

    p4d_processing = models.CharField(
        max_length=100, choices=YES_NO_CHOICES, null=True, blank=True
    )
    p4d_processing_done_by = models.CharField(
        max_length=20, choices=DRONE_PILOT_CHOICES, null=True, blank=True
    )
    p4d_processing_pc = models.CharField(max_length=100, null=True, blank=True)
    p4d_processing_comments = models.CharField(max_length=200, null=True, blank=True)

    flight_height = models.CharField(max_length=100, null=True, blank=True)
    flight_side_over = models.CharField(max_length=100, null=True, blank=True)
    flight_front_over = models.CharField(max_length=100, null=True, blank=True)
    flight_wind_speed = models.CharField(max_length=100, null=True, blank=True)
    flight_drone_type = models.CharField(max_length=100, null=True, blank=True)

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
    description = models.CharField(max_length=500, null=True, blank=True)
    data_delivery_method = models.CharField(max_length=100, null=True, blank=True)
    vollebekk_responsible = models.CharField(max_length=100, null=True, blank=True)
    sowing_date = models.CharField(max_length=100, null=True, blank=True)
    measuring_ground_level = models.CharField(max_length=100, null=True, blank=True)


class Flight_Paths(models.Model):
    record_number = models.IntegerField(db_column='#')

    project = models.CharField(max_length=100)
    short_id = models.CharField(max_length=50)
    project_folder_name = models.CharField(max_length=255)
    field_folder_name = models.CharField(max_length=255)
    flight_path_name = models.CharField(max_length=255)
    location_of_field_plot = models.CharField(max_length=255)
    type_of_flight = models.CharField(max_length=100)
    frequency = models.FloatField(null=True, blank=True)

    DRONE_MODEL_CHOICES = [
        ("M3M-1", "M3M-1"),
        ("M3M-2", "M3M-2"),
        ("M4T", "M4T"),
    ]
    
    drone_model = models.CharField(
       max_length=100,
       choices=DRONE_MODEL_CHOICES,
       help_text="One of M3M-1, M3M-2 or M4T"
   )
    flight_height = models.FloatField(null=True, blank=True)
    flight_speed = models.FloatField(null=True, blank=True)
    side_overlap = models.FloatField(null=True, blank=True)
    front_overlap = models.FloatField(null=True, blank=True)
    camera_angle = models.FloatField(null=True, blank=True)
    flight_pattern = models.CharField(max_length=100, null=True, blank=True)
    flight_path_angle = models.FloatField(null=True, blank=True)

    ortho_gsd = models.FloatField(db_column='Ortho GSD', null=True, blank=True)
    oblique_gsd = models.FloatField(db_column='Oblique GSD', null=True, blank=True)
    flight_length = models.FloatField(null=True, blank=True)
    ortho_gsd_pix4d = models.FloatField(db_column='Ortho GSD Pix4D', null=True, blank=True)
    oblique_gsd_pix4d = models.FloatField(db_column='Oblique GSD Pix4D', null=True, blank=True)

    first_flight_path = models.CharField(max_length=255, db_column='1_flight path')
    pix4d_path = models.CharField(max_length=255, db_column='2_1_pix4d path')

    class Meta:
        db_table = 'flight_paths'

class Sensor(models.Model):
    sensor_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.sensor_id


class SensorReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    soil_temperature = models.FloatField(null=True, blank=True)
    soil_moisture = models.FloatField(null=True, blank=True)
    air_temperature = models.FloatField(null=True, blank=True)
    air_humidity = models.FloatField(null=True, blank=True)
    battery = models.FloatField(null=True, blank=True)
    rainfall = models.FloatField(null=True, blank=True)

    crop_type = models.CharField(max_length=100, blank=True)
    soil_type = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("sensor", "timestamp")

    def __str__(self):
        return f"{self.sensor.sensor_id} @ {self.timestamp}"

"""
STAT_FIELDS = [
    "cv", "iqr", "kurtosis", "majority", "max", "mean", "median", "min", "minority",
    "q25", "q75", "range", "skewness", "std", "sum", "top_10", "top_10_mean", "top_10_median", "top_10_std",
    "top_15", "top_15_mean", "top_15_median", "top_15_std",
    "top_20", "top_25", "top_25_mean", "top_25_median", "top_25_std",
    "top_35", "top_35_mean", "top_35_median", "top_35_std",
    "top_50", "top_50_mean", "top_50_median", "top_50_std",
    "top_5_mean", "top_5_median", "top_5_std", "variance", "variety",
]
"""

class Field_visualisation(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class ZonalStat(models.Model):
    field = models.ForeignKey(
        Field_visualisation, on_delete=models.PROTECT, null=True, blank=True, db_index=True
    )
    idx = models.IntegerField()
    location = models.CharField(max_length=100)
    camera = models.CharField(max_length=100)
    flight_height = models.CharField(max_length=20)
    project = models.CharField(max_length=100)
    flight = models.CharField(max_length=200)
    date = models.DateField()
    spectrum = models.CharField(max_length=50)

    count = models.IntegerField()
    cv = models.FloatField()
    iqr = models.FloatField()
    kurtosis = models.FloatField()
    majority = models.FloatField()
    maximum = models.FloatField()
    mean = models.FloatField()
    median = models.FloatField()
    minimum = models.FloatField()
    minority = models.FloatField()
    q25 = models.FloatField()
    q75 = models.FloatField()
    range_stat = models.FloatField()
    skewness = models.FloatField()
    std = models.FloatField()
    sum_stat = models.FloatField()

    top_10 = models.FloatField()
    top_10_mean = models.FloatField()
    top_10_median = models.FloatField()
    top_10_std = models.FloatField()

    top_15 = models.FloatField()
    top_15_mean = models.FloatField()
    top_15_median = models.FloatField()
    top_15_std = models.FloatField()

    top_20 = models.FloatField()

    top_25 = models.FloatField()
    top_25_mean = models.FloatField()
    top_25_median = models.FloatField()
    top_25_std = models.FloatField()

    top_35 = models.FloatField()
    top_35_mean = models.FloatField()
    top_35_median = models.FloatField()
    top_35_std = models.FloatField()

    top_50 = models.FloatField()
    top_50_mean = models.FloatField()
    top_50_median = models.FloatField()
    top_50_std = models.FloatField()

    top_5_mean = models.FloatField()
    top_5_median = models.FloatField()
    top_5_std = models.FloatField()

    variance = models.FloatField()
    variety = models.IntegerField()

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["date", "idx", "spectrum"],
                name="uniq_date_idx_spectrum",
            ),
        ]
    

