from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import subprocess

app = Flask(__name__)
app.secret_key = 'zelo-zasebno-geslo'

# DB konfiguracija
config = {
    'host': 'minecraft2-db.ch6wiqkiysjy.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Sup3rSecret!',
    'database': 'minecraft_admin'
}

# RCON nastavitve
RCON_HOST = '10.0.2.163'
RCON_PORTS = [25575, 25576, 25577]
RCON_PASSWORD = 'SuperRCONpass123'
RCON_PATH = '/home/ubuntu/mcrcon/mcrcon'  # prilagodi če potrebuješ

def get_db_connection():
    return mysql.connector.connect(**config)

def execute_rcon(command):
    errors = []
    for port in RCON_PORTS:
        try:
            subprocess.run([
                RCON_PATH, '-H', RCON_HOST, '-P', str(port), '-p', RCON_PASSWORD, command
            ], check=True)
        except Exception as e:
            errors.append(f'Port {port} error: {str(e)}')
    return errors

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

            errors = execute_rcon(f'whitelist add {username}')
            if errors:
                flash('Partial whitelist success:\n' + '\n'.join(errors), 'warning')
            else:
                flash(f'User {username} added and whitelisted.', 'success')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
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

        errors = execute_rcon(f'whitelist remove {username}')
        if errors:
            flash('Partial de-whitelist success:\n' + '\n'.join(errors), 'warning')
        else:
            flash(f'User {username} removed.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/add_admin', methods=['POST'])
def add_admin():
    username = request.form['admin_username']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO admins (username) VALUES (%s)', (username,))
        conn.commit()
        cursor.close()
        conn.close()

        errors = execute_rcon(f'op {username}')
        if errors:
            flash('Partial op success:\n' + '\n'.join(errors), 'warning')
        else:
            flash(f'Admin {username} added and opped.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/delete_admin/<username>')
def delete_admin(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE username = %s', (username,))
        conn.commit()
        cursor.close()
        conn.close()

        errors = execute_rcon(f'deop {username}')
        if errors:
            flash('Partial deop success:\n' + '\n'.join(errors), 'warning')
        else:
            flash(f'Admin {username} deopped and removed.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
