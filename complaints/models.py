from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=24, blank=True)
    dark_mode = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile for {self.user.username}"


class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('Water Leakage', 'Water Leakage'),
        ('Electricity', 'Electricity'),
        ('Garbage', 'Garbage'),
        ('Classroom Issue', 'Classroom Issue'),
        ('Hostel Problem', 'Hostel Problem'),
        ('Internet Issue', 'Internet Issue'),
        ('Security Issue', 'Security Issue'),
        ('Maintenance', 'Maintenance'),
        ('Transport', 'Transport'),
        ('Other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Emergency', 'Emergency'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to='complaints/', blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Low')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_anonymous = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_complaints',
        limit_choices_to={'is_staff': True}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"

    def get_absolute_url(self):
        return reverse('complaint_detail', kwargs={'pk': self.pk})

    @property
    def display_user(self):
        return 'Anonymous' if self.is_anonymous else self.user.username


class Comment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_staff': True}
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        author = self.admin.username if self.admin else 'System'
        return f"Update for {self.complaint.title} by {author}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
