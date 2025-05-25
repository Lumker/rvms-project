from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserNotification
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample notifications for testing'

    def handle(self, *args, **options):
        # Get the first user or create a test user
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write('No users found. Please create a user first.')
                return
        except Exception as e:
            self.stdout.write(f'Error: {e}')
            return

        # Sample notifications
        notifications = [
            {
                'notification_type': 'document_approved',
                'title': 'Document Approved',
                'message': 'Your proof of residence document PR-202405-ABC123 has been approved and is ready for generation.',
                'priority': 'normal'
            },
            {
                'notification_type': 'meeting_scheduled',
                'title': 'Meeting Scheduled',
                'message': 'A village council meeting has been scheduled for tomorrow at 2:00 PM.',
                'priority': 'high'
            },
            {
                'notification_type': 'system_update',
                'title': 'System Maintenance',
                'message': 'The system will undergo maintenance this weekend from 2:00 AM to 6:00 AM.',
                'priority': 'low'
            },
            {
                'notification_type': 'user_message',
                'title': 'New Message',
                'message': 'You have received a new message from the system administrator.',
                'priority': 'normal'
            },
            {
                'notification_type': 'document_generated',
                'title': 'Document Ready',
                'message': 'Your requested document has been generated and is ready for download.',
                'priority': 'urgent'
            }
        ]

        created_count = 0
        for notif_data in notifications:
            notification = UserNotification.objects.create(
                user=user,
                **notif_data
            )
            created_count += 1
            self.stdout.write(f'Created notification: {notification.title}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample notifications for {user.username}')
        )