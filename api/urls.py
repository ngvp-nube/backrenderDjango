from django.urls import  re_path,path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import CustomAuthToken, UsuarioCreateView
from api import views


urlpatterns=[
    re_path(r'^api/producto/$',views.ProductoViewSet.as_view()),
    path('api/login/', CustomAuthToken.as_view()),
    path('api/usuarios/', UsuarioCreateView.as_view(), name='crear-usuario')

]
