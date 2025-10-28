from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    bio = models.CharField(max_length=300, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    isauthor = models.BooleanField(default=False)

    # 🆕 Additional Profile Fields
    gender_choices = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=20, choices=gender_choices, blank=True, null=True)

    country = models.CharField(max_length=100, null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        default='profile_pics/pfp.png',
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    

class EmailOTP(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="otps",
        null=True, blank=True  
    )
    temp_email = models.EmailField(null=True, blank=True)  
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20)  
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, editable=False)  

    def is_expired(self):
        # expire after 10 minutes
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)

    def __str__(self):
        target = self.user.email if self.user else self.temp_email
        return f"{target} - {self.purpose} ({self.code})"
