from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

# สร้าง Flask Application
app = Flask(__name__)

# ตั้งค่าครับ
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'football-shop-secret-key-2026'  # สำหรับ session

# สร้าง Database Instance
db = SQLAlchemy(app)

# ===== Models (ตาราง Database) =====
class Product(db.Model):
    """Model สำหรับตาราง Product"""
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(80), nullable=False, default='อุปกรณ์เสริมฟุตบอล')
    
    def to_dict(self):
        """แปลง Product object เป็น dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'image_url': self.image_url,
            'category': self.category
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'


# ===== Routes =====
@app.route('/')
def index():
    """หน้าแรก - ดึงข้อมูล Product จาก Database พร้อมตัวกรองหมวดหมู่"""
    category = request.args.get('category')
    if category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()
    # ส่ง list ของหมวดหมู่ที่ใช้งานให้ template แสดงเป็นเมนู
    categories = ['ลูกฟุตบอล', 'รองเท้าฟุตบอล', 'อุปกรณ์เสริมฟุตบอล']
    return render_template('index.html', products=products, categories=categories, selected_category=category)


@app.route('/cart')
def cart():
    """หน้าตะกร้าสินค้า"""
    return render_template('cart.html')


@app.route('/api/products', methods=['GET'])
def get_products():
    """API สำหรับดึงข้อมูล Product ทั้งหมด หรือกรองด้วย category"""
    category = request.args.get('category')
    if category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()
    return jsonify([product.to_dict() for product in products])


@app.route('/api/products', methods=['POST'])
def create_product():
    """API สำหรับสร้าง Product ใหม่"""
    try:
        data = request.get_json()
        
        # สร้าง Product object ใหม่
        new_product = Product(
            name=data.get('name'),
            price=data.get('price'),
            image_url=data.get('image_url'),
            category=data.get('category', 'อุปกรณ์เสริมฟุตบอล')
        )
        
        # เพิ่มลงใน Database
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product สร้างสำเร็จ',
            'product': new_product.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """API สำหรับดึงข้อมูล Product หนึ่งชิ้น"""
    product = Product.query.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product ไม่พบ'}), 404
    
    return jsonify(product.to_dict())


@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """API สำหรับแก้ไข Product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product ไม่พบ'}), 404
        
        data = request.get_json()
        
        # อัปเดตข้อมูล
        if 'name' in data:
            product.name = data['name']
        if 'price' in data:
            product.price = data['price']
        if 'image_url' in data:
            product.image_url = data['image_url']
        if 'category' in data:
            product.category = data['category']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product อัปเดตสำเร็จ',
            'product': product.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """API สำหรับลบ Product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product ไม่พบ'}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Product ลบสำเร็จ'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# ===== Admin Routes =====
def is_admin_logged_in():
    """ตรวจสอบว่า Admin ล้อกอินแล้วหรือไม่"""
    return session.get('admin_logged_in', False)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """หน้า Login สำหรับ Admin"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # ตรวจสอบข้อมูล
        if username == 'admin' and password == '1234':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='ชื่อผู้ใช้ หรือ รหัสผ่านไม่ถูกต้อง')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """ออกจากระบบ Admin"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin/dashboard')
def dashboard():
    """แดชบอร์ด Admin - แสดงรายการสินค้าทั้งหมด"""
    if not is_admin_logged_in():
        return redirect(url_for('login'))
    
    products = Product.query.all()
    return render_template('admin.html', products=products, username=session.get('admin_username'))


@app.route('/admin/add-product', methods=['GET', 'POST'])
def add_product_admin():
    """เพิ่มสินค้าใหม่จาก Admin"""
    if not is_admin_logged_in():
        return redirect(url_for('login'))
    
    categories = ['ลูกฟุตบอล', 'รองเท้าฟุตบอล', 'อุปกรณ์เสริมฟุตบอล']
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            price = request.form.get('price')
            image_url = request.form.get('image_url')
            category = request.form.get('category')
            
            # ตรวจสอบข้อมูล
            if not name or not price or not image_url or not category:
                return render_template('admin-add-product.html', 
                                     error='กรุณากรอกข้อมูลให้ครบ', categories=categories)
            
            # สร้าง Product object ใหม่
            new_product = Product(
                name=name,
                price=float(price),
                image_url=image_url,
                category=category
            )
            
            # บันทึกลง Database
            db.session.add(new_product)
            db.session.commit()
            
            return redirect(url_for('dashboard'))
        
        except ValueError:
            return render_template('admin-add-product.html', 
                                 error='ราคาต้องเป็นตัวเลข', categories=categories)
        except Exception as e:
            db.session.rollback()
            return render_template('admin-add-product.html', 
                                 error=f'เกิดข้อผิดพลาด: {str(e)}', categories=categories)
    
    return render_template('admin-add-product.html', categories=categories)


@app.route('/admin/delete-product/<int:product_id>', methods=['POST'])
def delete_product_admin(product_id):
    """ลบสินค้า จาก Admin"""
    if not is_admin_logged_in():
        return redirect(url_for('login'))
    
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return redirect(url_for('dashboard'))
        
        db.session.delete(product)
        db.session.commit()
    
    except Exception as e:
        db.session.rollback()
    
    return redirect(url_for('dashboard'))


# ===== Seed Sample Data =====
def seed_sample_data():
    """เพิ่มข้อมูลตัวอย่างลงใน Database ถ้าเป็นครั้งแรก"""
    with app.app_context():
        # ตรวจสอบถ้ามีข้อมูลอยู่แล้วให้ข้าม
        if Product.query.count() > 0:
            print("✅ Database already has products. Skipping sample data insertion.")
            return
        
        # ข้อมูลตัวอย่าง 4 ชิ้น (Football theme)
        sample_products = [
            Product(
                name="รองเท้าสตั๊ด Nike Mercurial",
                price=2990.00,
                image_url="https://images.unsplash.com/photo-1598643231624-2756a5c50916?w=400&h=250&fit=crop",
                category="รองเท้าฟุตบอล"
            ),
            Product(
                name="ลูกฟุตบอล Adidas Team Match",
                price=1290.00,
                image_url="https://images.unsplash.com/photo-1589548429479-5b3ea970fc9d?w=400&h=250&fit=crop",
                category="ลูกฟุตบอล"
            ),
            Product(
                name="เสื้อทีมฟุตบอล Replica",
                price=890.00,
                image_url="https://images.unsplash.com/photo-1580822183875-bc0d4142852c?w=400&h=250&fit=crop",
                category="อุปกรณ์เสริมฟุตบอล"
            ),
            Product(
                name="สนับเข่าสำหรับฟุตบอล",
                price=190.00,
                image_url="https://images.unsplash.com/photo-1627147030848-f7934b29f444?w=400&h=250&fit=crop",
                category="อุปกรณ์เสริมฟุตบอล"
            )
        ]
        
        try:
            # เพิ่มสินค้าไปยัง Database
            db.session.add_all(sample_products)
            db.session.commit()
            
            print("Sample products inserted successfully!")
            print(f"Added {len(sample_products)} products to database:")
            for product in sample_products:
                print(f"   - {product.name} (฿{product.price:.2f})")
        
        except Exception as e:
            db.session.rollback()
            print(f"Error inserting sample data: {str(e)}")


# ===== Initialize Database =====
def init_db():
    """สร้าง Database และตาราง ถ้ายังไม่มี
    นอกจากนี้จะพยายามเพิ่มคอลัมน์ `category` ถ้ายังไม่มี (สำหรับฐานข้อมูลเก่า)
    """
    with app.app_context():
        # สร้างตารางใหม่ (ถ้ายังไม่มี)
        db.create_all()
        print("Database initialized successfully!")
        print(f"Database file created: {os.path.abspath('shop.db')}")

        # สำหรับ SQLite ให้เพิ่มคอลัมน์ category ถ้ายังไม่มี
        try:
            with db.engine.connect() as conn:
                conn.execute("ALTER TABLE product ADD COLUMN category TEXT NOT NULL DEFAULT 'อุปกรณ์เสริมฟุตบอล'")
                print("✅ Added 'category' column to existing product table")
        except Exception:
            # ถ้าเกิดข้อผิดพลาด (เช่นคอลัมน์มีอยู่แล้ว) ให้ข้าม
            pass
        
        # เพิ่มข้อมูลตัวอย่างถ้า Database ว่างเปล่า
        seed_sample_data()


if __name__ == '__main__':
    # สร้าง Database เมื่อรันครั้งแรก
    init_db()
    
    # รัน Flask Development Server
    print("\n🚀 Starting Football Shop Server...")
    print("📍 http://localhost:5000")
    print("💡 Press CTRL+C to stop the server\n")
    
    app.run(debug=True, host='localhost', port=5000)
