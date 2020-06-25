from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Test(models.Model):
  dealer = models.CharField(max_length=100)
  start_time = models.CharField(max_length=100)
  end_time = models.CharField(max_length=100, null=True, blank=True)
  status = models.CharField(max_length=100)
  summary_file = models.CharField(max_length=100, null=True, blank=True)
  inventory_file = models.CharField(max_length=100, null=True, blank=True)
  user = models.ForeignKey(User, on_delete=models.CASCADE)

  def __str__(self):
      return self.dealer
