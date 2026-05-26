from decimal import Decimal
from django import forms
from django.contrib.auth.hashers import make_password
from django.db import connection
from .models import Usuario, RolMenuPermiso, Cliente, Empleado, Mesa, Plato, Orden, Factura


class LoginForm(forms.Form):
    """
    EXPLICACIÓN: Formulario de login personalizado.
    
    Este formulario valida que:
    1. El email sea válido
    2. La contraseña no esté vacía
    
    Lo usamos en lugar del formulario de Django por defecto porque
    nuestros usuarios se autentican con EMAIL, no con username.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Ingrese su email',
            'required': True
        })
    )
    contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control-custom',
            'placeholder': '••••••••',
            'required': True
        }),
        label='Contraseña'
    )


class RegistroForm(forms.ModelForm):
    """
    EXPLICACIÓN: Formulario para registrar nuevos usuarios.
    
    Este formulario:
    1. Valida que el email sea único (no puede haber duplicados)
    2. Valida que las contraseñas coincidan
    3. Encripta la contraseña antes de guardarla
    4. Crea el usuario en la base de datos usando SQL directo
    
    ¿POR QUÉ SQL DIRECTO?
    Django tiene problemas con campos IDENTITY de SQL Server.
    Usar connection.cursor() nos permite insertar directamente en la BD
    sin que Django intente manejar el ID (SQL Server lo genera automáticamente).
    """
    
    # Campo para confirmar contraseña (no está en el modelo, pero lo necesitamos)
    contrasena_confirmacion = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Confirme su contraseña',
        }),
        label='Confirmar Contraseña'
    )

    rol = forms.ChoiceField(
        choices=Usuario.ROLES,
        widget=forms.Select(attrs={
            'class': 'form-control-custom',
        }),
        label='Rol'
    )
    
    class Meta:
        model = Usuario
        fields = ['email', 'contrasena', 'rol']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ingrese su email',
            }),
            'contrasena': forms.PasswordInput(attrs={
                'class': 'form-control-custom',
                'placeholder': '••••••••',
            }),
        }
        labels = {
            'email': 'Email',
            'contrasena': 'Contraseña',
            'rol': 'Rol',
        }
    
    def clean(self):
        """
        EXPLICACIÓN: Método que valida todo el formulario.
        
        Aquí verificamos:
        1. Que las contraseñas coincidan
        2. Que el email no esté ya registrado
        """
        cleaned_data = super().clean()
        contrasena = cleaned_data.get('contrasena')
        contrasena_confirmacion = cleaned_data.get('contrasena_confirmacion')
        email = cleaned_data.get('email')
        
        # Validar que las contraseñas coincidan
        if contrasena and contrasena_confirmacion:
            if contrasena != contrasena_confirmacion:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        
        # Validar que el email no esté registrado
        if email and Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        
        # Validar que la contraseña sea segura (mínimo 6 caracteres)
        if contrasena and len(contrasena) < 6:
            raise forms.ValidationError("La contraseña debe tener al menos 6 caracteres.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        EXPLICACIÓN: Método personalizado para guardar usando SQL directo.
        
        En lugar de usar el ORM de Django (que tiene problemas con IDENTITY),
        usamos SQL directo para insertar en la tabla.
        
        VENTAJAS:
        - SQL Server maneja automáticamente el id_usuario (IDENTITY)
        - No hay conflictos entre Django y SQL Server
        - La contraseña se encripta antes de guardar
        
        PASOS:
        1. Encriptar la contraseña
        2. Usar connection.cursor() para obtener una conexión SQL
        3. Ejecutar INSERT directamente
        4. Hacer commit a la BD
        """
        email = self.cleaned_data['email']
        contrasena_plana = self.cleaned_data['contrasena']
        rol = self.cleaned_data.get('rol', 'Administrador')

        # Mapear el rol del formulario al valor exacto que espera la BD
        ROLE_DB_MAP = {
            'Administrador': 'administrador del restaurante',
            'Empleado': 'Empleado',
            'Cajero': 'Cajero',
        }
        db_rol = ROLE_DB_MAP.get(rol, rol)

        # Paso 1: Encriptar la contraseña
        contrasena_encriptada = make_password(contrasena_plana)

        # Paso 2 y 3: Usar SQL directo para insertar
        # Nota: No incluimos id_usuario porque SQL Server lo genera automáticamente
        sql = """
            INSERT INTO usuarios (email, contrasena, rol)
            VALUES (%s, %s, %s)
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, [email, contrasena_encriptada, db_rol])

            # Paso 4: El commit se hace automáticamente con el context manager
            return True

        except Exception as e:
            raise forms.ValidationError(f"Error al crear el usuario: {str(e)}")


class RolMenuPermisoForm(forms.ModelForm):
    """Formulario para editar los permisos de visualización de cada rol."""

    class Meta:
        model = RolMenuPermiso
        fields = [
            'ver_clientes',
            'ver_empleados',
            'ver_mesas',
            'ver_platos',
            'ver_ordenes',
            'ver_facturas',
            'ver_usuarios',
        ]
        widgets = {
            'ver_clientes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ver_empleados': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ver_mesas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ver_platos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ver_ordenes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ver_facturas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ver_usuarios': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ============ FORMULARIOS PARA CRUD ============

class ClienteForm(forms.ModelForm):
    """
    EXPLICACIÓN: Formulario para crear/editar clientes.
    
    Los campos son:
    - nombre: Nombre del cliente (requerido)
    - telefono: Teléfono de contacto (opcional)
    - correo: Email del cliente (opcional pero único)
    """
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'correo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cliente',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono (ej: 3001234567)',
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'telefono': 'Teléfono',
            'correo': 'Email',
        }


class EmpleadoForm(forms.ModelForm):
    """
    EXPLICACIÓN: Formulario para crear/editar empleados.
    
    Los campos son:
    - nombre: Nombre del empleado (requerido)
    - cargo: Tipo de cargo (Mesero, Cajero, etc)
    - telefono: Teléfono de contacto (opcional)
    - correo: Email del empleado (opcional pero único)
    """
    class Meta:
        model = Empleado
        fields = ['nombre', 'cargo', 'telefono', 'correo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del empleado',
            }),
            'cargo': forms.Select(attrs={
                'class': 'form-control',
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono',
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'cargo': 'Cargo',
            'telefono': 'Teléfono',
            'correo': 'Email',
        }


class MesaForm(forms.ModelForm):
    """
    EXPLICACIÓN: Formulario para crear/editar mesas.
    
    Los campos son:
    - numero_mesa: Número identificador de la mesa
    - capacidad: Cuántas personas pueden sentarse
    - estado_mesa: Disponible, Ocupada o Reservada
    """
    class Meta:
        model = Mesa
        fields = ['numero_mesa', 'capacidad', 'estado_mesa']
        widgets = {
            'numero_mesa': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1, 2, 3...',
            }),
            'capacidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 4',
            }),
            'estado_mesa': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        labels = {
            'numero_mesa': 'Número de Mesa',
            'capacidad': 'Capacidad',
            'estado_mesa': 'Estado',
        }


class PlatoForm(forms.ModelForm):
    """
    EXPLICACIÓN: Formulario para crear/editar platos.
    
    Los campos son:
    - nombre_plato: Nombre del plato
    - descripcion: Descripción de ingredientes (opcional)
    - precio: Precio del plato
    - categoria: Categoría (Entrada, Plato fuerte, etc)
    - disponible: Si está disponible o no
    """
    class Meta:
        model = Plato
        fields = ['nombre_plato', 'descripcion', 'precio', 'categoria', 'disponible']
        widgets = {
            'nombre_plato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del plato',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción (ingredientes, alergenos, etc)',
                'rows': 3,
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Entrada, Plato fuerte, Postre',
            }),
            'disponible': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'nombre_plato': 'Nombre del Plato',
            'descripcion': 'Descripción',
            'precio': 'Precio',
            'categoria': 'Categoría',
            'disponible': 'Disponible',
        }


class OrdenForm(forms.ModelForm):
    """
    EXPLICACIÓN: Formulario para crear/editar órdenes.
    
    Incluye:
    - cliente
    - empleado
    - mesa
    - estado_orden
    - total
    """
    class Meta:
        model = Orden
        fields = ['cliente', 'empleado', 'mesa', 'estado_orden', 'total']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'empleado': forms.Select(attrs={'class': 'form-control'}),
            'mesa': forms.Select(attrs={'class': 'form-control'}),
            'estado_orden': forms.Select(attrs={'class': 'form-control'}),
            'total': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Total de la orden',
                'step': '0.01',
            }),
        }
        labels = {
            'cliente': 'Cliente',
            'empleado': 'Empleado',
            'mesa': 'Mesa',
            'estado_orden': 'Estado de la Orden',
            'total': 'Total',
        }


class FacturaForm(forms.ModelForm):
    """
    EXPLICACIÓN: Formulario para crear/editar facturas.
    
    Este formulario calcula automáticamente:
    - subtotal = orden.total
    - total_factura = subtotal + impuesto
    """
    class Meta:
        model = Factura
        fields = ['orden', 'impuesto', 'metodo_pago']
        widgets = {
            'orden': forms.Select(attrs={'class': 'form-control'}),
            'impuesto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Impuesto en número',
                'step': '0.01',
            }),
            'metodo_pago': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'orden': 'Orden',
            'impuesto': 'Impuesto',
            'metodo_pago': 'Método de Pago',
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        orden = self.cleaned_data.get('orden')
        impuesto = self.cleaned_data.get('impuesto') or Decimal('0.00')

        if orden is not None:
            instance.subtotal = orden.total
            instance.total_factura = orden.total + impuesto

        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['orden'].queryset = Orden.objects.filter(pk=self.instance.orden.pk)
        else:
            self.fields['orden'].queryset = Orden.objects.exclude(factura__isnull=False)

    def clean_orden(self):
        orden = self.cleaned_data.get('orden')
        if orden and Factura.objects.filter(orden=orden).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Esta orden ya tiene una factura asociada.')
        return orden

    def clean_impuesto(self):
        impuesto = self.cleaned_data.get('impuesto')
        if impuesto is not None and impuesto < 0:
            raise forms.ValidationError('El impuesto no puede ser negativo.')
        return impuesto

    def save(self, commit=True):
        factura = super().save(commit=False)
        factura.subtotal = factura.orden.total
        factura.total_factura = factura.subtotal + factura.impuesto
        if commit:
            factura.save()
        return factura

