from django.db import models


class Pilot(models.Model):
    name = models.CharField(max_length=100)


class Flight(models.Model):
    title = models.CharField(max_length=200)
    scheduled_time = models.DateTimeField()
    end_time = models.DateTimeField()
    flown = models.BooleanField(default=False)
    pilot = models.ForeignKey(Pilot, on_delete=models.SET_NULL, null=True, blank=True)
    frequency_days = models.IntegerField(default=7)  # e.g. should be flown every X days


class Sensor(models.Model):
    sensor_id = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.sensor_id


class Sensor(models.Model):
    sensor_id = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.sensor_id


class SensorReading(models.Model):
    sensor = models.ForeignKey(
        Sensor, on_delete=models.CASCADE, related_name="readings"
    )
    timestamp = models.DateTimeField()

    soil_temperature = models.FloatField(null=True, blank=True)  # Jordtemperatur
    soil_moisture = models.FloatField(null=True, blank=True)  # Jordfuktighet
    air_temperature = models.FloatField(null=True, blank=True)  # Lufttemperatur
    air_humidity = models.FloatField(null=True, blank=True)  # Luftfuktighet
    battery = models.FloatField(null=True, blank=True)  # Batteri
    rainfall = models.FloatField(null=True, blank=True)  # Regnmengde
    crop_type = models.CharField(max_length=100, blank=True)  # Vekst
    soil_type = models.CharField(max_length=100, blank=True)  # Jordtype

    class Meta:
        unique_together = ("sensor", "timestamp")

    def __str__(self):
        return f"{self.sensor.sensor_id} - {self.timestamp}"
