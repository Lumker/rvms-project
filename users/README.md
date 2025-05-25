# Users App

This Django app manages user profiles for the legal practice management system.

## Features

- User profiles with different roles (Attorney, Paralegal, Admin)
- Custom admin interface for managing users and their profiles
- Profile management for users
- User listing and detail views for administrators

## Models

- **UserProfile**: Extends the built-in Django User model with additional fields:
  - Role (Attorney, Paralegal, Admin)
  - Practice Number
  - Created At timestamp

## Usage

1. Add 'users' to your INSTALLED_APPS in settings.py
2. Run migrations: `python manage.py makemigrations users` followed by `python manage.py migrate`
3. Include the users URLs in your project's urls.py:

```python
urlpatterns = [
    # ... other URL patterns
    path('users/', include('users.urls', namespace='users')),
]