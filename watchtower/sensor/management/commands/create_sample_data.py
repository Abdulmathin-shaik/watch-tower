from django.core.management.base import BaseCommand
from sensor.models import Sensor, SensorData
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Creates sample sensor data'

    def handle(self, *args, **kwargs):
        # Create a temperature sensor
        sensor = Sensor.objects.create(
            name='Temperature Sensor 1',
            description='Temperature sensor in Factory Area A'
        )

        # Create 7 days of sample data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        current_date = start_date

        while current_date <= end_date:
            # Create reading every hour
            for hour in range(24):
                timestamp = current_date + timedelta(hours=hour)
                # Random temperature between 20 and 30 degrees
                value = random.uniform(20, 30)
                SensorData.objects.create(
                    sensor=sensor,
                    timestamp=timestamp,
                    value=value
                )
            current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))
