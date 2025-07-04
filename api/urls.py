from django.urls import  re_path,path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import *
from api import views


urlpatterns=[
    re_path(r'^api/producto/$',views.ProductoViewSet.as_view()),
    path('api/login/', CustomAuthToken.as_view()),
    path('api/usuarios/', UsuarioCreateView.as_view(), name='crear-usuario'),   
    path('api/producto/<str:codigo>/', ProductoPorCodigoView.as_view(), name='producto-por-codigo'),
    path('api/boleta/', BoletaListCreateView.as_view(), name='boleta-list-create'),
    path('contabilidad/total/', TotalContabilidadView.as_view()),
    path('api/boleta/<int:boleta_id>/anular/', AnularBoletaView.as_view(), name='anular-boleta') 
]
