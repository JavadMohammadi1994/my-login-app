from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import bcrypt
import os

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_change_in_production_123456'

# ←←← اول تابع init_db تعریف می‌شه ←←←
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ←←← حالا دیتابیس رو در شروع برنامه می‌سازیم ←←←
with app.app_context():
    init_db()

# تنظیمات Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'لطفاً ابتدا وارد شوید.'
login_manager.login_message_category = 'info'

# مدل کاربر
class User(UserMixin):
    def __init__(self, id, username, name):
        self.id = id
        self.username = username
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, username, name FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(row[0], row[1], row[2])
    return None

# روت‌ها
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    return render_template('home.html', name=current_user.name or current_user.username)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        name = request.form.get('name', '').strip()

        if not username or not password:
            flash('نام کاربری و رمز عبور اجباری است!', 'danger')
            return render_template('register.html')

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
                      (username, hashed, name))
            conn.commit()
            flash('ثبت‌نام با موفقیت انجام شد! حالا وارد شو.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('این نام کاربری قبلاً استفاده شده!', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password, name FROM users WHERE username = ?", (username,))
        user_row = c.fetchone()
        conn.close()

        if user_row and bcrypt.checkpw(password.encode('utf-8'), user_row[2]):
            user = User(user_row[0], user_row[1], user_row[3])
            login_user(user)
            flash(f'خوش آمدی {user.name or username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است!', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('با موفقیت خارج شدی.', 'info')
    return redirect(url_for('login'))

# فقط برای اجرای محلی (در Render لازم نیست)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)