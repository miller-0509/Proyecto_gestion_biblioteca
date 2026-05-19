from app import db
from datetime import datetime, timezone

class PrestamoLibro(db.Model):
    __tablename__ = 'prestamos_libros'
    
    id_prestamo_libro = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_libro = db.Column(db.Integer, db.ForeignKey('libros.id_libro'), nullable=False)
    id_administrador = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)
    
    fecha_solicitud = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    fecha_aprobacion = db.Column(db.DateTime, nullable=True)
    fecha_devolucion_esperada = db.Column(db.DateTime, nullable=True)
    fecha_devolucion_real = db.Column(db.DateTime, nullable=True)
    
    estado = db.Column(db.String(20), default='pendiente')
    razon_rechazo = db.Column(db.String(255), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    
    # Devolucion
    observacion_devolucion = db.Column(db.Text, nullable=True)
    estado_fisico_devolucion = db.Column(db.String(20), nullable=True)
    
    # Tracking de notificaciones
    notificacion_vencimiento_enviada = db.Column(db.Boolean, default=False)
    notificacion_vencido_enviada = db.Column(db.Boolean, default=False)
    
    usuario = db.relationship('Usuario', foreign_keys=[id_usuario], backref='prestamos_libros_solicitados')
    libro = db.relationship('Libro', foreign_keys=[id_libro], backref='prestamos')
    administrador = db.relationship('Usuario', foreign_keys=[id_administrador], backref='prestamos_libros_gestionados')
    
    @property
    def id_prestamo(self):
        return self.id_prestamo_libro
    
    def save(self):
        db.session.add(self)
    
    def delete(self):
        db.session.delete(self)
    
    @staticmethod
    def validate_crear_prestamo(id_usuario, id_libro, observaciones=None):
        errors = []
        
        from app.models.usuarios import Usuario
        from app.models.libros import Libro
        
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            errors.append('El usuario no existe.')
        elif usuario.rol == 'administrador':
            errors.append('Los administradores no pueden solicitar préstamos de libros.')
        
        libro = Libro.query.get(id_libro)
        if not libro:
            errors.append('El libro no existe.')
        elif not libro.disponible_prestamo:
            errors.append('Este libro no está disponible para préstamo.')
        elif libro.estado != 'disponible':
            errors.append(f'El libro está en estado "{libro.estado}" y no puede prestarse.')
        
        prestamo_activo = PrestamoLibro.query.filter(
            PrestamoLibro.id_libro == id_libro,
            PrestamoLibro.estado.in_(['pendiente', 'aceptado'])
        ).first()
        if prestamo_activo:
            errors.append('Este libro ya tiene un préstamo en proceso.')
        
        return errors
