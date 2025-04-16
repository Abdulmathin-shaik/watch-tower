from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from sensor.models import (
    SensorType, Location, Organization, 
    Sensor, SensorData, Alert, MaintenanceLog
)
import random
from datetime import timedelta
import math

class Command(BaseCommand):
    help = 'Creates sample data for testing the application'

    def generate_temperature_data(self, timestamp, base_temp=22.0):
        """Simulate indoor temperature with daily variation"""
        hour = timestamp.hour
        # Daily temperature curve (peak at 14:00)
        daily_variation = 2 * math.sin(math.pi * (hour - 6) / 12)
        # Add some random noise
        noise = random.uniform(-0.5, 0.5)
        return base_temp + daily_variation + noise

    def generate_humidity_data(self, timestamp, base_humidity=50.0):
        """Simulate indoor humidity with daily variation"""
        hour = timestamp.hour
        # Inverse of temperature curve (higher at night)
        daily_variation = -10 * math.sin(math.pi * (hour - 6) / 12)
        noise = random.uniform(-3, 3)
        value = base_humidity + daily_variation + noise
        return max(min(value, 100), 0)  # Clamp between 0-100%

    def generate_pressure_data(self, timestamp, base_pressure=1013.25):
        """Simulate atmospheric pressure with weather patterns"""
        # Create a slow-changing pattern over days
        day_factor = (timestamp.timestamp() / (24 * 3600)) % 7
        weather_pattern = 5 * math.sin(2 * math.pi * day_factor / 7)
        noise = random.uniform(-0.5, 0.5)
        return base_pressure + weather_pattern + noise

    def generate_co2_data(self, timestamp, base_co2=400):
        """Simulate CO2 levels with occupancy patterns"""
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Simulate office hours (9-17 on weekdays)
        if weekday < 5 and 9 <= hour < 17:
            occupancy_factor = 200  # Higher CO2 during office hours
        else:
            occupancy_factor = 0
            
        # Add some random variation
        noise = random.uniform(-20, 20)
        return base_co2 + occupancy_factor + noise

    def generate_light_data(self, timestamp, base_light=300):
        """Simulate light levels with day/night cycle"""
        hour = timestamp.hour
        
        # Night time (very low light)
        if hour < 6 or hour > 20:
            return random.uniform(0, 10)
            
        # Day time with peak at noon
        daylight = 1000 * math.sin(math.pi * (hour - 6) / 12)
        noise = random.uniform(-50, 50)
        return max(base_light + daylight + noise, 0)

    def generate_noise_data(self, timestamp, base_noise=35):
        """Simulate noise levels with activity patterns"""
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Higher noise during work hours on weekdays
        if weekday < 5 and 9 <= hour < 17:
            activity_noise = random.uniform(15, 25)
        else:
            activity_noise = random.uniform(0, 10)
            
        noise = random.uniform(-5, 5)
        return base_noise + activity_noise + noise

    def generate_pm25_data(self, timestamp, base_pm25=10):
        """Simulate PM2.5 levels with daily patterns"""
        hour = timestamp.hour
        
        # Higher pollution during rush hours
        if hour in [8, 9, 17, 18]:
            traffic_factor = random.uniform(5, 15)
        else:
            traffic_factor = random.uniform(0, 5)
            
        noise = random.uniform(-2, 2)
        return max(base_pm25 + traffic_factor + noise, 0)

    def generate_voc_data(self, timestamp, base_voc=100):
        """Simulate VOC levels with activity patterns"""
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Higher VOCs during work hours
        if weekday < 5 and 9 <= hour < 17:
            activity_factor = random.uniform(50, 150)
        else:
            activity_factor = random.uniform(0, 50)
            
        noise = random.uniform(-20, 20)
        return max(base_voc + activity_factor + noise, 0)

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        MaintenanceLog.objects.all().delete()
        Alert.objects.all().delete()
        SensorData.objects.all().delete()
        Sensor.objects.all().delete()
        Location.objects.all().delete()
        SensorType.objects.all().delete()
        Organization.objects.all().delete()
        
        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write('Created superuser: admin/admin')

        # Create sensor types with realistic units and ranges
        sensor_configs = [
            {
                'name': 'Temperature',
                'unit': '°C',
                'description': 'Measures ambient temperature',
                'min_val': 15,
                'max_val': 30,
                'data_generator': self.generate_temperature_data
            },
            {
                'name': 'Humidity',
                'unit': '%',
                'description': 'Measures relative humidity',
                'min_val': 30,
                'max_val': 70,
                'data_generator': self.generate_humidity_data
            },
            {
                'name': 'Pressure',
                'unit': 'hPa',
                'description': 'Measures atmospheric pressure',
                'min_val': 980,
                'max_val': 1020,
                'data_generator': self.generate_pressure_data
            },
            {
                'name': 'CO2',
                'unit': 'ppm',
                'description': 'Measures carbon dioxide levels',
                'min_val': 400,
                'max_val': 1500,
                'data_generator': self.generate_co2_data
            },
            {
                'name': 'Light',
                'unit': 'lux',
                'description': 'Measures ambient light levels',
                'min_val': 0,
                'max_val': 2000,
                'data_generator': self.generate_light_data
            },
            {
                'name': 'Noise',
                'unit': 'dB',
                'description': 'Measures noise levels',
                'min_val': 35,
                'max_val': 85,
                'data_generator': self.generate_noise_data
            },
            {
                'name': 'PM2.5',
                'unit': 'µg/m³',
                'description': 'Measures fine particulate matter',
                'min_val': 0,
                'max_val': 50,
                'data_generator': self.generate_pm25_data
            },
            {
                'name': 'VOC',
                'unit': 'ppb',
                'description': 'Measures volatile organic compounds',
                'min_val': 100,
                'max_val': 500,
                'data_generator': self.generate_voc_data
            }
        ]
        
        created_types = []
        for config in sensor_configs:
            sensor_type, _ = SensorType.objects.get_or_create(
                name=config['name'],
                defaults={
                    'unit': config['unit'],
                    'description': config['description']
                }
            )
            created_types.append((sensor_type, config))
        
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
        
        # Create sensors with appropriate distribution
        created_sensors = []
        for i, ((sensor_type, config), location) in enumerate(zip(created_types, created_locations * 2)):
            unique_name = f"{config['name']} Sensor {location.name} {i+1}"
            sensor = Sensor.objects.create(
                name=unique_name,
                description=f"{config['name']} sensor in {location.name}",
                sensor_type=sensor_type,
                location=location,
                organization=org,
                status=random.choice(['active'] * 3 + ['maintenance', 'error']),
                min_threshold=config['min_val'],
                max_threshold=config['max_val'],
                reading_interval=random.choice([60, 300, 600])
            )
            created_sensors.append((sensor, config))
        
        # Generate sensor data
        end_time = timezone.now()
        start_time = end_time - timedelta(days=7)
        
        for sensor, config in created_sensors:
            # Delete existing data
            SensorData.objects.filter(sensor=sensor).delete()
            
            current_time = start_time
            data_generator = config['data_generator']
            
            while current_time <= end_time:
                # Generate value using the specific generator for this sensor type
                value = data_generator(current_time)
                
                # Determine data quality and possible anomalies
                if random.random() < 0.05:  # 5% chance of anomaly
                    value = value * random.uniform(1.5, 2.0)  # Significant deviation
                    quality = random.randint(30, 60)
                    
                    # Create alert for anomaly
                    Alert.objects.create(
                        sensor=sensor,
                        message=f'Abnormal {sensor.sensor_type.name} reading detected: {value:.2f} {sensor.sensor_type.unit}',
                        value=value,
                        severity=random.choice(['medium', 'high']),
                        timestamp=current_time
                    )
                else:
                    quality = random.randint(80, 100)
                
                SensorData.objects.create(
                    sensor=sensor,
                    timestamp=current_time,
                    value=value,
                    quality=quality
                )
                
                current_time += timedelta(seconds=sensor.reading_interval)
        
        # Create maintenance logs
        maintenance_tasks = {
            'Temperature': ['Calibration performed', 'Temperature sensor cleaned', 'Thermal paste replaced'],
            'Humidity': ['Humidity sensor calibrated', 'Moisture build-up cleaned', 'Filter replaced'],
            'Pressure': ['Pressure sensor calibrated', 'Barometer checked', 'Housing seal replaced'],
            'CO2': ['CO2 sensor calibrated', 'Gas chamber cleaned', 'Reference gas check completed'],
            'Light': ['Light sensor cleaned', 'Calibration against reference', 'Lens replaced'],
            'Noise': ['Microphone calibrated', 'Acoustic foam replaced', 'Sound level verification'],
            'PM2.5': ['Particle counter cleaned', 'Filter replaced', 'Flow rate calibrated'],
            'VOC': ['VOC sensor calibrated', 'Gas chamber cleaned', 'Reference gas check']
        }
        
        for sensor, _ in created_sensors:
            for _ in range(random.randint(1, 3)):
                tasks = maintenance_tasks.get(sensor.sensor_type.name, ['Routine maintenance check'])
                MaintenanceLog.objects.create(
                    sensor=sensor,
                    performed_by=User.objects.get(username='admin'),
                    description=random.choice(tasks),
                    next_maintenance_date=timezone.now() + timedelta(days=random.randint(30, 90))
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))
