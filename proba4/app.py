from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Создание базы данных
def create_db():
    conn = sqlite3.connect('repair_requests.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS repair_requests
                 (id INTEGER PRIMARY KEY, date_added TEXT, appliance_type TEXT, 
                 appliance_model TEXT, issue_description TEXT, client_name TEXT, 
                 phone_number TEXT, status TEXT)''')
    conn.commit()
    conn.close()


# Маршрут для главной страницы
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('repair_requests.db')
    c = conn.cursor()
    c.execute('SELECT * FROM repair_requests')
    requests = c.fetchall()
    conn.close()
    return render_template('index.html', requests=requests)


# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = sqlite3.connect('repair_requests.db')
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO users (username, password) VALUES (?, ?)''',
                      (username, hashed_password))
            conn.commit()
            flash('Регистрация прошла успешно, теперь вы можете войти', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Имя пользователя уже занято', 'error')
        conn.close()
    return render_template('register.html')


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('repair_requests.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['username'] = username
            flash('Вы вошли в систему', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неправильное имя пользователя или пароль', 'error')

    return render_template('login.html')


# Выход
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('login'))


# Добавление заявки
@app.route('/add_request', methods=['GET', 'POST'])
def add_request():
    if request.method == 'POST':
        date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        appliance_type = request.form['appliance_type']
        appliance_model = request.form['appliance_model']
        issue_description = request.form['issue_description']
        client_name = request.form['client_name']
        phone_number = request.form['phone_number']
        status = 'новая заявка'

        conn = sqlite3.connect('repair_requests.db')
        c = conn.cursor()
        c.execute('''INSERT INTO repair_requests (date_added, appliance_type, 
                     appliance_model, issue_description, client_name, phone_number, status) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''', (date_added, appliance_type,
                                                       appliance_model, issue_description, client_name, phone_number,
                                                       status))
        conn.commit()
        conn.close()
        flash('Заявка успешно добавлена', 'success')
        return redirect(url_for('index'))

    return render_template('add_request.html')


# Редактирование заявки
@app.route('/edit_request/<int:request_id>', methods=['GET', 'POST'])
def edit_request(request_id):
    if request.method == 'POST':
        status = request.form['status']
        issue_description = request.form['issue_description']

        conn = sqlite3.connect('repair_requests.db')
        c = conn.cursor()
        c.execute('''UPDATE repair_requests SET status=?, issue_description=? WHERE id=?''',
                  (status, issue_description, request_id))
        conn.commit()
        conn.close()
        flash('Заявка успешно отредактирована', 'success')
        return redirect(url_for('index'))
    else:
        conn = sqlite3.connect('repair_requests.db')
        c = conn.cursor()
        c.execute('SELECT * FROM repair_requests WHERE id=?', (request_id,))
        request_data = c.fetchone()
        conn.close()
        return render_template('edit_request.html', request_data=request_data)


# Отслеживание статуса заявок
@app.route('/track_status')
def track_status():
    conn = sqlite3.connect('repair_requests.db')
    c = conn.cursor()
    c.execute('SELECT * FROM repair_requests')
    requests = c.fetchall()
    conn.close()
    return render_template('track_status.html', requests=requests)


# Обработчик для поиска заявок
@app.route('/search', methods=['GET'])
def search_request():
    request_id = request.args.get('request_id')
    if request_id:
        conn = sqlite3.connect('repair_requests.db')
        c = conn.cursor()
        c.execute('SELECT * FROM repair_requests WHERE id=?', (request_id,))
        request_data = c.fetchone()
        conn.close()
        if request_data:
            return render_template('search_result.html', request_data=request_data)
        else:
            flash('Заявка с таким номером не найдена', 'error')
            return redirect(url_for('index'))
    else:
        flash('Введите номер заявки для поиска', 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    create_db()
    app.run(debug=True, port=5001)  # Используем порт 5001 вместо 5000
