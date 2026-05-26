from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import ProgrammingError, transaction
from django.forms import inlineformset_factory

# Importar modelos
from .models import Cliente, Empleado, Mesa, Orden, Factura, Plato, Usuario, RolMenuPermiso, DetalleOrden
# Importar formularios
from .forms import (
    LoginForm, RegistroForm, RolMenuPermisoForm, ClienteForm, EmpleadoForm,
    MesaForm, PlatoForm, DetalleOrdenForm, OrdenForm, FacturaForm
)

DetalleOrdenFormSet = inlineformset_factory(
    Orden,
    DetalleOrden,
    form=DetalleOrdenForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


def requiere_login(view_func):
    """
    EXPLICACIÓN: Decorador personalizado para proteger vistas.
    
    Si el usuario no está logueado, lo redirige al login.
    Si está logueado, lo deja pasar a la vista.
    """
    def wrapped_view(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapped_view


DEFAULT_ROL_PERMISOS = {
    'Administrador': {
        'ver_clientes': True,
        'ver_empleados': True,
        'ver_mesas': True,
        'ver_platos': True,
        'ver_ordenes': True,
        'ver_facturas': True,
        'ver_usuarios': True,
    },
    'Empleado': {
        'ver_clientes': False,
        'ver_empleados': False,
        'ver_mesas': True,
        'ver_platos': True,
        'ver_ordenes': True,
        'ver_facturas': False,
        'ver_usuarios': False,
    },
    'Cajero': {
        'ver_clientes': False,
        'ver_empleados': True,
        'ver_mesas': False,
        'ver_platos': False,
        'ver_ordenes': False,
        'ver_facturas': False,
        'ver_usuarios': False,
    },
}


def obtener_permisos_por_rol(rol):
    """Devuelve el diccionario de permisos que corresponde a un rol."""
    rol_permisos = DEFAULT_ROL_PERMISOS.get(rol, DEFAULT_ROL_PERMISOS['Empleado'])

    try:
        permiso, _ = RolMenuPermiso.objects.get_or_create(
            role=rol,
            defaults=rol_permisos
        )

        return {
            'clientes': permiso.ver_clientes,
            'empleados': permiso.ver_empleados,
            'mesas': permiso.ver_mesas,
            'platos': permiso.ver_platos,
            'ordenes': permiso.ver_ordenes,
            'facturas': permiso.ver_facturas,
            'usuarios': permiso.ver_usuarios,
        }
    except ProgrammingError:
        # Si la tabla no existe en la BD, usamos los permisos por defecto.
        return {
            'clientes': rol_permisos['ver_clientes'],
            'empleados': rol_permisos['ver_empleados'],
            'mesas': rol_permisos['ver_mesas'],
            'platos': rol_permisos['ver_platos'],
            'ordenes': rol_permisos['ver_ordenes'],
            'facturas': rol_permisos['ver_facturas'],
            'usuarios': rol_permisos['ver_usuarios'],
        }


def requiere_admin(view_func):
    """Decorador para proteger vistas que solo deben ver administradores."""
    def wrapped_view(request, *args, **kwargs):
        if request.session.get('usuario_rol') != 'Administrador':
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('inicio')
        return view_func(request, *args, **kwargs)
    return wrapped_view


def requiere_permiso(permiso_nombre):
    """Decorador para proteger rutas según permisos configurados por rol."""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            permisos = request.session.get('usuario_permisos', {})
            if not permisos.get(permiso_nombre, False):
                messages.error(request, 'No tienes permiso para ver esta sección.')
                return redirect('inicio')
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


# ============ VISTAS DE AUTENTICACIÓN ============

def login_view(request):
    """
    EXPLICACIÓN: Vista de login personalizada.
    
    QUÉ HACE:
    1. Si el método es GET: Muestra el formulario de login
    2. Si el método es POST: 
       - Valida el email y contraseña
       - Si son correctos, crea una sesión y redirige a 'inicio'
       - Si son incorrectos, muestra un mensaje de error
    
    SESIÓN: Después del login exitoso, Django crea una sesión que mantiene
    al usuario autenticado mientras navegue por la app.
    """
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            contrasena = form.cleaned_data['contrasena']
            
            try:
                # Buscar el usuario por email
                usuario = Usuario.objects.get(email=email)
                
                # Verificar que la contraseña sea correcta
                if usuario.check_password(contrasena):
                    # Crear sesión: Esto mantiene al usuario "logueado"
                    # IMPORTANTE: Usamos id_usuario (no id) porque ese es el nombre del campo
                    request.session['usuario_id'] = usuario.id_usuario
                    request.session['usuario_email'] = usuario.email
                    rol_usuario = usuario.rol
                    if rol_usuario == 'administrador del restaurante':
                        rol_usuario = 'Administrador'
                    request.session['usuario_rol'] = rol_usuario
                    request.session['usuario_permisos'] = obtener_permisos_por_rol(rol_usuario)
                    
                    # Mostrar mensaje de bienvenida
                    messages.success(request, f"¡Bienvenido {usuario.email}!")
                    
                    # Redirigir a la página de inicio
                    return redirect('inicio')
                else:
                    # La contraseña es incorrecta
                    messages.error(request, "Email o contraseña incorrectos.")
            
            except Usuario.DoesNotExist:
                # El email no existe en la BD
                messages.error(request, "Email o contraseña incorrectos.")
    
    else:
        form = LoginForm()
    
    context = {'form': form}
    return render(request, 'gestion/login.html', context)


@requiere_login
@requiere_admin
def registro_view(request):
    """
    EXPLICACIÓN: Vista para que un administrador cree nuevos usuarios.
    
    QUÉ HACE:
    1. Si el método es GET: Muestra el formulario de creación de usuario
    2. Si el método es POST:
       - Valida los datos del formulario
       - Si son válidos, crea el usuario usando SQL directo
       - Si hay errores, muestra los errores
    """
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "¡Usuario creado correctamente.")
                return redirect('crear_usuario')
            except Exception as e:
                messages.error(request, f"Error al registrar: {str(e)}")
    else:
        form = RegistroForm()
    
    context = {'form': form}
    return render(request, 'gestion/crear_usuario.html', context)


@requiere_login
@requiere_admin
def configurar_permisos(request):
    """Vista para que el administrador configure qué puede ver cada rol."""
    for rol in ['Administrador', 'Empleado', 'Cajero']:
        obtener_permisos_por_rol(rol)

    try:
        roles_permisos = list(RolMenuPermiso.objects.all())
    except ProgrammingError:
        # Si la tabla no existe, creamos instancias temporales con permisos por defecto.
        roles_permisos = [RolMenuPermiso(role=rol, **DEFAULT_ROL_PERMISOS[rol]) for rol in DEFAULT_ROL_PERMISOS]

    forms = [RolMenuPermisoForm(prefix=permiso.role, instance=permiso) for permiso in roles_permisos]

    if request.method == 'POST':
        forms = [RolMenuPermisoForm(request.POST, prefix=permiso.role, instance=permiso) for permiso in roles_permisos]
        if all(form.is_valid() for form in forms):
            try:
                for form in forms:
                    form.save()
                # Actualizar los permisos de la sesión del administrador
                request.session['usuario_permisos'] = obtener_permisos_por_rol(request.session.get('usuario_rol', 'Administrador'))
                messages.success(request, 'Permisos actualizados correctamente.')
                return redirect('configurar_permisos')
            except ProgrammingError:
                messages.error(request, 'No se pudo guardar en la base de datos porque falta la tabla de permisos.')

    context = {
        'forms': forms,
        'roles_permisos': roles_permisos,
    }
    return render(request, 'gestion/configurar_permisos.html', context)


def logout_view(request):
    """
    EXPLICACIÓN: Vista para cerrar sesión.
    
    QUÉ HACE:
    - Elimina la sesión del usuario (lo desautentica)
    - Lo redirige a la página de login
    """
    # Eliminar la sesión
    for key in ['usuario_id', 'usuario_email', 'usuario_rol', 'usuario_permisos']:
        if key in request.session:
            del request.session[key]
    
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('login')


# ============ VISTAS DE LA APLICACIÓN (protegidas) ============

@requiere_login
def inicio(request):
    """Vista de inicio - Solo para usuarios logueados"""
    context = {
        'total_clientes': Cliente.objects.count(),
        'total_empleados': Empleado.objects.count(),
        'total_mesas': Mesa.objects.count(),
        'total_platos': Plato.objects.count(),
        'total_ordenes': Orden.objects.count(),
        'total_facturas': Factura.objects.count(),
    }
    return render(request, 'gestion/inicio.html', context)


# ============ CRUD CLIENTES ============

@requiere_login
@requiere_permiso('clientes')
def lista_clientes(request):
    """
    EXPLICACIÓN: Muestra la lista de todos los clientes.
    
    QUÉ HACE:
    - Obtiene todos los clientes de la BD
    - Los pasa al template para mostrar en una tabla
    """
    clientes = Cliente.objects.all()
    return render(request, 'gestion/clientes.html', {'clientes': clientes})


@requiere_login
@requiere_permiso('clientes')
def crear_cliente(request):
    """
    EXPLICACIÓN: Vista para crear un nuevo cliente.
    
    QUÉ HACE:
    - GET: Muestra el formulario vacío
    - POST: Valida y guarda el nuevo cliente
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado correctamente.")
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    
    return render(request, 'gestion/cliente_form.html', {'form': form, 'titulo': 'Crear Cliente'})


@requiere_login
@requiere_permiso('clientes')
def editar_cliente(request, pk):
    """
    EXPLICACIÓN: Vista para editar un cliente existente.
    
    QUÉ HACE:
    - GET: Muestra el formulario con los datos actuales
    - POST: Valida y actualiza el cliente
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente actualizado correctamente.")
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'gestion/cliente_form.html', {'form': form, 'titulo': 'Editar Cliente', 'cliente': cliente})


@requiere_login
@requiere_permiso('clientes')
def eliminar_cliente(request, pk):
    """
    EXPLICACIÓN: Vista para eliminar un cliente.
    
    QUÉ HACE:
    - GET: Muestra una página de confirmación
    - POST: Elimina el cliente
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, "Cliente eliminado correctamente.")
        return redirect('lista_clientes')
    
    return render(request, 'gestion/confirmar_eliminar.html', {'objeto': cliente, 'tipo': 'Cliente'})


# ============ CRUD EMPLEADOS ============

@requiere_login
@requiere_permiso('empleados')
def lista_empleados(request):
    """
    EXPLICACIÓN: Muestra la lista de todos los usuarios con roles de Empleado y Cajero.
    """
    empleados = Usuario.objects.filter(rol__in=['Empleado', 'Cajero'])
    return render(request, 'gestion/empleados.html', {'empleados': empleados})


@requiere_login
@requiere_permiso('empleados')
def crear_empleado(request):
    """
    EXPLICACIÓN: Vista para crear un nuevo empleado.
    """
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado creado correctamente.")
            return redirect('lista_empleados')
    else:
        form = EmpleadoForm()
    
    return render(request, 'gestion/empleado_form.html', {'form': form, 'titulo': 'Crear Empleado'})


@requiere_login
@requiere_permiso('empleados')
def editar_empleado(request, pk):
    """
    EXPLICACIÓN: Vista para editar un empleado existente.
    """
    empleado = get_object_or_404(Empleado, pk=pk)
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado actualizado correctamente.")
            return redirect('lista_empleados')
    else:
        form = EmpleadoForm(instance=empleado)
    
    return render(request, 'gestion/empleado_form.html', {'form': form, 'titulo': 'Editar Empleado', 'empleado': empleado})


@requiere_login
@requiere_permiso('empleados')
def eliminar_empleado(request, pk):
    """
    EXPLICACIÓN: Vista para eliminar un empleado.
    """
    empleado = get_object_or_404(Empleado, pk=pk)
    
    if request.method == 'POST':
        empleado.delete()
        messages.success(request, "Empleado eliminado correctamente.")
        return redirect('lista_empleados')
    
    return render(request, 'gestion/confirmar_eliminar.html', {'objeto': empleado, 'tipo': 'Empleado'})


# ============ CRUD MESAS ============

@requiere_login
@requiere_permiso('mesas')
def lista_mesas(request):
    """
    EXPLICACIÓN: Muestra la lista de todas las mesas.
    """
    mesas = Mesa.objects.all()
    return render(request, 'gestion/mesas.html', {'mesas': mesas})


@requiere_login
@requiere_permiso('mesas')
def crear_mesa(request):
    """
    EXPLICACIÓN: Vista para crear una nueva mesa.
    """
    if request.method == 'POST':
        form = MesaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mesa creada correctamente.")
            return redirect('lista_mesas')
    else:
        form = MesaForm()
    
    return render(request, 'gestion/mesa_form.html', {'form': form, 'titulo': 'Crear Mesa'})


@requiere_login
@requiere_permiso('mesas')
def editar_mesa(request, pk):
    """
    EXPLICACIÓN: Vista para editar una mesa existente.
    """
    mesa = get_object_or_404(Mesa, pk=pk)
    
    if request.method == 'POST':
        form = MesaForm(request.POST, instance=mesa)
        if form.is_valid():
            form.save()
            messages.success(request, "Mesa actualizada correctamente.")
            return redirect('lista_mesas')
    else:
        form = MesaForm(instance=mesa)
    
    return render(request, 'gestion/mesa_form.html', {'form': form, 'titulo': 'Editar Mesa', 'mesa': mesa})


@requiere_login
@requiere_permiso('mesas')
def eliminar_mesa(request, pk):
    """
    EXPLICACIÓN: Vista para eliminar una mesa.
    """
    mesa = get_object_or_404(Mesa, pk=pk)
    
    if request.method == 'POST':
        mesa.delete()
        messages.success(request, "Mesa eliminada correctamente.")
        return redirect('lista_mesas')
    
    return render(request, 'gestion/confirmar_eliminar.html', {'objeto': mesa, 'tipo': 'Mesa'})


# ============ CRUD PLATOS ============

@requiere_login
@requiere_permiso('platos')
def lista_platos(request):
    """
    EXPLICACIÓN: Muestra la lista de todos los platos.
    """
    platos = Plato.objects.all()
    return render(request, 'gestion/platos.html', {'platos': platos})


@requiere_login
@requiere_permiso('platos')
def crear_plato(request):
    """
    EXPLICACIÓN: Vista para crear un nuevo plato.
    """
    if request.method == 'POST':
        form = PlatoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plato creado correctamente.")
            return redirect('lista_platos')
    else:
        form = PlatoForm()
    
    return render(request, 'gestion/plato_form.html', {'form': form, 'titulo': 'Crear Plato'})


@requiere_login
@requiere_permiso('platos')
def editar_plato(request, pk):
    """
    EXPLICACIÓN: Vista para editar un plato existente.
    """
    plato = get_object_or_404(Plato, pk=pk)
    
    if request.method == 'POST':
        form = PlatoForm(request.POST, instance=plato)
        if form.is_valid():
            form.save()
            messages.success(request, "Plato actualizado correctamente.")
            return redirect('lista_platos')
    else:
        form = PlatoForm(instance=plato)
    
    return render(request, 'gestion/plato_form.html', {'form': form, 'titulo': 'Editar Plato', 'plato': plato})


@requiere_login
@requiere_permiso('platos')
def eliminar_plato(request, pk):
    """
    EXPLICACIÓN: Vista para eliminar un plato.
    """
    plato = get_object_or_404(Plato, pk=pk)
    
    if request.method == 'POST':
        plato.delete()
        messages.success(request, "Plato eliminado correctamente.")
        return redirect('lista_platos')
    
    return render(request, 'gestion/confirmar_eliminar.html', {'objeto': plato, 'tipo': 'Plato'})


# ============ VISTAS DE SOLO LECTURA (Órdenes y Facturas) ============

@requiere_login
@requiere_permiso('ordenes')
def lista_ordenes(request):
    """Vista de órdenes - Solo para usuarios logueados"""
    ordenes = Orden.objects.select_related('cliente', 'empleado', 'mesa').prefetch_related('detalles')
    return render(request, 'gestion/ordenes.html', {'ordenes': ordenes})


@requiere_login
@requiere_permiso('ordenes')
def crear_orden(request):
    """Vista para crear una nueva orden."""
    if request.method == 'POST':
        form = OrdenForm(request.POST)
        orden = Orden()
        detalle_formset = DetalleOrdenFormSet(request.POST, instance=orden)

        if form.is_valid() and detalle_formset.is_valid():
            with transaction.atomic():
                orden = form.save(commit=False)
                orden.total = Decimal('0.00')
                orden.save()
                detalle_formset.instance = orden
                detalle_formset.save()
                orden.total = sum((detalle.subtotal or Decimal('0.00')) for detalle in orden.detalles.all())
                orden.save()

            messages.success(request, "Orden creada correctamente.")
            return redirect('lista_ordenes')
    else:
        form = OrdenForm()
        detalle_formset = DetalleOrdenFormSet(instance=Orden())

    return render(request, 'gestion/orden_form.html', {
        'form': form,
        'formset': detalle_formset,
        'titulo': 'Crear Orden'
    })


@requiere_login
@requiere_permiso('ordenes')
def editar_orden(request, pk):
    """Vista para editar una orden existente."""
    orden = get_object_or_404(Orden, pk=pk)
    if request.method == 'POST':
        form = OrdenForm(request.POST, instance=orden)
        detalle_formset = DetalleOrdenFormSet(request.POST, instance=orden)

        if form.is_valid() and detalle_formset.is_valid():
            with transaction.atomic():
                form.save()
                detalle_formset.save()
                orden.total = sum((detalle.subtotal or Decimal('0.00')) for detalle in orden.detalles.all())
                orden.save()

            messages.success(request, "Orden actualizada correctamente.")
            return redirect('lista_ordenes')
    else:
        form = OrdenForm(instance=orden)
        detalle_formset = DetalleOrdenFormSet(instance=orden)

    return render(request, 'gestion/orden_form.html', {
        'form': form,
        'formset': detalle_formset,
        'titulo': 'Editar Orden',
        'orden': orden
    })


@requiere_login
@requiere_permiso('ordenes')
def eliminar_orden(request, pk):
    """Vista para eliminar una orden."""
    orden = get_object_or_404(Orden, pk=pk)
    if request.method == 'POST':
        orden.delete()
        messages.success(request, "Orden eliminada correctamente.")
        return redirect('lista_ordenes')
    return render(request, 'gestion/confirmar_eliminar.html', {'objeto': orden, 'tipo': 'Orden'})


@requiere_login
@requiere_permiso('facturas')
def lista_facturas(request):
    """Vista de facturas - Solo para usuarios logueados"""
    facturas = Factura.objects.all()
    return render(request, 'gestion/facturas.html', {'facturas': facturas})


@requiere_login
@requiere_permiso('facturas')
def crear_factura(request):
    """Vista para crear una nueva factura."""
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Factura creada correctamente.")
            return redirect('lista_facturas')
    else:
        form = FacturaForm()
    return render(request, 'gestion/factura_form.html', {'form': form, 'titulo': 'Crear Factura'})


@requiere_login
@requiere_permiso('facturas')
def editar_factura(request, pk):
    """Vista para editar una factura existente."""
    factura = get_object_or_404(Factura, pk=pk)
    if request.method == 'POST':
        form = FacturaForm(request.POST, instance=factura)
        if form.is_valid():
            form.save()
            messages.success(request, "Factura actualizada correctamente.")
            return redirect('lista_facturas')
    else:
        form = FacturaForm(instance=factura)
    return render(request, 'gestion/factura_form.html', {'form': form, 'titulo': 'Editar Factura', 'factura': factura})


@requiere_login
@requiere_permiso('facturas')
def eliminar_factura(request, pk):
    """Vista para eliminar una factura."""
    factura = get_object_or_404(Factura, pk=pk)
    if request.method == 'POST':
        factura.delete()
        messages.success(request, "Factura eliminada correctamente.")
        return redirect('lista_facturas')
    return render(request, 'gestion/confirmar_eliminar.html', {'objeto': factura, 'tipo': 'Factura'})
