from django.db import models
from django.contrib.auth.models import User

class Layer(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='layers/')
    author = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Ticket(models.Model):
    full_ticket_front = models.ImageField(upload_to='tickets_front/')
    full_ticket_back = models.ImageField(upload_to='tickets_back/')
    foreground = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name='foreground_ticket', null=True, blank=True)
    background = models.ForeignKey(Layer, on_delete=models.CASCADE, related_name='background_ticket', null=True, blank=True)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="ticket")

    def __str__(self):
        return f"Ticket {self.owner.username}"  
    
class Challenge(models.Model):
    address = models.CharField(max_length=42)
    challenge = models.CharField(max_length=64)
    created_at = models.DateTimeField()
    
