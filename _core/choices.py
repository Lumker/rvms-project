from django.db import models

class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER = 'O', 'Other'

class MaritalStatus(models.TextChoices):
    SINGLE = 'single', 'Single'
    MARRIED = 'married', 'Married'
    DIVORCED = 'divorced', 'Divorced'
    WIDOWED = 'widowed', 'Widowed'
    SEPARATED = 'separated', 'Separated'

class EducationLevel(models.TextChoices):
    NO_EDUCATION = 'none', 'No Formal Education'
    PRIMARY = 'primary', 'Primary Education'
    SECONDARY = 'secondary', 'Secondary Education'
    MATRIC = 'matric', 'Matric/Grade 12'
    CERTIFICATE = 'certificate', 'Certificate'
    DIPLOMA = 'diploma', 'Diploma'
    DEGREE = 'degree', 'Bachelor\'s Degree'
    HONOURS = 'honours', 'Honours Degree'
    MASTERS = 'masters', 'Master\'s Degree'
    DOCTORATE = 'doctorate', 'Doctorate'

class EmploymentStatus(models.TextChoices):
    EMPLOYED = 'employed', 'Employed'
    UNEMPLOYED = 'unemployed', 'Unemployed'
    SELF_EMPLOYED = 'self_employed', 'Self Employed'
    STUDENT = 'student', 'Student'
    RETIRED = 'retired', 'Retired'
    DISABLED = 'disabled', 'Disabled'

class Priority(models.TextChoices):
    LOW = 'low', 'Low'
    MEDIUM = 'medium', 'Medium'
    HIGH = 'high', 'High'
    URGENT = 'urgent', 'Urgent'

class Status(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'

class SouthAfricanProvinces(models.TextChoices):
    EASTERN_CAPE = 'EC', 'Eastern Cape'
    FREE_STATE = 'FS', 'Free State'
    GAUTENG = 'GP', 'Gauteng'
    KWAZULU_NATAL = 'KZN', 'KwaZulu-Natal'
    LIMPOPO = 'LP', 'Limpopo'
    MPUMALANGA = 'MP', 'Mpumalanga'
    NORTHERN_CAPE = 'NC', 'Northern Cape'
    NORTH_WEST = 'NW', 'North West'
    WESTERN_CAPE = 'WC', 'Western Cape'