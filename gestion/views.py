from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Importar modelos
from .models import Cliente, Empleado, Mesa, Orden, Factura, Plato, Usuario
# Importar formularios
from .forms import (
    LoginForm, RegistroForm, ClienteForm, EmpleadoForm,
    MesaForm, PlatoForm, OrdenForm, FacturaForm
)


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


def registro_view(request):
    """
    EXPLICACIÓN: Vista para registrar nuevos usuarios.
    
    QUÉ HACE:
    1. Si el método es GET: Muestra el formulario de registro
    2. Si el método es POST:
       - Valida los datos del formulario
       - Si son válidos, crea el usuario usando SQL directo
       - Si hay errores, muestra los errores
    """
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        
        if form.is_valid():
            try:
                # Guardar el nuevo usuario (esto usa SQL directo)
                form.save()
                
                # Mostrar mensaje de éxito
                messages.success(request, "¡Usuario registrado correctamente! Por favor inicia sesión.")
                
                # Redirigir al login para que inicie sesión
                return redirect('login')
            
            except Exception as e:
                # Si hay error, mostrar mensaje
                messages.error(request, f"Error al registrar: {str(e)}")
    
    else:
        form = RegistroForm()
    
    context = {'form': form}
    return render(request, 'gestion/register.html', context)


def logout_view(request):
    """
    EXPLICACIÓN: Vista para cerrar sesión.
    
    QUÉ HACE:
    - Elimina la sesión del usuario (lo desautentica)
    - Lo redirige a la página de login
    """
    # Eliminar la sesión
    if 'usuario_id' in request.session:
        del request.session['usuario_id']
    if 'usuario_email' in request.session:
        del request.session['usuario_email']
    
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect('login')


# Middleware para verificar sesión
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


# ============ VISTAS DE LA APLICACIÓN (protegidas) ============

@requiere_login
def inicio(request):
    """Vista de inicio - Solo para usuarios logueados"""
    context = {
        'total_clientes': Cliente.objects.count(),
        'total_Empleado': Empleado.objects.count(),
        'total_Mesa': Mesa.objects.count(),
        'total_Orden': Orden.objects.count(),
        'total_Factura': Factura.objects.count(),
    }
    return render(request, 'gestion/inicio.html', context)


# ============ CRUD CLIENTES ============

@requiere_login
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
def lista_empleados(request):
    """
    EXPLICACIÓN: Muestra la lista de todos los empleados.
    """
    empleados = Empleado.objects.all()
    return render(request, 'gestion/empleados.html', {'empleados': empleados})


@requiere_login
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
def lista_mesas(request):
    """
    EXPLICACIÓN: Muestra la lista de todas las mesas.
    """
    mesas = Mesa.objects.all()
    return render(request, 'gestion/mesas.html', {'mesas': mesas})


@requiere_login
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
def lista_platos(request):
    """
    EXPLICACIÓN: Muestra la lista de todos los platos.
    """
    platos = Plato.objects.all()
    return render(request, 'gestion/platos.html', {'platos': platos})


@requiere_login
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
def lista_ordenes(request):
    """Vista de órdenes - Solo para usuarios logueados"""
    ordenes = Orden.objects.all()
    return render(request, 'gestion/ordenes.html', {'ordenes': ordenes})


@requiere_login
def crear_orden(request):
    """Vista para crear una nueva orden."""
    if request.method == 'POST':
        form = OrdenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Orden creada correctamente.")
            return redirect('lista_ordenes')
    else:
        form = OrdenForm()
    return render(request, 'gestion/orden_form.html', {'form': form, 'titulo': 'Crear Orden'})


@requiere_login
def editar_orden(request, pk):
    """Vista para editar una orden existente."""
    orden = get_object_or_404(Orden, pk=pk)
    if request.method == 'POST':
        form = OrdenForm(request.POST, instance=orden)
        if form.is_valid():
            form.save()
            messages.success(request, "Orden actualizada correctamente.")
            return redirect('lista_ordenes')
    else:
        form = OrdenForm(instance=orden)
    return render(request, 'gestion/orden_form.html', {'form': form, 'titulo': 'Editar Orden', 'orden': orden})


@requiere_login
def eliminar_orden(request, pk):
    """Vista para eliminar una orden."""
    orden = get_object_or_404(Orden, pk=pk)
    if request.method == 'POST':
        orden.delete()
        messages.success(request, "Orden eliminada correctamente.")
        return redirect('lista_ordenes')
    return render(request, 'gestion/confirmar_eliminar.html', {'objeto': orden, 'tipo': 'Orden'})


@requiere_login
def lista_facturas(request):
    """Vista de facturas - Solo para usuarios logueados"""
    facturas = Factura.objects.all()
    return render(request, 'gestion/facturas.html', {'facturas': facturas})


@requiere_login
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
def eliminar_factura(request, pk):
    """Vista para eliminar una factura."""
    factura = get_object_or_404(Factura, pk=pk)
    if request.method == 'POST':
        factura.delete()
        messages.success(request, "Factura eliminada correctamente.")
        return redirect('lista_facturas')
    return render(request, 'gestion/confirmar_eliminar.html', {'objeto': factura, 'tipo': 'Factura'})
