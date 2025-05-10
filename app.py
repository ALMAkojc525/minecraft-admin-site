from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import subprocess

app = Flask(__name__)
app.secret_key = 'zelo-zasebno-geslo'

config = {
    'host': 'minecraft2-db.ch6wiqkiysjy.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Sup3rSecret!',
    'database': 'minecraft_admin'
}

rcon_targets = [
    {'host': '10.0.2.163', 'port': 25575},
    {'host': '10.0.2.163', 'port': 25576},
    {'host': '10.0.2.163', 'port': 25577},
]
rcon_password = 'SuperRCONpass123'
mcrcon_path = '/usr/local/bin/mcrcon'

def get_db_connection():
    return mysql.connector.connect(**config)

def rcon_command(command):
    for target in rcon_targets:
        subprocess.run([
            mcrcon_path,
            '-H', target['host'],
            '-P', str(target['port']),
            '-p', rcon_password,
            command
        ], stdout=subprocess.DEVNULL)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.execute('SELECT * FROM admins')
    admins = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', users=users, admins=admins)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        surname = request.form['surname']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, name, surname) VALUES (%s, %s, %s)', (username, name, surname))
            conn.commit()
            cursor.close()
            conn.close()
            rcon_command(f'whitelist add {username}')
            flash(f'{username} added to whitelist.', 'success')
        except Exception as e:
            flash(f'Error adding user: {e}', 'danger')
        return redirect(url_for('index'))
    return render_template('add_user.html')

@app.route('/delete_user/<username>')
def delete_user(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username = %s', (username,))
        conn.commit()
        cursor.close()
        conn.close()
        rcon_command(f'whitelist remove {username}')
        flash(f'{username} removed from whitelist.', 'success')
    except Exception as e:
        flash(f'Error removing user: {e}', 'danger')
    return redirect(url_for('index'))

@app.route('/add_admin', methods=['GET', 'POST'])
def add_admin():
    if request.method == 'POST':
        username = request.form['username']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO admins (username) VALUES (%s)', (username,))
            conn.commit()
            cursor.close()
            conn.close()
            rcon_command(f'op {username}')
            flash(f'{username} added as admin.', 'success')
        except Exception as e:
            flash(f'Error adding admin: {e}', 'danger')
        return redirect(url_for('index'))
    return render_template('add_admin.html')

@app.route('/delete_admin/<username>')
def delete_admin(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE username = %s', (username,))
        conn.commit()
        cursor.close()
        conn.close()
        rcon_command(f'deop {username}')
        flash(f'{username} removed as admin.', 'success')
    except Exception as e:
        flash(f'Error removing admin: {e}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
