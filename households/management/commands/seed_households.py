from django.core.management.base import BaseCommand
from faker import Faker
import random

from governance.models import Province, District, Municipality
from households.models import Household, Resident

fake = Faker()

class Command(BaseCommand):
    help = 'Seed household and resident data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # Create a fake province
        province, _ = Province.objects.get_or_create(name="Fake Province")

        # Create a fake district with the province
        district, _ = District.objects.get_or_create(
            name="Fake District",
            defaults={"province": province}
        )

        # Ensure the district is linked properly to the province
        if district.province_id != province.id:
            district.province = province
            district.save()

        # Create a fake municipality linked to the district
        municipality, _ = Municipality.objects.get_or_create(
            name="Fake Municipality",
            defaults={"district": district}
        )

        if municipality.district_id != district.id:
            municipality.district = district
            municipality.save()

        # Create fake households and residents
        for _ in range(10):
            household = Household.objects.create(
                address=fake.address(),
                municipality=municipality,
                head_of_household=fake.name()
            )

            for _ in range(random.randint(2, 6)):
                Resident.objects.create(
                    household=household,
                    full_name=fake.name(),
                    age=random.randint(1, 90),
                    gender=random.choice(['Male', 'Female', 'Other']),
                    occupation=fake.job()
                )

        self.stdout.write(self.style.SUCCESS("✅ Successfully seeded households and residents."))
