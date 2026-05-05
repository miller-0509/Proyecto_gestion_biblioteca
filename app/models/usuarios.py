import re
from app import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Regex básico para validación de email
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id_usuario      = db.Column(db.Integer, primary_key=True)
    nombres         = db.Column(db.String(100), nullable=False)
    apellidos       = db.Column(db.String(100), nullable=False)
    correo          = db.Column(db.String(150), unique=True, nullable=False)
    password        = db.Column(db.String(255), nullable=False)
    rol             = db.Column(db.Enum('administrador', 'aprendiz', 'instructor'), default='aprendiz')
    estado          = db.Column(db.Enum('activo', 'inactivo', 'bloqueado'), default='activo')
    fecha_registro  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def is_active(self):
        """Flask-Login respeta este property: solo usuarios activos pueden autenticarse."""
        return self.estado == 'activo'

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
        elif not _EMAIL_RE.match(correo):
            errors.append('El formato del correo electrónico no es válido.')
        elif Usuario.query.filter_by(correo=correo).first():
            errors.append('El correo ya está registrado.')
        if not password:
            errors.append('La contraseña es obligatoria.')
        elif len(password) < 6:
            errors.append('La contraseña debe tener al menos 6 caracteres.')
            
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
