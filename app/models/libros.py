from app import db
from datetime import datetime, timezone

class Libro(db.Model):
    __tablename__ = 'libros'

    id_libro            = db.Column(db.Integer, primary_key=True)
    titulo              = db.Column(db.String(255), nullable=False)
    autor               = db.Column(db.String(150), nullable=False)
    genero              = db.Column(db.String(100), nullable=False)
    codigo_unico        = db.Column(db.String(100), unique=True, nullable=False)
    estado              = db.Column(db.Enum('disponible', 'prestado', 'mantenimiento', 'dañado'), default='disponible')
    ubicacion           = db.Column(db.String(150))
    fecha_registro      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    disponible_prestamo = db.Column(db.Boolean, default=True)
    tiempo_max_prestamo = db.Column(db.Integer, default=15)  # 15 dias por defecto
    descripcion         = db.Column(db.Text)

    @property
    def tiene_prestamo_activo(self):
        from app.models.prestamos_libros import PrestamoLibro
        return PrestamoLibro.query.filter(
            PrestamoLibro.id_libro == self.id_libro,
            PrestamoLibro.estado.in_(['pendiente', 'aceptado'])
        ).first() is not None

    def __repr__(self):
        return f'<Libro {self.titulo}>'

    def to_dict(self):
        return {
            'id_libro': self.id_libro,
            'titulo': self.titulo,
            'autor': self.autor,
            'genero': self.genero,
            'codigo_unico': self.codigo_unico,
            'estado': self.estado,
            'ubicacion': self.ubicacion,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'disponible_prestamo': self.disponible_prestamo,
            'tiempo_max_prestamo': self.tiempo_max_prestamo,
            'descripcion': self.descripcion,
        }

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def validate_libro(titulo, autor, genero, codigo_unico):
        errors = []
        if not titulo or not titulo.strip():
            errors.append('El título del libro es obligatorio.')
        if not autor or not autor.strip():
            errors.append('El autor es obligatorio.')
        if not genero or not genero.strip():
            errors.append('El género es obligatorio.')
        if not codigo_unico or not codigo_unico.strip():
            errors.append('El código único es obligatorio.')
        elif Libro.query.filter_by(codigo_unico=codigo_unico).first():
            errors.append('Ya existe un libro con ese código único.')
        return errors
