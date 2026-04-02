from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ========== DATABASE MODELS ==========

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), nullable=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    product = db.relationship('Product')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ========== ADD SAMPLE PRODUCTS ==========

def add_sample_products():
    if Product.query.count() == 0:
        products = [
            {'name': '🎧 Wireless Headphones', 'price': 2999, 'description': 'Noise cancelling, 30hr battery', 'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300', 'stock': 50, 'category': 'Electronics'},
            {'name': '⌚ Smart Watch', 'price': 4999, 'description': 'Fitness tracker, heart rate monitor', 'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300', 'stock': 30, 'category': 'Electronics'},
            {'name': '👟 Running Shoes', 'price': 1999, 'description': 'Lightweight, cushioned sole', 'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300', 'stock': 100, 'category': 'Fashion'},
            {'name': '📱 Smartphone', 'price': 24999, 'description': '5G, 108MP camera, 5000mAh battery', 'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300', 'stock': 25, 'category': 'Electronics'},
            {'name': '💻 Laptop', 'price': 54999, 'description': '16GB RAM, 512GB SSD', 'image_url': 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=300', 'stock': 15, 'category': 'Electronics'},
            {'name': '🎒 Backpack', 'price': 1299, 'description': 'Water resistant, USB charging', 'image_url': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=300', 'stock': 75, 'category': 'Fashion'},
            {'name': '☕ Coffee Maker', 'price': 3499, 'description': 'Automatic, programmable', 'image_url': 'https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=300', 'stock': 40, 'category': 'Home'},
            {'name': '📚 Bestseller Book', 'price': 499, 'description': 'International bestseller', 'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300', 'stock': 200, 'category': 'Books'}
        ]
        for p in products:
            db.session.add(Product(**p))
        db.session.commit()

# ========== ROUTES ==========

@app.route('/')
def index():
    products = Product.query.limit(6).all()
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email exists!', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome {username}!', 'success')
            if user.is_admin:
                return redirect(url_for('admin_panel'))
            return redirect(url_for('index'))
        flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out!', 'info')
    return redirect(url_for('index'))

@app.route('/products')
def products():
    category = request.args.get('category')
    if category:
        product_list = Product.query.filter_by(category=category).all()
    else:
        product_list = Product.query.all()
    
    categories = db.session.query(Product.category).distinct().all()
    return render_template('products.html', products=product_list, categories=categories)

@app.route('/add-to-cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in items)
    return render_template('cart.html', cart_items=items, total=total)

@app.route('/update-cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        qty = int(request.form['quantity'])
        if qty > 0:
            item.quantity = qty
        else:
            db.session.delete(item)
        db.session.commit()
        flash('Cart updated!', 'success')
    return redirect(url_for('cart'))

@app.route('/remove-from-cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed!', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Cart is empty!', 'warning')
        return redirect(url_for('products'))
    
    if request.method == 'POST':
        session['delivery_address'] = f"{request.form['address']}, {request.form['city']}"
        return redirect(url_for('order_success'))
    
    total = sum(item.product.price * item.quantity for item in items)
    return render_template('checkout.html', cart_items=items, total=total)

@app.route('/order-success')
@login_required
def order_success():
    # Clear cart
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    for item in items:
        db.session.delete(item)
    db.session.commit()
    
    delivery_date = (datetime.now() + timedelta(days=3)).strftime('%d %B, %Y')
    return render_template('success.html', delivery_date=delivery_date)

# ========== ADMIN ROUTES ==========

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Admin access only!', 'danger')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    users = User.query.all()
    return render_template('admin.html', products=products, users=users)

@app.route('/admin/add-product', methods=['POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    
    product = Product(
        name=request.form['name'],
        price=float(request.form['price']),
        description=request.form['description'],
        image_url=request.form.get('image_url', ''),
        stock=int(request.form.get('stock', 0)),
        category=request.form.get('category', '')
    )
    db.session.add(product)
    db.session.commit()
    flash('Product added!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-product/<int:product_id>')
@login_required
def delete_product(product_id):
    if not current_user.is_admin:
        flash('Unauthorized!', 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted!', 'success')
    return redirect(url_for('admin_panel'))

# ========== CREATE DATABASE ==========

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@shop.com', password=generate_password_hash('admin123'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
    add_sample_products()

if __name__ == '__main__':
    app.run(debug=True)