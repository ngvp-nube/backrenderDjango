from django.shortcuts import render
from ValdivianoApp.models import CustomUser, Producto
from .serializers import ProductoSerializer, UsuarioCreateSerializer 
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.contrib.auth import authenticate
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