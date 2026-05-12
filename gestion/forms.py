from django import forms
from django.contrib.auth.hashers import make_password
from django.db import connection
from .models import Usuario


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
    
    class Meta:
        model = Usuario
        fields = ['email', 'contrasena']
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
        rol = 'administrador del restaurante'
        
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
                cursor.execute(sql, [email, contrasena_encriptada, rol])
            
            # Paso 4: El commit se hace automáticamente con el context manager
            return True
        
        except Exception as e:
            raise forms.ValidationError(f"Error al crear el usuario: {str(e)}")

