from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    codigo = models.CharField(max_length=50, default='SIN-CODIGO')
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)  # Peso (Kg)
    cantidad = models.IntegerField(default=0)  
    def __str__(self):
        return self.nombre

class CustomUser(AbstractUser):
    rol = models.CharField(max_length=50, choices=[('Admin', 'Admin'), ('Vendedor', 'Vendedor')])