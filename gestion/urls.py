#crear rutas
from django.urls import path
from. import views #importar todas las listas

urlpatterns=[
    path('',views.inicio,name='inicio'),
    path('clientes/',views.lista_clientes, name='lista_clientes'),
    path('empleados/',views.lista_empleados, name='lista_empleados'),
    path('mesas/',views.lista_mesas, name='lista_mesas'),
    path('platos/',views.lista_platos, name='lista_platos'),
    path('ordenes/',views.lista_ordenes, name='lista_ordenes'),
    path('facturas/',views.lista_facturas, name='lista_facturas'),
]