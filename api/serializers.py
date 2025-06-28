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
