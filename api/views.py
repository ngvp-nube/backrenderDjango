from django.shortcuts import render
from ValdivianoApp.models import BoletaHistorica, CustomUser, DetalleBoleta, Producto, Boleta
from .serializers import ProductoSerializer, UsuarioCreateSerializer ,BoletaSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from django.db.models import Sum, F
from rest_framework.permissions import AllowAny
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework import status
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

        return Response(productos, status=200)