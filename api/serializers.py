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
    
class DetalleBoletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleBoleta
        fields = ['nombre', 'precio', 'cantidad', 'total', 'tipo_venta']


class BoletaSerializer(serializers.ModelSerializer):
    detalles = DetalleBoletaSerializer(many=True)

    class Meta:
        model = Boleta
        fields = ['id', 'fecha', 'total', 'estado', 'detalles']
        read_only_fields = ['total']

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        total = 0

        for detalle in detalles_data:
            # Convertimos valores a float para evitar errores
            precio = float(detalle['precio'])
            cantidad = float(detalle['cantidad'])
            tipo_venta = detalle.get('tipo_venta', 'unidad').lower()

            # Si ya viene el total, usamos ese; si no, lo calculamos
            if 'total' in detalle and detalle['total'] not in (None, ''):
                subtotal = float(detalle['total'])
            else:
                if tipo_venta == 'gramos':
                    subtotal = precio * cantidad / 1000
                else:
                    subtotal = precio * cantidad
                detalle['total'] = subtotal  # Guardamos en el detalle

            total += subtotal

        # Creamos la boleta con el total calculado
        boleta = Boleta.objects.create(total=total, **validated_data)

        # Creamos los detalles
        for detalle in detalles_data:
            DetalleBoleta.objects.create(boleta=boleta, **detalle)

        return boleta

    
class BoletaHistoricaSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoletaHistorica
        fields = '__all__'

class pruebaImpresionSerializer(serializers.Serializer):
    mensaje = serializers.CharField(default="boleta de prueba")