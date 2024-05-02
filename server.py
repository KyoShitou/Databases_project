from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Dummy user database (replace with a real database in a production environment)
users = {
    'user1': {
        'username': 'user1',
        'password': 'password1'
    },
    'user2': {
        'username': 'user2',
        'password': 'password2'
    }
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if username in users:
            return 'Username already exists'
        users[username] = {'username': username, 'password': password}
        if role == "Customer":
            return redirect(url_for('reg_customer'))
        elif role == "Agent":
            return redirect(url_for('reg_agent'))
        else:
            return redirect(url_for('reg_staff'))
    return render_template('register.html')

@app.route('/reg_customer', methods=['GET', 'POST'])
def reg_customer():
    return render_template('reg_customer.html')

@app.route('/reg_agent', methods=['GET', 'POST'])
def reg_agent():
    return render_template('reg_agent.html')

@app.route('/reg_staff', methods=['GET', 'POST'])
def reg_staff():
    return render_template('reg_staff.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

