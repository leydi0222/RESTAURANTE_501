from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Importar modelos
from .models import Cliente, Empleado, Mesa, Orden, Factura, Plato, Usuario
from .forms import LoginForm, RegistroForm


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


@requiere_login
def lista_clientes(request):
    """Vista de clientes - Solo para usuarios logueados"""
    clientes = Cliente.objects.all()
    return render(request, 'gestion/clientes.html', {'clientes': clientes})


@requiere_login
def lista_empleados(request):
    """Vista de empleados - Solo para usuarios logueados"""
    empleados = Empleado.objects.all()
    return render(request, 'gestion/empleados.html', {'empleados': empleados})


@requiere_login
def lista_mesas(request):
    """Vista de mesas - Solo para usuarios logueados"""
    mesas = Mesa.objects.all()
    return render(request, 'gestion/mesas.html', {'mesas': mesas})


@requiere_login
def lista_ordenes(request):
    """Vista de órdenes - Solo para usuarios logueados"""
    ordenes = Orden.objects.all()
    return render(request, 'gestion/ordenes.html', {'ordenes': ordenes})


@requiere_login
def lista_facturas(request):
    """Vista de facturas - Solo para usuarios logueados"""
    facturas = Factura.objects.all()
    return render(request, 'gestion/facturas.html', {'facturas': facturas})


@requiere_login
def lista_platos(request):
    """Vista de platos - Solo para usuarios logueados"""
    platos = Plato.objects.all()
    return render(request, 'gestion/platos.html', {'platos': platos})
