import re
from app import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Regex básico para validación de email
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id_usuario         = db.Column(db.Integer, primary_key=True)
    nombres            = db.Column(db.String(100), nullable=False)
    apellidos          = db.Column(db.String(100), nullable=False)
    correo             = db.Column(db.String(150), unique=True, nullable=False)
    password           = db.Column(db.String(255), nullable=False)
    rol                = db.Column(db.String(20), default='aprendiz')
    estado             = db.Column(db.String(20), default='activo')
    fecha_registro     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    email_verificado   = db.Column(db.Boolean, default=False, nullable=False, server_default='false')
    fecha_verificacion = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, **kwargs):
        # Normalizar correo si está presente
        if 'correo' in kwargs:
            kwargs['correo'] = kwargs['correo'].strip().lower()
        super(Usuario, self).__init__(**kwargs)

    @property
    def is_active(self):
        """Flask-Login respeta este property: solo usuarios activos pueden autenticarse."""
        if not self.estado:
            return False
        
        # Convertir a string de forma segura y normalizar para comparación
        estado_str = str(self.estado).lower()
        
        # En algunos sistemas el string viene como 'estado_usuario.activo'
        return 'activo' in estado_str

    def get_id(self):
        return str(self.id_usuario)

    def set_password(self, password_plano):
        self.password = generate_password_hash(password_plano)

    def check_password(self, password_plano):
        return check_password_hash(self.password, password_plano)

    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    def to_dict(self):
        return {
            'id_usuario': self.id_usuario,
            'nombres':    self.nombres,
            'apellidos':  self.apellidos,
            'correo':     self.correo,
            'rol':        self.rol,
            'estado':     self.estado,
        }

    def save(self):
        db.session.add(self)

    # ── Validaciones ───────────────────────────────
    @staticmethod
    def validate_registro(nombres, apellidos, correo, password, rol, is_admin=False):
        errors = []
        if not nombres or not nombres.strip():
            errors.append('El nombre es obligatorio.')
        if not apellidos or not apellidos.strip():
            errors.append('Los apellidos son obligatorios.')
        if not correo or not correo.strip():
            errors.append('El correo es obligatorio.')
        else:
            correo_normalizado = correo.strip().lower()
            if not _EMAIL_RE.match(correo_normalizado):
                errors.append('El formato del correo electrónico no es válido.')
            elif Usuario.query.filter_by(correo=correo_normalizado).first():
                errors.append('El correo ya está registrado.')
        if not password:
            errors.append('La contraseña es obligatoria.')
        else:
            if len(password) < 8:
                errors.append('La contraseña debe tener al menos 8 caracteres.')
            if not any(c.isupper() for c in password):
                errors.append('La contraseña debe contener al menos una letra mayúscula.')
            if not any(c.isdigit() for c in password):
                errors.append('La contraseña debe contener al menos un número.')
            
        roles_permitidos = ['aprendiz', 'instructor']
        if is_admin:
            roles_permitidos.append('administrador')
            
        if rol not in roles_permitidos:
            errors.append(f"Debes seleccionar un rol válido ({', '.join(roles_permitidos)}).")
        return errors

    @staticmethod
    def validate_edicion(nombres, apellidos, correo, rol, estado, current_correo=None):
        errors = []
        if not nombres or not nombres.strip():
            errors.append('El nombre es obligatorio.')
        if not apellidos or not apellidos.strip():
            errors.append('Los apellidos son obligatorios.')
        if not correo or not correo.strip():
            errors.append('El correo es obligatorio.')
        elif not _EMAIL_RE.match(correo):
            errors.append('El formato del correo electrónico no es válido.')
        elif correo != current_correo and Usuario.query.filter_by(correo=correo).first():
            errors.append('El correo ya está registrado por otro usuario.')
        
        if rol not in ['administrador', 'aprendiz', 'instructor']:
            errors.append('Debes seleccionar un rol válido.')
        if estado not in ['activo', 'inactivo', 'bloqueado']:
            errors.append('Debes seleccionar un estado válido.')
        return errors
