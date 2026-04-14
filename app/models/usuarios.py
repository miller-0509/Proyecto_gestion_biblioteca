from app import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash


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
        db.session.commit()

    # ── Validaciones ───────────────────────────────
    @staticmethod
    def validate_registro(nombres, apellidos, correo, password, rol):
        errors = []
        if not nombres or not nombres.strip():
            errors.append('El nombre es obligatorio.')
        if not apellidos or not apellidos.strip():
            errors.append('Los apellidos son obligatorios.')
        if not correo or not correo.strip():
            errors.append('El correo es obligatorio.')
        elif Usuario.query.filter_by(correo=correo).first():
            errors.append('El correo ya está registrado.')
        if not password:
            errors.append('La contraseña es obligatoria.')
        elif len(password) < 6:
            errors.append('La contraseña debe tener al menos 6 caracteres.')
        if rol not in ['aprendiz', 'instructor']:
            errors.append('Debes seleccionar un rol válido (aprendiz o instructor).')
        return errors
