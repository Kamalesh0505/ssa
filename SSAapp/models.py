
# Create your models here.
from django.db import models


class Customer(models.Model):

    mobile = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    alt_number = models.CharField(max_length=20)
    dob = models.CharField(max_length=20)
    local_address = models.TextField()
    permanent_address = models.TextField()
    aadhar_pan = models.CharField(max_length=50)
    email = models.EmailField()

    def __str__(self):
        return self.customer_name