from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.IntegerField()
    codigo = models.CharField(max_length=50, unique=True)
    tipo_venta = models.CharField(max_length=10, choices=[('gramos', 'Gramos'), ('unidad', 'Unidad')],default='unidad')
    peso_kg = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)  # Peso (Kg)
    cantidad = models.IntegerField(default=0)  
    def __str__(self):
        return self.nombre
    
class BoletaHistorica(models.Model):
    fecha = models.DateTimeField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    boleta_original_id = models.IntegerField()
    productos = models.JSONField()  # Aquí almacenamos los detalles como un array de diccionarios
    archivada_en = models.DateTimeField(auto_now_add=True)

class CustomUser(AbstractUser):
    rol = models.CharField(max_length=50, choices=[('Admin', 'Admin'), ('Vendedor', 'Vendedor')])

class Boleta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, default='activa')
    def __str__(self):
        return f'Boleta #{self.id} - {self.estado}'

class DetalleBoleta(models.Model):
    boleta = models.ForeignKey(Boleta, related_name='detalles', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)  # en gramos
    total = models.DecimalField(max_digits=10, decimal_places=2)