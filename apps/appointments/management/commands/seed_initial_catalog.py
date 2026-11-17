import datetime
import re
from django.db import transaction
from accounts.management.passwords import initial_password
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from customers.models import Customer
from services.models import Service, Professional
from appointments.models import Appointment


class Command(BaseCommand):
    help = 'Puebla el catálogo de servicios, clientes, profesionales y citas iniciales'

    def add_arguments(self, parser):
        parser.add_argument('--no-input', '--noinput', action='store_false', dest='interactive', default=True)

    @transaction.atomic
    def handle(self, *args, **kwargs):
        profs_data = [
            {
                'username': 'julian',
                'email': 'julian@studiogest.co',
                'first_name': 'Julian',
                'last_name': 'Restrepo',
                'specialty': 'Barbero Senior',
                'color_tag': '#0D9488'
            },
            {
                'username': 'camila',
                'email': 'camila@studiogest.co',
                'first_name': 'Camila',
                'last_name': 'Torres',
                'specialty': 'Estilista & Colorista',
                'color_tag': '#D5A66D'
            },
            {
                'username': 'andres',
                'email': 'andres@studiogest.co',
                'first_name': 'Andres',
                'last_name': 'Valencia',
                'specialty': 'Barbero & Colorimetrista',
                'color_tag': '#2563EB'
            },
        ]

        users = {}
        for data in profs_data:
            user = User.objects.filter(username=data['username']).first()
            if user is None:
                user = User(
                    username=data['username'], email=data['email'],
                    first_name=data['first_name'], last_name=data['last_name'],
                    role=User.Role.WORKER, phone='3101234567',
                )
                key = re.sub(r'[^A-Z0-9]', '_', data['username'].upper())
                password = initial_password(
                    f'INITIAL_CATALOG_{key}_PASSWORD', user=user, interactive=kwargs['interactive'],
                )
                user.set_password(password)
            users[data['username']] = user

        self.stdout.write('[INFO] Iniciando carga de catalogo StudioGest...')

        # 1. SERVICIOS (Precios en COP según DESIGN.md)
        services_data = [
            {'name': 'Corte Degradado + Barba Spa', 'price_cop': 65000, 'duration_minutes': 45, 'description': 'Corte moderno degradado con perfilado y toalla caliente para barba.'},
            {'name': 'Corte Caballero Clasico', 'price_cop': 35000, 'duration_minutes': 30, 'description': 'Corte tradicional a tijera o maquina con lavado incluido.'},
            {'name': 'Perfilado y Diseno de Barba', 'price_cop': 30000, 'duration_minutes': 30, 'description': 'Ritual de afeitado con navaja clasica y balsamo nutritivo.'},
            {'name': 'Balayage & Spa Capilar', 'price_cop': 180000, 'duration_minutes': 120, 'description': 'Diseno de color personalizado y mascarilla hidratante profunda.'},
            {'name': 'Ritual Facial Masculino', 'price_cop': 50000, 'duration_minutes': 45, 'description': 'Exfoliacion, mascarilla de carbon activado y masaje revitalizante.'},
            {'name': 'Corte VIP', 'price_cop': 75000, 'duration_minutes': 60, 'description': 'Servicio exclusivo de corte, barba, exfoliacion y bebida de cortesia.'},
        ]
        created_services = []
        for s_data in services_data:
            s, _ = Service.objects.get_or_create(
                name=s_data['name'],
                defaults=s_data
            )
            created_services.append(s)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(created_services)} servicios cargados.'))

        # 2. USUARIOS Y PROFESIONALES
        created_professionals = []
        for p_data in profs_data:
            u = users[p_data['username']]
            if u.pk is None:
                u.save()

            prof, _ = Professional.objects.get_or_create(
                user=u,
                defaults={
                    'specialty': p_data['specialty'],
                    'color_tag': p_data['color_tag'],
                    'is_active': True
                }
            )
            created_professionals.append(prof)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(created_professionals)} profesionales listos.'))

        # 3. CLIENTES
        customers_data = [
            {'name': 'Carlos Mendoza', 'phone': '3104567890', 'email': 'carlos@cliente.co', 'is_vip': True, 'notes': 'Cliente frecuente de los viernes. Prefiere café negro.'},
            {'name': 'Cristian Londono', 'phone': '3152345678', 'email': 'cristian@cliente.co', 'is_vip': True, 'notes': 'Alergico al alcohol perfumado, usar balsamo neutro.'},
            {'name': 'Mateo Gomez', 'phone': '3001234567', 'email': 'mateo@cliente.co', 'is_vip': False, 'notes': 'Corte degradado bajo.'},
            {'name': 'Daniel Quintero', 'phone': '3119876543', 'email': 'daniel@cliente.co', 'is_vip': False, 'notes': 'Diseno de barba angular.'},
            {'name': 'Sebastian Morales', 'phone': '3187654321', 'email': 'sebastian@cliente.co', 'is_vip': False, 'notes': ''},
        ]
        created_customers = []
        for c_data in customers_data:
            c, _ = Customer.objects.get_or_create(
                phone=c_data['phone'],
                defaults=c_data
            )
            created_customers.append(c)
        self.stdout.write(self.style.SUCCESS(f'[OK] {len(created_customers)} clientes registrados.'))

        # 4. CITAS DE PRUEBA (Hoy y la semana actual)
        today = datetime.date.today()
        # Keep historical appointments; repeated runs do not replace them.

        admin_user = User.objects.filter(is_superuser=True).first()

        sample_appointments = [
            # Hoy
            {
                'customer': created_customers[0],
                'service': created_services[0],  # Corte Degradado + Barba Spa
                'professional': created_professionals[0],  # Julián
                'date': today,
                'start_time': datetime.time(9, 0),
                'end_time': datetime.time(9, 45),
                'price_cop': 65000,
                'status': Appointment.Status.COMPLETED,
                'notes': 'Servicio realizado a satisfacción.'
            },
            {
                'customer': created_customers[1],
                'service': created_services[5],  # Corte VIP
                'professional': created_professionals[0],  # Julián
                'date': today,
                'start_time': datetime.time(11, 0),
                'end_time': datetime.time(12, 0),
                'price_cop': 75000,
                'status': Appointment.Status.CONFIRMED,
                'notes': 'Cliente alérgico al alcohol perfumado.'
            },
            {
                'customer': created_customers[2],
                'service': created_services[3],  # Balayage & Spa
                'professional': created_professionals[1],  # Camila
                'date': today,
                'start_time': datetime.time(14, 0),
                'end_time': datetime.time(16, 0),
                'price_cop': 180000,
                'status': Appointment.Status.CONFIRMED,
                'notes': 'Tono cenizo solicitado.'
            },
            {
                'customer': created_customers[3],
                'service': created_services[2],  # Perfilado barba
                'professional': created_professionals[2],  # Andrés
                'date': today,
                'start_time': datetime.time(16, 30),
                'end_time': datetime.time(17, 0),
                'price_cop': 30000,
                'status': Appointment.Status.CONFIRMED,
                'notes': ''
            },
            # Mañana
            {
                'customer': created_customers[4],
                'service': created_services[1],  # Corte clásico
                'professional': created_professionals[0],  # Julián
                'date': today + datetime.timedelta(days=1),
                'start_time': datetime.time(10, 0),
                'end_time': datetime.time(10, 30),
                'price_cop': 35000,
                'status': Appointment.Status.CONFIRMED,
                'notes': ''
            },
            # Pasado mañana
            {
                'customer': created_customers[0],
                'service': created_services[4],  # Facial
                'professional': created_professionals[1],  # Camila
                'date': today + datetime.timedelta(days=2),
                'start_time': datetime.time(15, 0),
                'end_time': datetime.time(15, 45),
                'price_cop': 50000,
                'status': Appointment.Status.CONFIRMED,
                'notes': 'Cliente VIP'
            },
        ]

        for app_data in sample_appointments:
            Appointment.objects.get_or_create(
                professional=app_data['professional'], date=app_data['date'],
                start_time=app_data['start_time'],
                defaults={
                    'created_by': admin_user,
                    **{key: value for key, value in app_data.items()
                       if key not in {'professional', 'date', 'start_time'}},
                },
            )

        self.stdout.write(self.style.SUCCESS(f'[OK] {len(sample_appointments)} citas iniciales creadas en agenda.'))
        self.stdout.write(self.style.SUCCESS('[OK] Catalogo de StudioGest cargado con exito.'))
