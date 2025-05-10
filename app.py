from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import subprocess

app = Flask(__name__)

DB_CONFIG = {
    'host': 'minecraft2-db.ch6wiqkiysjy.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Sup3rSecret!',
    'database': 'minecraft_admin'
}

RCON_SERVERS = [
    {"host": "10.0.2.163", "port": "25575"},
    {"host": "10.0.2.163", "port": "25576"},
    {"host": "10.0.2.163", "port": "25577"},
]
RCON_PASSWORD = "SuperRCONpass123"
RCON_BINARY = "/home/ubuntu/mcrcon/mcrcon"

def send_rcon_command(command):
    for server in RCON_SERVERS:
        try:
            subprocess.run([
                RCON_BINARY,
                "-H", server["host"],
                "-P", server["port"],
                "-p", RCON_PASSWORD,
                command
            ], check=True)
        except subprocess.CalledProcessError:
            print(f"Napaka pri pošiljanju RCON na {server['host']}:{server['port']}")

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('index.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        surname = request.form['surname']
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, name, surname) VALUES (%s, %s, %s)",
            (username, name, surname)
        )
        conn.commit()
        conn.close()
        send_rcon_command(f"whitelist add {username}")
        return redirect(url_for('index'))
    return render_template('add_user.html')

@app.route('/delete_user/<username>')
def delete_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    conn.close()
    send_rcon_command(f"whitelist remove {username}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
