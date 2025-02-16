from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from sensor.models import (
    SensorType, Location, Organization, 
    Sensor, SensorData, Alert, MaintenanceLog
)
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates sample data for testing the application'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write('Created superuser: admin/admin')

        # Create sensor types
        sensor_types = [
            ('Temperature', '°C', 'Measures ambient temperature'),
            ('Humidity', '%', 'Measures relative humidity'),
            ('Pressure', 'hPa', 'Measures atmospheric pressure'),
            ('CO2', 'ppm', 'Measures carbon dioxide levels'),
            ('Light', 'lux', 'Measures ambient light levels'),
            ('Noise', 'dB', 'Measures noise levels'),
            ('PM2.5', 'µg/m³', 'Measures fine particulate matter'),
            ('VOC', 'ppb', 'Measures volatile organic compounds')
        ]
        
        created_types = []
        for name, unit, desc in sensor_types:
            sensor_type, _ = SensorType.objects.get_or_create(
                name=name,
                defaults={'unit': unit, 'description': desc}
            )
            created_types.append(sensor_type)
        
        # Create locations
        locations = [
            ('Server Room A', 'Main server room', 37.7749, -122.4194),
            ('Server Room B', 'Backup server room', 37.7749, -122.4195),
            ('Office Area', 'Open office space', 37.7750, -122.4194),
            ('Meeting Room 1', 'Main conference room', 37.7751, -122.4194),
            ('Data Center', 'Primary data center', 37.7752, -122.4194)
        ]
        
        created_locations = []
        for name, desc, lat, lon in locations:
            location, _ = Location.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'latitude': lat,
                    'longitude': lon
                }
            )
            created_locations.append(location)
        
        # Create organization
        org, _ = Organization.objects.get_or_create(
            name='TechCorp',
            defaults={'description': 'Technology Corporation'}
        )
        org.users.add(User.objects.get(username='admin'))
        
        # Create sensors
        sensors_config = [
            ('Temp Sensor 1', created_types[0], created_locations[0], (15, 30)),
            ('Humid Sensor 1', created_types[1], created_locations[0], (30, 70)),
            ('Pressure Sensor 1', created_types[2], created_locations[0], (980, 1020)),
            ('CO2 Sensor 1', created_types[3], created_locations[2], (400, 1500)),
            ('Light Sensor 1', created_types[4], created_locations[2], (200, 1000)),
            ('Noise Sensor 1', created_types[5], created_locations[2], (40, 80)),
            ('PM2.5 Sensor 1', created_types[6], created_locations[3], (0, 50)),
            ('VOC Sensor 1', created_types[7], created_locations[3], (100, 500))
        ]
        
        created_sensors = []
        for name, type_, location, (min_val, max_val) in sensors_config:
            sensor, _ = Sensor.objects.get_or_create(
                name=name,
                defaults={
                    'description': f'{type_.name} sensor in {location.name}',
                    'sensor_type': type_,
                    'location': location,
                    'organization': org,
                    'status': random.choice(['active', 'active', 'active', 'maintenance', 'error']),
                    'min_threshold': min_val,
                    'max_threshold': max_val,
                    'reading_interval': random.choice([60, 300, 600])
                }
            )
            created_sensors.append(sensor)
        
        # Generate sensor data
        end_time = timezone.now()
        start_time = end_time - timedelta(days=7)
        
        for sensor in created_sensors:
            # Delete existing data
            SensorData.objects.filter(sensor=sensor).delete()
            
            current_time = start_time
            min_val, max_val = sensor.min_threshold, sensor.max_threshold
            
            while current_time <= end_time:
                # Generate some anomalies
                if random.random() < 0.05:  # 5% chance of anomaly
                    value = random.uniform(max_val, max_val * 1.2)
                    quality = random.randint(30, 60)
                    
                    # Create alert for anomaly
                    Alert.objects.create(
                        sensor=sensor,
                        message=f'Abnormal reading detected: {value:.2f} {sensor.sensor_type.unit}',
                        value=value,
                        severity=random.choice(['medium', 'high']),
                        timestamp=current_time
                    )
                else:
                    value = random.uniform(min_val, max_val)
                    quality = random.randint(80, 100)
                
                SensorData.objects.create(
                    sensor=sensor,
                    timestamp=current_time,
                    value=value,
                    quality=quality
                )
                
                current_time += timedelta(seconds=sensor.reading_interval)
        
        # Create some maintenance logs
        for sensor in created_sensors:
            for _ in range(random.randint(1, 3)):
                MaintenanceLog.objects.create(
                    sensor=sensor,
                    performed_by=User.objects.get(username='admin'),
                    description=random.choice([
                        'Routine maintenance check',
                        'Calibration performed',
                        'Firmware updated',
                        'Sensor cleaned',
                        'Battery replaced'
                    ]),
                    next_maintenance_date=timezone.now() + timedelta(days=random.randint(30, 90))
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))
