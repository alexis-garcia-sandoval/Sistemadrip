from app import db
from flask_login import UserMixin
from datetime import datetime


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena = db.Column(db.String(256), nullable=False)
    tipo = db.Column(db.String(20), default='cliente')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    carrito = db.relationship('Carrito', backref='usuario', lazy=True, cascade='all, delete-orphan')
    ventas = db.relationship('Venta', backref='usuario', lazy=True)
    favoritos = db.relationship('Favorito', backref='usuario', lazy=True, cascade='all, delete-orphan')


class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    emoji = db.Column(db.String(10), default='👕')
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    descripcion = db.Column(db.Text)
    imagen_url = db.Column(db.String(256))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    carrito_items = db.relationship('Carrito', backref='producto', lazy=True)
    detalles_venta = db.relationship('DetalleVenta', backref='producto', lazy=True)
    favoritos = db.relationship('Favorito', backref='producto', lazy=True)


class Carrito(db.Model):
    __tablename__ = 'carrito'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)


class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='completada')

    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)


class DetalleVenta(db.Model):
    __tablename__ = 'detalles_venta'
    id = db.Column(db.Integer, primary_key=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)


class Favorito(db.Model):
    __tablename__ = 'favoritos'
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    fecha_agregado = db.Column(db.DateTime, default=datetime.utcnow)
