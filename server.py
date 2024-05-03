from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Dummy user database (replace with a real database in a production environment)
users = {
    'user1': {
        'username': 'user1',
        'password': 'password1',
        'role': 'Customer'
    },
    'user2': {
        'username': 'user2',
        'password': 'password2',
        'role': 'Agent'
    },
    'user3': {
        'username': 'user3',
        'password': 'password3',
        'role': 'Staff'
    },
    'user4': {
        'username': 'user4',
        'password': 'password4',
        'role': 'Staff'
    }
}

@app.route('/', endpoint='home')
def home():
    return render_template('home.html', msg=[False])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = users[username]['role']
            if session['role'] == 'Staff' and session['username'] == 'user3':
                session['admin'] = True
                session['operator'] = True
            elif session['role'] == 'Staff' and session['username'] == 'user4':
                session['admin'] = False
                session['operator'] = False
            
            print(f"User {username} logged in")
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
        
        if role == "Customer":
            return redirect(url_for('reg_customer', username=username, password=password))
        elif role == "Agent":
            return redirect(url_for('reg_agent', username=username, password=password))
        else:
            return redirect(url_for('reg_staff', username=username, password=password))
    return render_template('register.html')

@app.route('/reg_customer?username=<username>&password=<password>', methods=['GET', 'POST'])
def reg_customer(username, password):
    if username=="customer25":
        return render_template('reg_customer.html', username='', password='', error=[True, "Username already exists"])
    return render_template('reg_customer.html', username=username, password=password, error=False)

@app.route('/reg_agent?username=<username>&password=<password>', methods=['GET', 'POST'])
def reg_agent(username, password):
    return render_template('reg_agent.html', username=username, password=password)

@app.route('/reg_staff?username=<username>&password=<password>', methods=['GET', 'POST'])
def reg_staff(username, password):
    return render_template('reg_staff.html', username=username, password=password)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    print("search_flights")
    if request.method == 'POST' and request.form.get("Search"):
        departure_airport = request.form['departure_airport']
        departure_city = request.form['departure_city']
        arrival_airport = request.form['arrival_airport']
        arrival_city = request.form['arrival_city']
        departure_date_from = request.form['departure_date_from']
        departure_date_to = request.form['departure_date_to']
        print(f"Searching for flights from {departure_airport} to {arrival_airport} from {departure_date_from} to {departure_date_to}")
        return render_template('search_flights.html', error=[False])
    
    if request.method == 'POST' and request.form.get("Book"):
        if session['role'] == 'Customer':
            flight_number = request.form['flight_number']
            msg = f"Customer {session['username']} booked flight {flight_number}"
            print(f"Customer {session['username']} booked flight {flight_number}")
        else:
            flight_number = request.form['flight_number']
            customer_email = request.form['customer_email']
            msg = f"Agent {session['username']} booked flight {flight_number} for customer {customer_email}"
            print(f"Agent {session['username']} booked flight {flight_number} for customer {customer_email}")
        return render_template('search_flights.html', error=[True, msg])

    return render_template('search_flights.html', error=[False])

@app.route('/book_flights', methods=['GET', 'POST'])
def book_flights():
    if request.method == 'POST':
        if session['role'] == 'Customer':
            flight_number = request.form['flight_number']
            print(f"Customer {session['username']} booked flight {flight_number}")
        else:
            flight_number = request.form['flight_number']
            customer_email = request.form['customer_email']
            print(f"Agent {session['username']} booked flight {flight_number} for customer {customer_email}")
    return render_template('search_flights.html')

@app.route('/view_my_flights', methods=['GET', 'POST'])
def view_my_flights(): 
    return render_template('view_my_flights.html')

# @app.route('/buy_tickets', methods=['GET', 'POST'])
# def buy_tickets():
#     return 

@app.route('/track_spendings', methods=['GET', 'POST'])
def track_spendings():
    img_url = url_for('static', filename='img0.jpg')
    return render_template('track_spendings.html', filename=img_url)

@app.route('/view_commission', methods=['GET', 'POST'])
def view_commission():
    ttl_commission = 0
    ttl_tickets = 0
    if ttl_tickets == 0:
        avg_commission = 0
    else:
        avg_commission  = ttl_commission/ttl_tickets
    if request.method == 'POST':
        from_date = request.form['departure_date_from']
        to_date = request.form['departure_date_to']
        ttl_commission = 0
        ttl_tickets = 0
        if ttl_tickets == 0:
            avg_commission = 0
        else:
            avg_commission  = ttl_commission/ttl_tickets

        return render_template('view_commission.html', start_date=from_date, end_date=to_date, ttl_commission=ttl_commission, ttl_tickets=ttl_tickets, avg_commission=avg_commission)
    return render_template('view_commission.html', start_date=None, end_date=None, ttl_commission=ttl_commission, ttl_tickets=ttl_tickets, avg_commission=avg_commission)

@app.route('/view_top_customers', methods=['GET', 'POST'])
def view_top_customers():
    img_url = url_for('static', filename='img0.jpg')

    if request.method == 'POST':
        from_date = request.form['departure_date_from']
        to_date = request.form['departure_date_to']
        img_url = url_for('static', filename='img0.jpg')
        return render_template('view_top_customers.html', start_date=from_date, end_date=to_date, filename=img_url)
    
    return render_template('view_top_customers.html', start_date=None, end_date=None, filename=img_url)

@app.route('/manage_flights', methods=['GET', 'POST'])
def manage_flights():
    return

@app.route('/create_new_flights', methods=['GET', 'POST'])
def create_new_flights():
    if session["admin"] == False:
        return redirect(url_for('home'))
    if request.method == 'POST':
        departure_airport = request.form['departure_airport']
        arrival_airport = request.form['arrival_airport']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        price = request.form['price']
        airplane_id = request.form['Airplane_id']
        print(f"New flight created from {departure_airport} to {arrival_airport} at {departure_time} to {arrival_time} for ${price} with airplane {airplane_id}")
        return render_template('create_new_flights.html', msg=[True, f"New flight created from {departure_airport} to {arrival_airport} at {departure_time} to {arrival_time} for ${price} with airplane {airplane_id}"])
    return render_template('create_new_flights.html', msg=[False])

@app.route('/change_status', methods=['GET', 'POST'])
def change_status():
    if session["operator"] == False and session["admin"] == False:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        flight_id = request.form['flight_id']
        new_departure_time = request.form['new_departure_time'] 
        new_arrival_time = request.form['new_arrival_time']

        print(f"Flight {flight_id} departure time changed to {new_departure_time} and arrival time changed to {new_arrival_time} by {session['username']}")
    return render_template('change_status.html')

@app.route('/add_new_plane', methods=['GET', 'POST'])
def add_new_plane():
    if session["admin"] == False:
        return redirect(url_for('home'))
    if request.method == 'POST':
        seat_count = request.form['seats']
        print(f"New plane added with {seat_count} seats by {session['username']}")
        return render_template('add_new_plane.html', msg=[True, f"New plane added with {seat_count} seats"])
    return render_template('add_new_plane.html', msg=[False])

@app.route('/add_new_airport', methods=['GET', 'POST'])
def add_new_airport():
    if session["admin"] == False:
        return redirect(url_for('home'))
    if request.method == 'POST':
        airport_name = request.form['airport_name']
        city = request.form['airport_city']
        print(f"New airport added with name {airport_name} in {city} by {session['username']}")
        return render_template('add_new_airport.html', msg=[True, f"New airport added with name {airport_name} in {city}"])
    return render_template('add_new_airport.html', msg=[False])

@app.route('/add_new_agent', methods=['GET', 'POST'])
def add_new_agent():
    return

@app.route('/manage_agents', methods=['GET', 'POST'])
def manage_agents():
    if request.method == 'POST' and request.form.get("Search"):
        date_from = request.form['from_date']
        date_to = request.form['date_to']
        print(f"Searching for agents from {date_from} to {date_to}")
        return render_template('manage_agents.html', msg=[True, f"Searching for agents from {date_from} to {date_to}"])  
    if request.method == 'POST' and request.form.get("Add"):
        email = request.form['email']
        print(f"Agent {email} added by {session['username']}")
        return render_template('manage_agents.html', msg=[True, f"Agent {email} added by {session['username']}"])      
    return render_template('manage_agents.html', msg=[False])

@app.route('/view_frequent_customers', methods=['GET', 'POST'])
def view_frequent_customers():
    if request.method == 'POST' and request.form.get("Search"):
        date_from = request.form['from_date']
        date_to = request.form['date_to']
        print(f"Searching for customers from {date_from} to {date_to}")
        return render_template('view_frequent_customers.html', msg=[True, f"Searching for agents from {date_from} to {date_to}"])
    return render_template('view_frequent_customers.html', msg=[False]) 

@app.route('/view_reports', methods=['GET', 'POST'])
def view_reports():
    img_url = url_for('static', filename='img0.jpg')
    if request.method == 'POST' and request.form.get("Search"):
        date_from = request.form['from_date']
        date_to = request.form['date_to']
        print(f"Searching for customers from {date_from} to {date_to}")
        return render_template('view_frequent_customers.html', msg=[True, f"Searching for agents from {date_from} to {date_to}"], 
                               filename=img_url)
    return render_template('view_reports.html', msg=[False], filename=img_url)

@app.route('/manage_staff', methods=['GET', 'POST'])
def manage_staff():
    if request.method == "POST":
        username = request.form['username']
        premission = request.form['permission']
        print(f"User {username} has been granted {premission} by {session['username']}")
        return render_template('manage_staff.html', msg=[True, f"User {username} has been granted {premission} by {session['username']}"])
    return render_template('manage_staff.html', msg=[False])

@app.route('/upload/<filename>')
def send_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(debug=True)

