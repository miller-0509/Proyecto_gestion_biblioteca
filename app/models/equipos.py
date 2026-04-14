from app import db
from datetime import datetime, timezone


class Equipo(db.Model):
    __tablename__ = 'equipos'

    id_equipo           = db.Column(db.Integer, primary_key=True)
    nombre              = db.Column(db.String(150), nullable=False)
    tipo_equipo         = db.Column(db.String(50), nullable=False)  # Laptop, monitor, teclado, herramienta, etc.
    marca               = db.Column(db.String(100))
    modelo              = db.Column(db.String(100))
    numero_serie        = db.Column(db.String(100), unique=True, nullable=False)
    estado              = db.Column(db.Enum('disponible', 'prestado', 'mantenimiento', 'dañado'), default='disponible')
    ubicacion           = db.Column(db.String(150))  # Biblioteca, Almacén, Aula X, etc.
    fecha_registro      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_compra        = db.Column(db.Date)
    proveedor           = db.Column(db.String(150))
    responsable         = db.Column(db.String(150))  # Persona o área responsable
    disponible_prestamo = db.Column(db.Boolean, default=True)  # ¿Disponible para préstamo?
    tiempo_max_prestamo = db.Column(db.Integer)  # Tiempo máximo de préstamo en días
    descripcion         = db.Column(db.Text)  # Descripción adicional

    def __repr__(self):
        return f'<Equipo {self.nombre}>'

    def to_dict(self):
        return {
            'id_equipo': self.id_equipo,
            'nombre': self.nombre,
            'tipo_equipo': self.tipo_equipo,
            'marca': self.marca,
            'modelo': self.modelo,
            'numero_serie': self.numero_serie,
            'estado': self.estado,
            'ubicacion': self.ubicacion,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'fecha_compra': self.fecha_compra.isoformat() if self.fecha_compra else None,
            'proveedor': self.proveedor,
            'responsable': self.responsable,
            'disponible_prestamo': self.disponible_prestamo,
            'tiempo_max_prestamo': self.tiempo_max_prestamo,
        }

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def validate_equipo(nombre, tipo_equipo, numero_serie):
        errors = []
        if not nombre or not nombre.strip():
            errors.append('El nombre del equipo es obligatorio.')
        if not tipo_equipo or not tipo_equipo.strip():
            errors.append('El tipo de equipo es obligatorio.')
        if not numero_serie or not numero_serie.strip():
            errors.append('El número de serie es obligatorio.')
        elif Equipo.query.filter_by(numero_serie=numero_serie).first():
            errors.append('Ya existe un equipo con ese número de serie.')
        return errors
