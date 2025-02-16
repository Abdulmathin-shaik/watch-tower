from django.contrib import admin
from .models import Sensor, SensorData

# Register your models here.
admin.site.register(Sensor)
admin.site.register(SensorData)
