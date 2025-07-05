from ValdivianoApp.models import *
from rest_framework import serializers

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

def create(self, validated_data):
    user = CustomUser.objects.create_user(**validated_data)
    password = validated_data.pop('password')
    rol = validated_data.pop('rol', None)

    user = CustomUser(**validated_data)
    user.set_password(password)

    if rol:
        user.rol = rol

    user.save()
    return user   

class UsuarioCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'email', 'rol']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user
    
#boleta y detalle
class DetalleBoletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleBoleta
        fields = ['nombre', 'precio', 'cantidad', 'total']

class BoletaSerializer(serializers.ModelSerializer):
    detalles = DetalleBoletaSerializer(many=True)

    class Meta:
        model = Boleta
        fields = ['id', 'fecha', 'total','estado', 'detalles']

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        boleta = Boleta.objects.create(**validated_data)
        for detalle in detalles_data:
            DetalleBoleta.objects.create(boleta=boleta, **detalle)
        return boleta
    
class BoletaHistoricaSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoletaHistorica
        fields = '__all__'