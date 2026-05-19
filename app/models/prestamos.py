from app import db
from datetime import datetime, timezone, timedelta


class Prestamo(db.Model):
    __tablename__ = 'prestamos'
    
    id_prestamo = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_equipo = db.Column(db.Integer, db.ForeignKey('equipos.id_equipo'), nullable=False)
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
    
    # Renovaciones
    renovaciones_aplicadas = db.Column(db.Integer, default=0)
    estado_renovacion = db.Column(db.String(20), nullable=True) # 'pendiente', etc.
    
    
    # Relaciones
    usuario = db.relationship('Usuario', foreign_keys=[id_usuario], backref='prestamos_solicitados')
    equipo = db.relationship('Equipo', foreign_keys=[id_equipo], backref='prestamos')
    administrador = db.relationship('Usuario', foreign_keys=[id_administrador], backref='prestamos_gestionados')
    
    def to_dict(self):
        return {
            'id_prestamo': self.id_prestamo,
            'id_usuario': self.id_usuario,
            'id_equipo': self.id_equipo,
            'id_administrador': self.id_administrador,
            'usuario_nombres': self.usuario.nombre_completo() if self.usuario else None,
            'equipo_nombre': self.equipo.nombre if self.equipo else None,
            'fecha_solicitud': self.fecha_solicitud.isoformat() if self.fecha_solicitud else None,
            'fecha_aprobacion': self.fecha_aprobacion.isoformat() if self.fecha_aprobacion else None,
            'fecha_devolucion_esperada': self.fecha_devolucion_esperada.isoformat() if self.fecha_devolucion_esperada else None,
            'fecha_devolucion_real': self.fecha_devolucion_real.isoformat() if self.fecha_devolucion_real else None,
            'estado': self.estado,
            'razon_rechazo': self.razon_rechazo,
            'observaciones': self.observaciones,
            'observacion_devolucion': self.observacion_devolucion,
            'estado_fisico_devolucion': self.estado_fisico_devolucion,
        }
    
    def save(self):
        db.session.add(self)
    
    def delete(self):
        db.session.delete(self)
    
    @staticmethod
    def validate_crear_prestamo(id_usuario, id_equipo, observaciones=None):
        """Validar creación de préstamo"""
        errors = []
        
        from app.models.usuarios import Usuario
        from app.models.equipos import Equipo
        
        # Verificar usuario existe
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            errors.append('El usuario no existe.')
        elif usuario.rol == 'administrador':
            errors.append('Los administradores no pueden solicitar préstamos.')
        elif usuario.tiene_multas_pendientes():
            errors.append('No puedes solicitar préstamos porque tienes una sanción por retraso activa o en proceso.')
        
        # Verificar equipo existe
        equipo = Equipo.query.get(id_equipo)
        if not equipo:
            errors.append('El equipo no existe.')
        elif not equipo.disponible_prestamo:
            errors.append('Este equipo no está disponible para préstamo.')
        elif equipo.estado != 'disponible':
            errors.append(f'El equipo está en estado "{equipo.estado}" y no puede prestarse.')
        
        # Verificar si ya existe préstamo activo de este equipo
        prestamo_activo = Prestamo.query.filter(
            Prestamo.id_equipo == id_equipo,
            Prestamo.estado.in_(['pendiente', 'aceptado'])
        ).first()
        if prestamo_activo:
            errors.append('Este equipo ya tiene un préstamo en proceso.')
        
        return errors
