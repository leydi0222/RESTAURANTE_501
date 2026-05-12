#crear rutas
from django.urls import path
from . import views

urlpatterns = [
    # RUTAS DE AUTENTICACIÓN
    path('login/', views.login_view, name='login'),              # LOGIN
    path('registro/', views.registro_view, name='registro'),     # REGISTRO
    path('logout/', views.logout_view, name='logout'),           # LOGOUT
    
    # RUTA DE INICIO
    path('', views.inicio, name='inicio'),
    
    # RUTAS CRUD CLIENTES
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/eliminar/', views.eliminar_cliente, name='eliminar_cliente'),
    
    # RUTAS CRUD EMPLEADOS
    path('empleados/', views.lista_empleados, name='lista_empleados'),
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/<int:pk>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleados/<int:pk>/eliminar/', views.eliminar_empleado, name='eliminar_empleado'),
    
    # RUTAS CRUD MESAS
    path('mesas/', views.lista_mesas, name='lista_mesas'),
    path('mesas/crear/', views.crear_mesa, name='crear_mesa'),
    path('mesas/<int:pk>/editar/', views.editar_mesa, name='editar_mesa'),
    path('mesas/<int:pk>/eliminar/', views.eliminar_mesa, name='eliminar_mesa'),
    
    # RUTAS CRUD PLATOS
    path('platos/', views.lista_platos, name='lista_platos'),
    path('platos/crear/', views.crear_plato, name='crear_plato'),
    path('platos/<int:pk>/editar/', views.editar_plato, name='editar_plato'),
    path('platos/<int:pk>/eliminar/', views.eliminar_plato, name='eliminar_plato'),
    
    # RUTAS DE ÓRDENES
    path('ordenes/', views.lista_ordenes, name='lista_ordenes'),
    path('ordenes/crear/', views.crear_orden, name='crear_orden'),
    path('ordenes/<int:pk>/editar/', views.editar_orden, name='editar_orden'),
    path('ordenes/<int:pk>/eliminar/', views.eliminar_orden, name='eliminar_orden'),

    # RUTAS DE FACTURAS
    path('facturas/', views.lista_facturas, name='lista_facturas'),
    path('facturas/crear/', views.crear_factura, name='crear_factura'),
    path('facturas/<int:pk>/editar/', views.editar_factura, name='editar_factura'),
    path('facturas/<int:pk>/eliminar/', views.eliminar_factura, name='eliminar_factura'),
]

