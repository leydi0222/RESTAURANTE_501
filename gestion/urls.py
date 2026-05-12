#crear rutas
from django.urls import path
from . import views

urlpatterns = [
    # RUTAS DE AUTENTICACIÓN
    path('login/', views.login_view, name='login'),              # LOGIN
    path('registro/', views.registro_view, name='registro'),     # REGISTRO
    path('logout/', views.logout_view, name='logout'),           # LOGOUT
    
    # RUTAS DE LA APLICACIÓN (requieren login)
    path('', views.inicio, name='inicio'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('mesas/', views.lista_mesas, name='lista_mesas'),
    path('platos/', views.lista_platos, name='lista_platos'),
    path('ordenes/', views.lista_ordenes, name='lista_ordenes'),
    path('facturas/', views.lista_facturas, name='lista_facturas'),
]
