from django.db import models

# Create your models here.

class Member(models.Model):
    serial_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)

    # Only required IF role = worker (we’ll validate this later)
    department = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    status_complete = models.BooleanField(default=False)

    gender = models.CharField(max_length=10, blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    parent_name = models.CharField(max_length=100, blank=True, null=True)
    parent_phone_number = models.CharField(max_length=20, blank=True, null=True)


    def __str__(self):
        return f"{self.serial_number} — {self.name}"

class NewMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.phone_number}"

class Attendance(models.Model):
    SERVICE_CHOICES = [
        ("first", "First Service"),
        ("second", "Second Service"),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    date = models.DateField()
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    time_marked = models.DateTimeField(auto_now_add=True)
    marked_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ("member", "date", "service_type")  # prevents double marking

    def __str__(self):
        return f"{self.member.name} - {self.date} ({self.service_type})"
