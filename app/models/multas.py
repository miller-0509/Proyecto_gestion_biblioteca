from app import db
from datetime import datetime, timezone

class Multa(db.Model):
    __tablename__ = 'multas'

    id_multa = db.Column(db.Integer, primary_key=True)
    tipo_recurso = db.Column(db.String(20), nullable=False) # 'libro' o 'equipo'
    
    # Foreign keys (uno de los dos será nulo dependiendo del recurso)
    id_prestamo_equipo = db.Column(db.Integer, db.ForeignKey('prestamos.id_prestamo'), nullable=True)
    id_prestamo_libro = db.Column(db.Integer, db.ForeignKey('prestamos_libros.id_prestamo_libro'), nullable=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    
    # Valores de la suspensión
    dias_retraso = db.Column(db.Integer, default=0, nullable=False)
    dias_suspension = db.Column(db.Integer, default=0, nullable=False)
    
    # Fechas
    fecha_generacion = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fecha_inicio_suspension = db.Column(db.DateTime, nullable=True)
    fecha_fin_suspension = db.Column(db.DateTime, nullable=True)
    
    # Estado ('acumulando', 'activa', 'cumplida', 'condonada')
    estado = db.Column(db.String(20), default='acumulando', nullable=False)
    
    # Resolución administrativa
    observacion = db.Column(db.Text, nullable=True)
    id_administrador_resolucion = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    usuario = db.relationship('Usuario', foreign_keys=[id_usuario], backref=db.backref('multas', lazy=True, cascade='all, delete-orphan'))
    prestamo_equipo = db.relationship('Prestamo', foreign_keys=[id_prestamo_equipo], backref=db.backref('multa', uselist=False, cascade='all, delete-orphan'))
    prestamo_libro = db.relationship('PrestamoLibro', foreign_keys=[id_prestamo_libro], backref=db.backref('multa', uselist=False, cascade='all, delete-orphan'))
    administrador_resolucion = db.relationship('Usuario', foreign_keys=[id_administrador_resolucion])

    def to_dict(self):
        return {
            'id_multa': self.id_multa,
            'tipo_recurso': self.tipo_recurso,
            'id_prestamo_equipo': self.id_prestamo_equipo,
            'id_prestamo_libro': self.id_prestamo_libro,
            'id_usuario': self.id_usuario,
            'usuario_nombres': self.usuario.nombre_completo() if self.usuario else None,
            'dias_retraso': self.dias_retraso,
            'dias_suspension': self.dias_suspension,
            'fecha_generacion': self.fecha_generacion.isoformat() if self.fecha_generacion else None,
            'fecha_inicio_suspension': self.fecha_inicio_suspension.isoformat() if self.fecha_inicio_suspension else None,
            'fecha_fin_suspension': self.fecha_fin_suspension.isoformat() if self.fecha_fin_suspension else None,
            'estado': self.estado,
            'observacion': self.observacion,
            'admin_resolucion_nombre': self.administrador_resolucion.nombre_completo() if self.administrador_resolucion else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def save(self):
        db.session.add(self)

    def delete(self):
        db.session.delete(self)
