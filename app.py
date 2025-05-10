from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import subprocess

app = Flask(__name__)
app.secret_key = 'zelo-zasebno-geslo'

# Konfiguracija baze
config = {
    'host': 'minecraft2-db.ch6wiqkiysjy.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Sup3rSecret!',
    'database': 'minecraft_admin'
}

def get_db_connection():
    return mysql.connector.connect(**config)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', users=users)

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

            subprocess.run([
                './mcrcon/mcrcon', '-H', '10.0.2.163', '-P', '25575', '-p', 'SuperRCONpass123', f'whitelist add {username}'
            ], check=True)
            flash(f'Uporabnik {username} dodan in whitelist posodobljen.', 'success')
        except Exception as e:
            flash(f'Napaka pri dodajanju: {str(e)}', 'danger')

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

        subprocess.run([
            './mcrcon/mcrcon', '-H', '10.0.2.163', '-P', '25575', '-p', 'SuperRCONpass123', f'whitelist remove {username}'
        ], check=True)
        flash(f'Uporabnik {username} odstranjen iz baze in whitelist.', 'success')
    except Exception as e:
        flash(f'Napaka pri brisanju: {str(e)}', 'danger')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
