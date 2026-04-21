from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, Response
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from models import Usuario, Producto, Venta, DetalleVenta
from datetime import datetime
import json

admin_bp = Blueprint('admin', __name__)

CATEGORIAS = [
    ('camisas', '👕 Camisas'),
    ('gorras', '🧢 Gorras'),
    ('sueteres', '🧥 Suéteres'),
    ('pantalones', '👖 Pantalones'),
    ('tenis', '👟 Tenis'),
    ('accesorios', '💍 Accesorios'),
]

EMOJI_MAP = {
    'camisas': '👕', 'gorras': '🧢', 'sueteres': '🧥',
    'pantalones': '👖', 'tenis': '👟', 'accesorios': '💍',
}


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash('Acceso denegado 🚫', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_productos = Producto.query.filter_by(activo=True).count()
    total_usuarios = Usuario.query.filter_by(tipo='cliente').count()
    total_ventas = Venta.query.count()
    ingresos_total = db.session.query(func.sum(Venta.total)).scalar() or 0

    ventas_recientes = Venta.query.order_by(Venta.fecha.desc()).limit(5).all()

    productos_top = db.session.query(
        Producto.nombre,
        Producto.emoji,
        func.sum(DetalleVenta.cantidad).label('total_vendido')
    ).join(DetalleVenta).group_by(Producto.id).order_by(
        func.sum(DetalleVenta.cantidad).desc()
    ).limit(5).all()

    stock_bajo = Producto.query.filter(
        Producto.stock < 5, Producto.activo == True
    ).all()

    return render_template('admin/dashboard.html',
        total_productos=total_productos,
        total_usuarios=total_usuarios,
        total_ventas=total_ventas,
        ingresos_total=ingresos_total,
        ventas_recientes=ventas_recientes,
        productos_top=productos_top,
        stock_bajo=stock_bajo,
    )


@admin_bp.route('/productos')
@login_required
@admin_required
def productos():
    categoria = request.args.get('categoria', '')
    busqueda = request.args.get('busqueda', '')

    query = Producto.query
    if categoria:
        query = query.filter_by(categoria=categoria)
    if busqueda:
        query = query.filter(Producto.nombre.ilike(f'%{busqueda}%'))

    prods = query.order_by(Producto.fecha_creacion.desc()).all()
    return render_template('admin/productos.html',
        productos=prods, categorias=CATEGORIAS,
        categoria_filtro=categoria, busqueda=busqueda,
    )


@admin_bp.route('/productos/agregar', methods=['GET', 'POST'])
@login_required
@admin_required
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '')
        precio = float(request.form.get('precio', 0))
        stock = int(request.form.get('stock', 0))
        descripcion = request.form.get('descripcion', '')
        imagen_url = request.form.get('imagen_url', '')

        prod = Producto(
            nombre=nombre, categoria=categoria,
            emoji=EMOJI_MAP.get(categoria, '👕'),
            precio=precio, stock=stock,
            descripcion=descripcion, imagen_url=imagen_url,
        )
        db.session.add(prod)
        db.session.commit()
        flash(f'Producto "{nombre}" agregado 🔥', 'success')
        return redirect(url_for('admin.productos'))

    return render_template('admin/agregar_producto.html', categorias=CATEGORIAS)


@admin_bp.route('/productos/editar/<int:pid>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_producto(pid):
    prod = Producto.query.get_or_404(pid)

    if request.method == 'POST':
        prod.nombre = request.form.get('nombre', '').strip()
        prod.categoria = request.form.get('categoria', '')
        prod.emoji = EMOJI_MAP.get(prod.categoria, '👕')
        prod.precio = float(request.form.get('precio', 0))
        prod.stock = int(request.form.get('stock', 0))
        prod.descripcion = request.form.get('descripcion', '')
        prod.imagen_url = request.form.get('imagen_url', '')
        db.session.commit()
        flash(f'Producto "{prod.nombre}" actualizado ✅', 'success')
        return redirect(url_for('admin.productos'))

    return render_template('admin/editar_producto.html', producto=prod, categorias=CATEGORIAS)


@admin_bp.route('/productos/eliminar/<int:pid>', methods=['POST'])
@login_required
@admin_required
def eliminar_producto(pid):
    prod = Producto.query.get_or_404(pid)
    prod.activo = False
    db.session.commit()
    flash(f'Producto "{prod.nombre}" eliminado 🗑️', 'warning')
    return redirect(url_for('admin.productos'))


@admin_bp.route('/ventas')
@login_required
@admin_required
def ventas():
    ventas_lista = Venta.query.order_by(Venta.fecha.desc()).all()
    total_ingresos = db.session.query(func.sum(Venta.total)).scalar() or 0
    return render_template('admin/ventas.html',
        ventas=ventas_lista, total_ingresos=total_ingresos)


@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    usuarios_lista = Usuario.query.filter_by(tipo='cliente').order_by(
        Usuario.fecha_registro.desc()
    ).all()
    return render_template('admin/usuarios.html', usuarios=usuarios_lista)


@admin_bp.route('/backup')
@login_required
@admin_required
def backup():
    data = {
        'usuarios': [
            {'id': u.id, 'nombre': u.nombre, 'correo': u.correo, 'tipo': u.tipo,
             'fecha_registro': str(u.fecha_registro)}
            for u in Usuario.query.all()
        ],
        'productos': [
            {'id': p.id, 'nombre': p.nombre, 'categoria': p.categoria,
             'precio': p.precio, 'stock': p.stock, 'activo': p.activo}
            for p in Producto.query.all()
        ],
        'ventas': [
            {'id': v.id, 'id_usuario': v.id_usuario, 'total': v.total,
             'fecha': str(v.fecha), 'estado': v.estado}
            for v in Venta.query.all()
        ],
    }
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename=backup_sistemadrip_{timestamp}.json'},
    )
