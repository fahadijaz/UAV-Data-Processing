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
