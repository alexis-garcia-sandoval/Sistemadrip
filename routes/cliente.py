from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from models import Producto, Carrito, Venta, DetalleVenta, Favorito

cliente_bp = Blueprint('cliente', __name__)

CATEGORIAS = [
    ('camisas', '👕 Camisas'),
    ('gorras', '🧢 Gorras'),
    ('sueteres', '🧥 Suéteres'),
    ('pantalones', '👖 Pantalones'),
    ('tenis', '👟 Tenis'),
    ('accesorios', '💍 Accesorios'),
]


@cliente_bp.route('/')
@login_required
def tienda():
    categoria = request.args.get('categoria', '')
    busqueda = request.args.get('busqueda', '')

    query = Producto.query.filter_by(activo=True)
    if categoria:
        query = query.filter_by(categoria=categoria)
    if busqueda:
        query = query.filter(Producto.nombre.ilike(f'%{busqueda}%'))

    productos = query.order_by(Producto.fecha_creacion.desc()).all()

    favoritos_ids = {f.id_producto for f in Favorito.query.filter_by(id_usuario=current_user.id).all()}

    return render_template('cliente/tienda.html',
        productos=productos, categorias=CATEGORIAS,
        categoria_filtro=categoria, busqueda=busqueda,
        favoritos_ids=favoritos_ids,
    )


@cliente_bp.route('/carrito')
@login_required
def carrito():
    items = Carrito.query.filter_by(id_usuario=current_user.id).all()
    total = sum(item.producto.precio * item.cantidad for item in items)
    return render_template('cliente/carrito.html', items=items, total=total)


@cliente_bp.route('/carrito/agregar/<int:id_producto>', methods=['POST'])
@login_required
def agregar_carrito(id_producto):
    prod = Producto.query.get_or_404(id_producto)
    cantidad = int(request.form.get('cantidad', 1))

    existente = Carrito.query.filter_by(
        id_usuario=current_user.id, id_producto=id_producto
    ).first()

    if existente:
        existente.cantidad += cantidad
    else:
        db.session.add(Carrito(
            id_usuario=current_user.id,
            id_producto=id_producto,
            cantidad=cantidad,
        ))

    db.session.commit()
    flash(f'{prod.emoji} {prod.nombre} agregado al carrito 🛒', 'success')
    return redirect(request.referrer or url_for('cliente.tienda'))


@cliente_bp.route('/carrito/eliminar/<int:item_id>', methods=['POST'])
@login_required
def eliminar_carrito(item_id):
    item = Carrito.query.get_or_404(item_id)
    if item.id_usuario != current_user.id:
        flash('No autorizado ❌', 'danger')
        return redirect(url_for('cliente.carrito'))
    db.session.delete(item)
    db.session.commit()
    flash('Producto eliminado del carrito 🗑️', 'warning')
    return redirect(url_for('cliente.carrito'))


@cliente_bp.route('/carrito/actualizar/<int:item_id>', methods=['POST'])
@login_required
def actualizar_carrito(item_id):
    item = Carrito.query.get_or_404(item_id)
    if item.id_usuario != current_user.id:
        flash('No autorizado ❌', 'danger')
        return redirect(url_for('cliente.carrito'))

    cantidad = int(request.form.get('cantidad', 1))
    if cantidad <= 0:
        db.session.delete(item)
    else:
        item.cantidad = cantidad
    db.session.commit()
    return redirect(url_for('cliente.carrito'))


@cliente_bp.route('/comprar', methods=['POST'])
@login_required
def comprar():
    items = Carrito.query.filter_by(id_usuario=current_user.id).all()

    if not items:
        flash('Tu carrito está vacío 😢', 'warning')
        return redirect(url_for('cliente.carrito'))

    for item in items:
        if item.producto.stock < item.cantidad:
            flash(f'Stock insuficiente para {item.producto.nombre} ❌', 'danger')
            return redirect(url_for('cliente.carrito'))

    total = sum(item.producto.precio * item.cantidad for item in items)
    venta = Venta(id_usuario=current_user.id, total=total)
    db.session.add(venta)
    db.session.flush()

    for item in items:
        db.session.add(DetalleVenta(
            id_venta=venta.id,
            id_producto=item.id_producto,
            cantidad=item.cantidad,
            precio_unitario=item.producto.precio,
            subtotal=item.producto.precio * item.cantidad,
        ))
        item.producto.stock -= item.cantidad
        db.session.delete(item)

    db.session.commit()
    flash(f'¡Compra realizada! Total: ${total:.2f} MXN 🎉', 'success')
    return redirect(url_for('cliente.historial'))


@cliente_bp.route('/historial')
@login_required
def historial():
    ventas = Venta.query.filter_by(id_usuario=current_user.id).order_by(
        Venta.fecha.desc()
    ).all()
    return render_template('cliente/historial.html', ventas=ventas)


@cliente_bp.route('/favoritos')
@login_required
def favoritos():
    favs = Favorito.query.filter_by(id_usuario=current_user.id).all()
    productos = [f.producto for f in favs if f.producto.activo]
    favoritos_ids = {p.id for p in productos}
    return render_template('cliente/favoritos.html', productos=productos, favoritos_ids=favoritos_ids)


@cliente_bp.route('/favoritos/toggle/<int:id_producto>', methods=['POST'])
@login_required
def toggle_favorito(id_producto):
    Producto.query.get_or_404(id_producto)
    fav = Favorito.query.filter_by(
        id_usuario=current_user.id, id_producto=id_producto
    ).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash('Eliminado de favoritos 💔', 'info')
    else:
        db.session.add(Favorito(id_usuario=current_user.id, id_producto=id_producto))
        db.session.commit()
        flash('Agregado a favoritos ❤️', 'success')

    return redirect(request.referrer or url_for('cliente.tienda'))
