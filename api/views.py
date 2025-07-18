from django.shortcuts import render
from ValdivianoApp.models import BoletaHistorica, CustomUser, DetalleBoleta, Producto, Boleta
from .serializers import ProductoSerializer, UsuarioCreateSerializer ,BoletaSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from django.db.models import Sum, F
from rest_framework.permissions import AllowAny
from datetime import datetime, timedelta
import base64
from django.utils.timezone import make_aware
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from cryptography.hazmat.primitives import hashes
from django.contrib.auth import authenticate
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from rest_framework.views import APIView
from rest_framework import status
from cryptography.hazmat.primitives.asymmetric import padding
from rest_framework.generics import RetrieveAPIView
# Create your views here.

class ProductoViewSet(generics.ListCreateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        print("Usuario autenticado:", self.request.user)
        serializer.save()


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'non_field_errors': ['Unable to log in with provided credentials.']}, status=400)

        token, created = Token.objects.get_or_create(user=user)
        rol = getattr(user, 'rol', None)
        if not rol and user.groups.exists():
            rol = user.groups.first().name

        return Response({
            'token': token.key,
            'user': {
                'username': user.username,
                'email': user.email,
                'rol': rol,
            }
        })


class UsuarioCreateView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UsuarioCreateSerializer


class ProductoPorCodigoView(APIView):
    def get(self, request, codigo):
        try:
            producto = Producto.objects.get(codigo=codigo)
            serializer = ProductoSerializer(producto)
            return Response(serializer.data)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
class BoletaListCreateView(generics.ListCreateAPIView):
    queryset = Boleta.objects.all()
    serializer_class = BoletaSerializer


class TotalContabilidadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        fecha = request.query_params.get('fecha')

        if fecha:
            try:
                inicio = make_aware(datetime.strptime(fecha, "%Y-%m-%d"))
                fin = inicio + timedelta(days=1)
                boletas = Boleta.objects.filter(fecha__gte=inicio, fecha__lt=fin)
            except Exception as e:
                return Response({'error': 'Fecha inválida', 'detalle': str(e)}, status=400)
        else:
            boletas = Boleta.objects.all()

        total = sum(boleta.total for boleta in boletas)
        return Response({'total_general': total})
    

class AnularBoletaView(APIView):
    def post(self, request, boleta_id):
        try:
            boleta = Boleta.objects.get(pk=boleta_id)
            boleta.estado = 'anulada'
            boleta.save()
            return Response({'mensaje': 'Boleta anulada correctamente'}, status=status.HTTP_200_OK)
        except Boleta.DoesNotExist:
            return Response({'error': 'Boleta no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
class EliminarBoletaAPIView(APIView):
    def post(self, request):
        boleta_id = request.data.get('boleta_id')

        if not boleta_id:
            return Response({'error': 'Debe proporcionar el ID de la boleta.'}, status=400)

        try:
            boleta = Boleta.objects.get(id=boleta_id)
        except Boleta.DoesNotExist:
            return Response({'error': 'Boleta no encontrada.'}, status=404)

        # Convertir detalles en JSON
        detalles = boleta.detalles.all()
        productos = [
            {
                "nombre": detalle.nombre,
                "precio": float(detalle.precio),
                "cantidad": float(detalle.cantidad),
                "total": float(detalle.total)
            }
            for detalle in detalles
        ]

        # Crear boleta histórica
        BoletaHistorica.objects.create(
            fecha=boleta.fecha,
            total=boleta.total,
            boleta_original_id=boleta.id,
            productos=productos
        )

        # Eliminar boleta y sus detalles
        boleta.delete()

        return Response({'mensaje': 'Boleta archivada correctamente.'}, status=200)
    
class ProductosPorFechaAPIView(APIView):
    def get(self, request):
        fecha_str = request.query_params.get('fecha')

        if not fecha_str:
            return Response({"error": "Debe proporcionar una fecha en formato YYYY-MM-DD."}, status=400)

        try:
            fecha = parse_date(fecha_str)
            if not fecha:
                raise ValueError
        except ValueError:
            return Response({"error": "Fecha inválida."}, status=400)

        detalles = DetalleBoleta.objects.filter(boleta__fecha__date=fecha)

        productos = detalles.values('nombre', 'precio').annotate(
            total_cantidad=Sum('cantidad'),
            total_ventas=Sum('total')
        ).order_by('nombre')

        # Calcular el total general de ventas
        total_general = detalles.aggregate(total=Sum('total'))['total'] or 0

        return Response({
            "productos": productos,
            "total_general": total_general
        }, status=200)
    
class ActualizarProductoAPIView(APIView):
    def put(self, request, codigo):
        try:
            producto = Producto.objects.get(codigo=codigo)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductoSerializer(producto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'mensaje': 'Producto actualizado correctamente', 'producto': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class EliminarProductoAPIView(APIView):
    def delete(self, request, codigo):
        try:
            producto = Producto.objects.get(codigo=codigo)
            producto.delete()
            return Response({'mensaje': 'Producto eliminado correctamente'}, status=status.HTTP_200_OK)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
class ObtenerBoletaPorIDView(RetrieveAPIView):
    queryset = Boleta.objects.all()
    serializer_class = BoletaSerializer


class FirmaDigitalAPIView(APIView):
    def post(self, request):
        data_to_sign = request.data.get('data')
        if not data_to_sign:
            return Response({"error": "No data to sign"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Carga tu clave privada PEM desde un archivo seguro en el servidor
            with open('keys/private-key.pem', 'rb') as key_file:
                private_key = load_pem_private_key(key_file.read(), password=None)

            # Firmar con SHA256 + PKCS1v15
            signature = private_key.sign(
                data_to_sign.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            # Codificar firma en base64 para enviar al cliente
            signature_b64 = base64.b64encode(signature).decode('utf-8')

            return Response(signature_b64)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)