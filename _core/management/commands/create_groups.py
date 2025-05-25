from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Create default user groups with permissions'

    def handle(self, *args, **options):
        # Create groups
        groups_data = [
            {
                'name': 'System Admin',
                'permissions': ['add_user', 'change_user', 'delete_user', 'view_user']
            },
            {
                'name': 'Governance Admin',
                'permissions': ['add_traditionalcouncil', 'change_traditionalcouncil', 'view_traditionalcouncil']
            },
            {
                'name': 'Village Admin',
                'permissions': ['add_village', 'change_village', 'view_village']
            },
            {
                'name': 'Council Member',
                'permissions': ['view_traditionalcouncil', 'add_councilmeeting', 'change_councilmeeting']
            },
            {
                'name': 'Villager',
                'permissions': ['view_village']
            },
        ]

        for group_data in groups_data:
            group, created = Group.objects.get_or_create(name=group_data['name'])
            if created:
                self.stdout.write(f'Created group: {group.name}')
                
                # Add permissions (this would need to be expanded based on your actual models)
                for perm_codename in group_data.get('permissions', []):
                    try:
                        permission = Permission.objects.get(codename=perm_codename)
                        group.permissions.add(permission)
                    except Permission.DoesNotExist:
                        self.stdout.write(f'Permission {perm_codename} not found')
            else:
                self.stdout.write(f'Group already exists: {group.name}')

        self.stdout.write(self.style.SUCCESS('Successfully created default groups'))