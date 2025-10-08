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
from django.utils.timezone import localdate
from rest_framework.generics import RetrieveAPIView
from django.db import transaction
from .utils.firma_digital import firmar_con_llave_privada
# Create your views here.
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import os
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from escpos.printer import *

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
    serializer_class = BoletaSerializer

    def get_queryset(self):
        # 🔹 Obtener la fecha actual (según zona horaria del servidor)
        hoy = localdate()

        # 🔹 Si quieres permitir un filtro opcional también
        fecha_str = self.request.query_params.get('fecha')
        if fecha_str:
            fecha = parse_date(fecha_str)
            if fecha:
                return Boleta.objects.filter(fecha__date=fecha).order_by('-id')

        # 🔹 Por defecto, devuelve solo las boletas del día actual
        return Boleta.objects.filter(fecha__date=hoy).order_by('-id')


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
        try:
            data_to_sign = request.data.get('data')
            if not data_to_sign:
                return Response({"error": "No data to sign"}, status=status.HTTP_400_BAD_REQUEST)

            # Leer la clave privada desde variable de entorno
            private_key_pem = os.getenv('PRIVATE_KEY')
            if not private_key_pem:
                return Response({"error": "Private key not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Convertir string a bytes (asegúrate que los saltos de línea están bien)
            private_key_bytes = private_key_pem.encode('utf-8')

            # Cargar clave privada
            private_key = load_pem_private_key(private_key_bytes, password=None)

            # Firmar
            signature = private_key.sign(
                data_to_sign.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            signature_b64 = base64.b64encode(signature).decode('utf-8')

            return Response({"signature": signature_b64})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ImprimirBoletaAPIView(APIView):
    def post(self, request, format=None):
        try:
            # ✅ Configura IP de la impresora
            ip_impresora = "192.168.1.102"
            printer = Network(ip_impresora)

            # ✅ Datos desde frontend
            venta = request.data.get("venta", {})
            productos = request.data.get("productos", [])
            total = request.data.get("total", 0)

            nro_venta = venta.get("numero", "")
            direccion = venta.get("direccion", "")
            fecha_str = venta.get("fecha")

            # ✅ CABECERA: título en grande
            printer.set(align='center', bold=True)
            printer._raw(b'\x1D\x21\x11')  # doble ancho y alto
            printer.text("El Valdiviano\n")
            printer._raw(b'\x1D\x21\x00')  # reset tamaño

            # ✅ DATOS DE VENTA
            printer.set(align='left', bold=False)
            printer.text(f"NRO Venta: {nro_venta}\n")
            printer.text(f"{direccion}\n")

            if fecha_str:
                fecha = datetime.fromisoformat(fecha_str)
                printer.text("Fecha: " + fecha.strftime("%d-%m-%Y, %H:%M:%S") + "\n")

            printer.text("─" * 44 + "\n")

            # ✅ ENCABEZADO DE PRODUCTOS
            printer.set(bold=True)
            printer.text(
                f"{'Producto'.ljust(14)}"
                f"{'Precio'.rjust(10)}"
                f"{'Cant'.rjust(8)}"
                f"{'Total'.rjust(10)}\n"
            )
            printer.set(bold=False)
            printer.text("─" * 44 + "\n")

            # ✅ DETALLE DE PRODUCTOS
            for p in productos:
                nombre = p.get("nombre", "")
                precio = p.get("precio", 0)
                cantidad = p.get("cantidad", "")
                unidad = p.get("unidad", "")
                total_item = p.get("total", 0)

                cantidad_str = f"{cantidad} {unidad}".strip() if unidad else str(cantidad)
                precio_str = f"{precio:,}".replace(",", ".")
                total_str = f"{total_item:,}".replace(",", ".")

                line = (
                    f"{nombre.ljust(14)[:14]}"
                    f"{precio_str.rjust(10)}"
                    f"{cantidad_str.rjust(8)}"
                    f"{total_str.rjust(10)}\n"
                )
                printer.text(line)

            # ✅ TOTAL FINAL
            printer.text("─" * 44 + "\n")
            printer.set(align='center', bold=True)
            printer._raw(b'\x1D\x21\x11')  # doble alto/ancho
            total_str = f"{total:,}".replace(",", ".")
            printer.text(f"\nTOTAL $ {total_str}\n")
            printer._raw(b'\x1D\x21\x00')  # reset

            # ✅ MENSAJE FINAL
            printer.set(align='center')
            printer.text("\n¡Gracias por su compra!\n")

            # ✅ CORTAR PAPEL
            printer.cut()

            return Response(
                {"status": "ok", "mensaje": "Boleta impresa correctamente ✅"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": "error", "mensaje": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UltimaBoletaAPIView(APIView):
    def get(self, request):
        try:
            ultima_boleta = Boleta.objects.latest('id')
            return Response({'ultimo_id': ultima_boleta.id}, status=status.HTTP_200_OK)
        except Boleta.DoesNotExist:
            return Response({'error': 'No hay boletas registradas'}, status=status.HTTP_404_NOT_FOUND)
        
class CrearBoletaAPIView(APIView):
    def post(self, request):
        try:
            data = request.data
            fecha_str = data.get("fecha")
            total = data.get("total")
            productos = data.get("productos", [])

            if not productos:
                return Response({"error": "Debe enviar productos"}, status=400)

            # ✅ Convertir fecha si viene del frontend
            fecha = datetime.fromisoformat(fecha_str) if fecha_str else None

            # ✅ Crear la boleta
            boleta = Boleta.objects.create(
                fecha=fecha,
                total=total
            )

            # ✅ Crear detalles de boleta
            for p in productos:
                DetalleBoleta.objects.create(
                    boleta=boleta,
                    nombre=p.get("nombre"),
                    precio=p.get("precio"),
                    cantidad=p.get("cantidad"),
                    total=p.get("total"),
                    tipo_venta=p.get("tipo_venta", "unidad")  # por defecto "unidad"
                )

            return Response({"mensaje": "Boleta creada correctamente", "boleta_id": boleta.id}, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=500)