from flask import Flask, render_template, request, redirect, url_for
import uuid

app = Flask(__name__)

# Seznam uporabnikov s strukturiranimi slovarji
users = []

@app.route('/')
def index():
    return render_template('index.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        surname = request.form['surname']
        users.append({
            'id': str(uuid.uuid4()),
            'username': username,
            'name': name,
            'surname': surname
        })
        return redirect(url_for('index'))
    return render_template('add_user.html')

@app.route('/delete_user/<id>')
def delete_user(id):
    global users
    users = [user for user in users if user['id'] != id]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
