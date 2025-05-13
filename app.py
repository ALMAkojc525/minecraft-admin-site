"""
---------------------------------------------------------------------
 Flask aplikacija za upravljanje Minecraft platforme na AWS
 --------------------------------------------------------------------
  • Hkrati urejamo:
      1. MySQL (Aurora) bazo z dvema tabelama:
         - users   : whitelist (username, ime, priimek)
         - admins  : OP-uporabniki (username)
      2. Vse tri Minecraft strežnike, ki tečejo v Docker
         (survival, creative, custom) – do njih dostopamo preko RCON.

  • Ko v UI dodamo/odstranimo userja ali admina:
      – VPIŠEMO / BRIŠEMO zapis v bazi
      – Pošljemo ukaz na VSE 3 serverje:
            whitelist add / remove
            op / deop
  • UI (Flask + Bootstrap) prikaže dve tabeli in omogoča dodajanje/
    brisanje z gumbi; komunikacijo izvaja prek spodnjih view-jev.
---------------------------------------------------------------------
"""

# ----------------------- 1) UVOZI ------------------------------- #
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector          # Klient za MySQL
import subprocess               # Za zaganjanje ukaza mcrcon

# ----------------------- 2) FLASK INIT -------------------------- #
app = Flask(__name__)
app.secret_key = 'zelo-zasebno-geslo'   # Potrebno za flash sporočila / seje

# ----------------------- 3) KONFIGURACIJA ----------------------- #
# ----- MySQL podatki (AWS Aurora) -----
db_conf = {
    'host':     'minecraft2-db.ch6wiqkiysjy.eu-north-1.rds.amazonaws.com',
    'user':     'admin',
    'password': 'Sup3rSecret!',
    'database': 'minecraft_admin'
}

# Funkcija za vzpostavitev nove povezave z bazo
def db_conn():
    """Vsakič odpremo novo povezavo (Flask zahteva je kratkotrajna)."""
    return mysql.connector.connect(**db_conf)

# ----- RCON nastavitve -----
rcon_password = 'SuperRCONpass123'
mcrcon_path   = '/usr/local/bin/mcrcon'   # absolutna pot do binarke

# En sam strežnik (EC2) gosti vse tri containerje → isti IP, različni porti
rcon_targets = [
    {'host': '10.0.2.163', 'port': 25575},   # survival
    {'host': '10.0.2.163', 'port': 25576},   # creative
    {'host': '10.0.2.163', 'port': 25577},   # custom
]

# ----------------------- 4) POMOŽNE FUNKCIJE -------------------- #
# Funkcija za pošiljanje RCON ukaza na vse tri strežnike
def rcon_command(cmd: str) -> None:
    """
    Pošlje ukaz `cmd` na VSE strežnike.
    • STDOUT ignoriramo (pošiljamo v DEVNULL), ker uporabniku ni pomemben.
    • Če pride do napake, subprocess vrže izjemo – ujamemo jo tam,
      kjer to funkcijo kličemo in prikažemo flash.
    """
    for target in rcon_targets:
        subprocess.run(
            [
                mcrcon_path,
                '-H', target['host'],
                '-P', str(target['port']),
                '-p', rcon_password,
                cmd
            ],
            stdout=subprocess.DEVNULL,  
            stderr=subprocess.DEVNULL,
            check=True                   
        )

# ----------------------- 5) ROUTES / VIEW-i --------------------- #
@app.route('/')
def index():
    """
    Glavna nadzorna plošča.
    - preberemo admin & user sezname iz baze
    - posredujemo jih predlogi (index.html)
    """
    with db_conn() as conn:
        cur = conn.cursor(dictionary=True)

        cur.execute('SELECT * FROM admins ORDER BY username')
        admins = cur.fetchall()

        cur.execute('SELECT * FROM users ORDER BY username')
        users = cur.fetchall()

    return render_template('index.html', admins=admins, users=users)

# ---------------------------------------------------------------
#                     U P O R A B N I K I
# ---------------------------------------------------------------
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """
    GET  → prikaži formo.
    POST → zapiši v DB in pošlji whitelist add na vse serverje.
    """
    if request.method == 'POST':
        # ----- 1) preberemo vnos -----
        username = request.form['username']
        name     = request.form['name']
        surname  = request.form['surname']

        try:
            # ----- 2) DB INSERT -----
            with db_conn() as conn:
                cur = conn.cursor()
                cur.execute(
                    'INSERT INTO users (username, name, surname) VALUES (%s, %s, %s)',
                    (username, name, surname)
                )
                conn.commit()

            # ----- 3) RCON (whitelist add) -----
            rcon_command(f'whitelist add {username}')
            flash(f'{username} added to whitelist.', 'success')

        except Exception as e:
            flash(f'Napaka pri dodajanju uporabnika: {e}', 'danger')

        return redirect(url_for('index'))

    # GET
    return render_template('add_user.html')

# Izbriši uporabnika iz baze + odstrani iz whitelist prek RCON
@app.route('/delete_user/<username>')
def delete_user(username):
    """Odstrani userja iz baze + iz whitelist na vseh serverjih."""
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM users WHERE username = %s', (username,))
            conn.commit()

        rcon_command(f'whitelist remove {username}')
        flash(f'{username} removed from whitelist.', 'success')

    except Exception as e:
        flash(f'Napaka pri brisanju uporabnika: {e}', 'danger')

    return redirect(url_for('index'))

# ---------------------------------------------------------------
#                        A D M I N I
# ---------------------------------------------------------------
@app.route('/add_admin', methods=['GET', 'POST'])
def add_admin():
    """Doda OP-uporabnika."""
    if request.method == 'POST':
        username = request.form['username']
        try:
            with db_conn() as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO admins (username) VALUES (%s)', (username,))
                conn.commit()

            rcon_command(f'op {username}')
            flash(f'{username} added as admin (OP).', 'success')

        except Exception as e:
            flash(f'Napaka pri dodajanju admina: {e}', 'danger')

        return redirect(url_for('index'))

    return render_template('add_admin.html')

# Odstrani OP pravice in admina iz baze
@app.route('/delete_admin/<username>')
def delete_admin(username):
    """Odstrani OP pravice in izbriše admina iz baze."""
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM admins WHERE username = %s', (username,))
            conn.commit()

        rcon_command(f'deop {username}')
        flash(f'{username} removed as admin.', 'success')

    except Exception as e:
        flash(f'Napaka pri brisanju admina: {e}', 'danger')

    return redirect(url_for('index'))

# -------------------- 6) ZAGON APP-a --------------------------- #
if __name__ == '__main__':
    # DEBUG način se samodejno reload-a pri spremembah in prikaže tracebacke.
    # V produkciji ga ugasni in uporabi WSGI strežnik (gunicorn/uwsgi).
    app.run(debug=True, host='0.0.0.0')
