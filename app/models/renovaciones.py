from app import db
from datetime import datetime, timezone

class RenovacionEquipo(db.Model):
    __tablename__ = 'renovaciones_equipos'
    
    id_renovacion = db.Column(db.Integer, primary_key=True)
    id_prestamo = db.Column(db.Integer, db.ForeignKey('prestamos.id_prestamo'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_administrador = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)
    
    fecha_solicitud = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_respuesta = db.Column(db.DateTime, nullable=True)
    
    fecha_esperada_original = db.Column(db.DateTime, nullable=False)
    fecha_esperada_nueva = db.Column(db.DateTime, nullable=True)
    
    estado = db.Column(db.String(20), default='pendiente') # pendiente, aprobada, rechazada
    motivo_solicitud = db.Column(db.Text, nullable=False)
    motivo_rechazo = db.Column(db.String(255), nullable=True)
    
    # Relaciones
    prestamo = db.relationship('Prestamo', backref=db.backref('historial_renovaciones', lazy=True, order_by='RenovacionEquipo.fecha_solicitud.desc()'))
    usuario = db.relationship('Usuario', foreign_keys=[id_usuario])
    administrador = db.relationship('Usuario', foreign_keys=[id_administrador])
    
    def save(self):
        db.session.add(self)

class RenovacionLibro(db.Model):
    __tablename__ = 'renovaciones_libros'
    
    id_renovacion = db.Column(db.Integer, primary_key=True)
    id_prestamo_libro = db.Column(db.Integer, db.ForeignKey('prestamos_libros.id_prestamo_libro'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_administrador = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)
    
    fecha_solicitud = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_respuesta = db.Column(db.DateTime, nullable=True)
    
    fecha_esperada_original = db.Column(db.DateTime, nullable=False)
    fecha_esperada_nueva = db.Column(db.DateTime, nullable=True)
    
    estado = db.Column(db.String(20), default='pendiente') # pendiente, aprobada, rechazada
    motivo_solicitud = db.Column(db.Text, nullable=False)
    motivo_rechazo = db.Column(db.String(255), nullable=True)
    
    # Relaciones
    prestamo_libro = db.relationship('PrestamoLibro', backref=db.backref('historial_renovaciones', lazy=True, order_by='RenovacionLibro.fecha_solicitud.desc()'))
    usuario = db.relationship('Usuario', foreign_keys=[id_usuario])
    administrador = db.relationship('Usuario', foreign_keys=[id_administrador])
    
    def save(self):
        db.session.add(self)
