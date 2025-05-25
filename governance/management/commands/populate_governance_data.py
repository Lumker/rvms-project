from django.core.management.base import BaseCommand
from governance.models import Province, District, Municipality

class Command(BaseCommand):
    help = 'Populate initial governance structure data for South Africa'

    def handle(self, *args, **options):
        # South African Provinces
        provinces_data = [
            {'name': 'Eastern Cape', 'code': 'EC'},
            {'name': 'Free State', 'code': 'FS'},
            {'name': 'Gauteng', 'code': 'GP'},
            {'name': 'KwaZulu-Natal', 'code': 'KZN'},
            {'name': 'Limpopo', 'code': 'LP'},
            {'name': 'Mpumalanga', 'code': 'MP'},
            {'name': 'Northern Cape', 'code': 'NC'},
            {'name': 'North West', 'code': 'NW'},
            {'name': 'Western Cape', 'code': 'WC'},
        ]

        self.stdout.write('Creating provinces...')
        for province_data in provinces_data:
            province, created = Province.objects.get_or_create(
                code=province_data['code'],
                defaults={'name': province_data['name']}
            )
            if created:
                self.stdout.write(f'Created province: {province.name}')

        # Sample districts for Limpopo (you can expand this)
        limpopo = Province.objects.get(code='LP')
        districts_data = [
            {'name': 'Capricorn District Municipality', 'code': 'DC35', 'province': limpopo},
            {'name': 'Mopani District Municipality', 'code': 'DC33', 'province': limpopo},
            {'name': 'Sekhukhune District Municipality', 'code': 'DC47', 'province': limpopo},
            {'name': 'Vhembe District Municipality', 'code': 'DC34', 'province': limpopo},
            {'name': 'Waterberg District Municipality', 'code': 'DC36', 'province': limpopo},
        ]

        self.stdout.write('Creating districts...')
        for district_data in districts_data:
            district, created = District.objects.get_or_create(
                code=district_data['code'],
                defaults={
                    'name': district_data['name'],
                    'province': district_data['province']
                }
            )
            if created:
                self.stdout.write(f'Created district: {district.name}')

        self.stdout.write(self.style.SUCCESS('Successfully populated governance data'))