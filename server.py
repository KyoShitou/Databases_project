from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from datetime import datetime
import pymysql.cursors
import utils
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

conn = pymysql.connect(host="localhost", user="root", password="", db="Airplane_Management", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)


@app.route('/', endpoint='home')
def home():
    return render_template('home.html', msg=[False])

@app.route('/login', methods=['GET', 'POST'])

def login():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM Customer WHERE email='{username}' AND password='{password}'")
        result = cursor.fetchone()
        if result:
            session['logged_in'] = True
            session['username'] = result['name']
            session['role'] = 'Customer'
            session['email'] = username
            print(f"Customer {username} logged in")
            cursor.close()
            return redirect(url_for('home'))
        else:
            cursor.execute(f"SELECT * FROM BookingAgent WHERE email='{username}' AND password='{password}'")
            result = cursor.fetchone()
            if result:
                session['logged_in'] = True
                session['username'] = result['username']
                session['role'] = 'Agent'
                session['email'] = username
                print(f"Agent {username} logged in")
                cursor.close()
                return redirect(url_for('home'))
            else:
                cursor.execute(f"SELECT * FROM AirlineStaff WHERE email='{username}' AND password='{password}'")
                result = cursor.fetchone()
                if result:
                    session['logged_in'] = True
                    session['username'] = result['aStaff_username']
                    session['role'] = 'Staff'
                    session['email'] = username
                    session['airline'] = result['IATA_code']
                    if result['Admin_perm'] == 1:
                        session['admin'] = True
                    else:
                        session['admin'] = False
                    
                    if result['Oper_perm'] == 1:
                        session['operator'] = True
                    else:
                        session['operator'] = False
                    cursor.close()
                    print(f"Staff {username} ({session['admin']}, {session['operator']})logged in")
                    return redirect(url_for('home'))
                else:
                    cursor.close()
                    print(f"Invalid username or password, {username}, {password}")
                    return render_template('login.html', msg=[True, "Invalid username or password"])
    return render_template('login.html', msg=[False])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        cursor = conn.cursor()
        
        if role == "Customer":
            cursor.execute(f"SELECT * FROM Customer WHERE email='{username}'")
            result = cursor.fetchone()
            if result:
                cursor.close()
                return render_template('register.html', msg=[True, "Username already exists"])
            else:
                cursor.close()
                print(url_for('reg_customer', email=username, password=password))
                return redirect(url_for('reg_customer', email=username, password=password))
        elif role == "Agent":
            cursor.execute(f"SELECT * FROM BookingAgent WHERE email='{username}'")
            result = cursor.fetchone()
            if result:
                cursor.close()
                return render_template('register.html', msg=[True, "Username already exists"])
            else:
                cursor.close()
                return redirect(url_for('reg_agent', email=username, password=password))
        else:
            cursor.execute(f"SELECT * FROM AirlineStaff WHERE email='{username}'")
            result = cursor.fetchone()
            if result:
                cursor.close()
                return render_template('register.html', msg=[True, "Username already exists"])
            else:
                cursor.close()
            return redirect(url_for('reg_staff', email=username, password=password))
    return render_template('register.html', msg=[False])

@app.route('/reg_customer?email=<email>&password=<password>', methods=['GET', 'POST'])
def reg_customer(email, password):
    if request.method == "POST":
        name = request.form["name"]
        address = request.form["address"]
        city = request.form["city"]
        state = request.form["state"]
        phone = request.form["cellphone"]
        passport_number = request.form["passport"]
        passport_expiration = request.form["expiry"]
        passport_country = request.form["passport_country"]
        dob = request.form["dob"]

        today = datetime.now().date()

        if datetime.strptime(passport_expiration, "%Y-%m-%d").date() < today:
            return render_template('reg_customer.html', email=email, password=password, error=[True, "Passport has expired"])

        if datetime.strptime(dob, "%Y-%m-%d").date() > today:
            return render_template('reg_customer.html', email=email, password=password, error=[True, "Invalid date of birth"])
        
        cursor = conn.cursor()
        cursor.execute(f"""INSERT INTO Customer VALUES (
                       "{email}", "{name}", "{password}", "{address}", "{city}", "{state}"
                       , "{phone}", "{passport_number}", "{passport_expiration}", "{passport_country}", "{dob}")
                       """)
        conn.commit()
        cursor.close()
        print(f"Customer {email} registered")
        session['logged_in'] = True
        session['username'] = name
        session['email'] = email
        session['role'] = 'Customer'
        return redirect(url_for('home'))
        # Continue with the registration process
    return render_template('reg_customer.html', email=email, password=password, error=[False])

@app.route('/reg_agent?email=<email>&password=<password>', methods=['GET', 'POST'])
def reg_agent(email, password):
    airlines = utils.retrieve_airlines(conn)
    workfor = []
    if request.method == "POST":
        username = request.form['username']
        cursor = conn.cursor()
        for airline in airlines:
            try:
                print(f"Tried {airline['IATA_code']}")
                request.form[airline['IATA_code']]
                workfor.append(airline)
            except:
                print(f"Failed {airline['IATA_code']}")
                continue

        print(workfor)
        cursor.execute(f"INSERT INTO BookingAgent (email, password, username) VALUES ('{email}', '{password}', '{username}')")

        for airline in workfor:
            cursor.execute(f"INSERT INTO Agent_work_for VALUES ('{email}', '{airline['IATA_code']}')")
        conn.commit()
        cursor.close()

        print(f"Agent {email} registered")
        session['logged_in'] = True
        session['email'] = email
        session['username'] = username
        session['role'] = 'Agent'
        return redirect(url_for('home'))
        
    return render_template('reg_agent.html', email=email, password=password, airlines=airlines)

@app.route('/reg_staff?email=<email>&password=<password>', methods=['GET', 'POST'])
def reg_staff(email, password):
    airlines = utils.retrieve_airlines(conn)
    if request.method == "POST":
        print(request.form)
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date_of_birth = request.form['dob']
        admin_perm = request.form['admin_permission']
        oper_perm = request.form['oper_permission']
        airline = request.form['company']

        cursor = conn.cursor()
        cursor.execute(f"""INSERT INTO AirlineStaff VALUES (
                       "{username}", "{email}", "{password}", "{first_name}", "{last_name}", "{date_of_birth}",
                          "{admin_perm}", "{oper_perm}", "{airline}") """)
        conn.commit()
        cursor.close()

        session['logged_in'] = True
        session['email'] = email
        session['username'] = username
        session['role'] = 'Staff'
        session['airline'] = airline
        session['admin'] = False
        session['operator'] = False
        if admin_perm == "1":
            session['admin'] = True
        if oper_perm == "1":
            session['operator'] = True

        return redirect(url_for('home'))
    return render_template('reg_staff.html', email=email, password=password, airlines=airlines)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('email', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('home'))

@app.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    airport_city_dict, airport_lst, city_lst = utils.retrieve_airports_and_city(conn)
    flights = utils.retrieve_flights(conn)
    print(flights)
    if request.method == 'POST' and request.form.get("Search"):
        departure_airport = request.form['departure_airport']
        departure_city = request.form['departure_city']
        arrival_airport = request.form['arrival_airport']
        arrival_city = request.form['arrival_city']
        departure_date_from = request.form['departure_date_from']
        departure_date_to = request.form['departure_date_to']
        print(f"Searching for flights from {departure_airport} to {arrival_airport} from {departure_date_from} to {departure_date_to}")
        flights = utils.retrieve_flights(conn, dept_ap=departure_airport, arri_ap=arrival_airport, dept_city=departure_city, arri_city=arrival_city, dept_time_from=departure_date_from, dept_time_to=departure_date_to)

        return render_template('search_flights.html', error=[False],
                               airport_lst=airport_lst, city_lst=city_lst, flights=flights)
    
    if request.method == 'POST' and request.form.get("Book"):
        if session['role'] == 'Customer':
            flight_number = request.form['flight_number']
            msg = f"Customer {session['username']} booked flight {flight_number}"


            avail = utils.retrieve_flights(conn, airline=flight_number[:2], flight_num=flight_number[2:])
            if avail[0]['status'] == "Cancelled":
                return render_template('search_flights.html', error=[True, f"Flight {flight_number} is cancelled"], 
                               airport_lst=airport_lst, city_lst=city_lst, flights=flights)
            if avail[0]['remaining_seats'] <= 0:
                return render_template('search_flights.html', error=[True, f"Flight {flight_number} is full"], 
                               airport_lst=airport_lst, city_lst=city_lst, flights=flights)

            cursor = conn.cursor()

            cursor.execute(f"INSERT INTO Ticket (flight_num, IATA_code) VALUES ({flight_number[2:]}, '{flight_number[:2]}')")
            cursor.execute(f"SELECT MAX(ticket_id) FROM Ticket WHERE flight_num={flight_number[2:]} AND IATA_code='{flight_number[:2]}'")
            ticket_id = cursor.fetchone()['MAX(ticket_id)']
            cursor.execute(f"""
                            INSERT INTO purchase VALUES(
                           {ticket_id}, '{session['email']}', NULL, NOW())
                           """)
            conn.commit()
            cursor.close()
            
            print(f"Customer {session['username']} booked flight {flight_number}")

        else:
            flight_number = request.form['flight_number']
            customer_email = request.form['email']

            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM Customer WHERE email='{customer_email}'")
            result = cursor.fetchone()
            if result == None:
                cursor.close()
                return render_template('search_flights.html', error=[True, f"Customer {customer_email} does not exist"], 
                               airport_lst=airport_lst, city_lst=city_lst, flights=flights)
            cursor.execute(f"INSERT INTO Ticket (flight_num, IATA_code) VALUES ({flight_number[2:]}, '{flight_number[:2]}')")
            cursor.execute(f"SELECT MAX(ticket_id) FROM Ticket WHERE flight_num={flight_number[2:]} AND IATA_code='{flight_number[:2]}'")
            ticket_id = cursor.fetchone()['MAX(ticket_id)']
            cursor.execute(f"INSERT INTO purchase VALUES({ticket_id}, '{customer_email}', '{session['email']}', NOW())")
            conn.commit()
            cursor.close()
            
            msg = f"Agent {session['username']} booked flight {flight_number} for customer {customer_email}"
            print(f"Agent {session['username']} booked flight {flight_number} for customer {customer_email}")


        return render_template('search_flights.html', error=[True, msg], 
                               airport_lst=airport_lst, city_lst=city_lst, flights=flights)

    return render_template('search_flights.html', error=[False], 
                           airport_lst=airport_lst, city_lst=city_lst, flights=flights)

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
    if session['role'] == 'Customer':
        flights = utils.retrieve_flights_with_passengers(conn, customer=session['email'])
    elif session['role'] == 'Agent':
        flights = utils.retrieve_flights_with_passengers(conn, agent=session['email'])
    else:
        flights = utils.retrieve_flights_with_passengers(conn, staff=session['email'])

    if request.method == 'POST':
        from_date = request.form['departure_date_from']
        to_date = request.form['departure_date_to']
        print(f"Searching for flights from {from_date} to {to_date}")
        if session['role'] == 'Customer':
            flights = utils.retrieve_flights_with_passengers(conn, customer=session['email'], date_from=from_date, date_to=to_date)
        elif session['role'] == 'Agent':
            flights = utils.retrieve_flights_with_passengers(conn, agent=session['email'], date_from=from_date, date_to=to_date)
        else:
            flights = utils.retrieve_flights_with_passengers(conn, staff=session['email'], date_from=from_date, date_to=to_date)
        
        return render_template('view_my_flights.html', start_date=from_date, end_date=to_date, flights=flights)
    return render_template('view_my_flights.html', flights=flights)

@app.route('/track_spendings', methods=['GET', 'POST'])
def track_spendings():

    if request.method == 'POST':
        from_date = request.form['departure_date_from']
        to_date = request.form['departure_date_to']
        filename = utils.monthly_spendings(conn, from_date, to_date, session['email'])
        print(f"Searching for flights from {from_date} to {to_date}")
        img_url = url_for('static', filename=f'{filename}.png')
        return render_template('track_spendings.html', filename=img_url)

    today = datetime.now()
    from_date = []
    if today.month - 5 <= 0:
        from_date.append(str(today.year -  1))
        from_date.append(str(today.month + 7))
    else:
        from_date.append(str(today.year))
        from_date.append(str(today.month - 5))

    from_date = "-".join(from_date)


    filename= utils.monthly_spendings(conn, from_date, f"{today.year}-{today.month}", session["email"])
    img_url = url_for('static', filename=f'{filename}.png')
    return render_template('track_spendings.html', filename=img_url)

@app.route('/view_commission', methods=['GET', 'POST'])
def view_commission():
    cursor = conn.cursor()
    cursor.execute(f"""
                SELECT COUNT(ticket_id) as CNT
                FROM purchase
                WHERE agent_email='{session["email"]}'   """)
    
    ttl_tickets = cursor.fetchone()["CNT"]

    cursor.execute(f"""
                SELECT SUM(price) as SUM
                FROM ticket NATURAL JOIN purchase NATURAL JOIN flight
                WHERE agent_email='{session["email"]}'
                   """)
    ttl_commission = float(cursor.fetchone()["SUM"]) * 0.1
    cursor.close()

    if ttl_tickets == 0:
        avg_commission = 0
    else:
        avg_commission  = ttl_commission/ttl_tickets
    if request.method == 'POST':
        from_date = request.form['departure_date_from']
        to_date = request.form['departure_date_to']
        restriction = []
        if from_date != "":
            restriction.append(f"date >= '{from_date}'")
        if to_date != "":
            restriction.append(f"date <= '{to_date}'")

        if restriction:
            restriction = " AND ".join(restriction)
        else:
            restriction = ""

        cursor = conn.cursor()
        cursor.execute(f"""
                    SELECT COUNT(ticket_id) as CNT
                    FROM purchase
                    WHERE agent_email='{session["email"]}' AND {restriction}""")
        
        ttl_tickets = cursor.fetchone()["CNT"]

        cursor.execute(f"""
                    SELECT SUM(price) as SUM
                    FROM ticket NATURAL JOIN purchase NATURAL JOIN flight
                    WHERE agent_email='{session["email"]}' AND {restriction}
                    """)
        ttl_commission = float(cursor.fetchone()["SUM"]) * 0.1
        cursor.close()
        if ttl_tickets == 0:
            avg_commission = 0
        else:
            avg_commission  = ttl_commission/ttl_tickets

        return render_template('view_commission.html', start_date=from_date, end_date=to_date, ttl_commission=ttl_commission, ttl_tickets=ttl_tickets, avg_commission=avg_commission)
    return render_template('view_commission.html', start_date=None, end_date=None, ttl_commission=ttl_commission, ttl_tickets=ttl_tickets, avg_commission=avg_commission)

@app.route('/view_top_customers', methods=['GET', 'POST'])
def view_top_customers():
    today = datetime.now()
    from_date = []
    if today.month - 5 <= 0:
        from_date.append(str(today.year -  1))
        from_date.append(str(today.month + 7))
    else:
        from_date.append(str(today.year))
        from_date.append(str(today.month - 5))
    from_date.append("01")
    from_date = "-".join(from_date)
    filename = utils.top_customers(conn, from_date, f"{today.year}-{today.month}-{today.day}", session['email'])
    img_url = url_for('static', filename=f"{filename}.png")

    if request.method == 'POST':
        from_date = request.form['departure_date_from']
        to_date = request.form['departure_date_to']
        img_url = url_for('static', filename='img0.jpg')

        return render_template('view_top_customers.html', start_date=from_date, end_date=to_date, filename=img_url)    
    return render_template('view_top_customers.html', start_date=None, end_date=None, filename=img_url)

# @app.route('/manage_flights', methods=['GET', 'POST'])
# def manage_flights():
#     return

@app.route('/create_new_flights', methods=['GET', 'POST'])
def create_new_flights():
    if session["admin"] == False:
        return render_template('home.html', msg=[True, "No admin permission"])
    if request.method == 'POST':
        airport_city_dict, airport_lst, city_lst = utils.retrieve_airports_and_city(conn)
        airplane_lst = utils.retrieve_airplanes(conn, session['airline'])
        departure_airport = request.form['departure_airport']
        arrival_airport = request.form['arrival_airport']
        departure_time = request.form['departure_time']
        arrival_time = request.form['arrival_time']
        price = request.form['price']
        airplane_id = request.form['Airplane_id']
        flag = utils.create_new_flights(conn, departure_airport, arrival_airport, departure_time, arrival_time, price, airplane_id, session['airline'])
        if flag == 0:
            return render_template('create_new_flights.html', airport_lst=airport_lst, airplane_lst=airplane_lst, msg=[True, f"New flight created from {departure_airport} to {arrival_airport} at {departure_time} to {arrival_time} for ${price} with airplane {airplane_id}"])
        elif flag == 1:
            return render_template('create_new_flights.html', airport_lst=airport_lst, airplane_lst=airplane_lst, msg=[True, f"Error, plane in use"])
        else:
            return render_template('create_new_flights.html', airport_lst=airport_lst, airplane_lst=airplane_lst, msg=[True, f"Error, arrival time after departure time"])
    
    airport_city_dict, airport_lst, city_lst = utils.retrieve_airports_and_city(conn)
    airplane_lst = utils.retrieve_airplanes(conn, session['airline'])
    return render_template('create_new_flights.html', msg=[False], airport_lst=airport_lst, airplane_lst=airplane_lst)

@app.route('/change_status', methods=['GET', 'POST'])
def change_status():
    if session["operator"] == False and session["admin"] == False:
        return render_template('home.html', msg=[True, "No operator permission"])
    
    if request.method == 'POST' and request.form.get("Change"):
        flight_id = request.form['flight_id']
        new_departure_time = request.form['new_departure_time'] 
        new_arrival_time = request.form['new_arrival_time']
        if flight_id[:2] != session['airline']:
            flights = utils.retrieve_flights(conn, airline=session['airline'], dept_time_from=datetime.now())
            return render_template('change_status.html', flights=flights, msg=[True, f"Flight {flight_id} does not belong to {session['airline']}"])
        
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM flight WHERE flight_num={flight_id[2:]} AND IATA_code='{flight_id[:2]}'")
        if not cursor.fetchone():
            cursor.close()
            flights = utils.retrieve_flights(conn, airline=session['airline'], dept_time_from=datetime.now())
            return render_template('change_status.html', flights=flights, msg=[True, f"Flight {flight_id} does not exist"])
        

        cursor.execute(f"SELECT Departure_time, Arrival_time FROM flight WHERE flight_num={flight_id[2:]} AND IATA_code='{flight_id[:2]}'")
        result = cursor.fetchone()
        cursor.execute(f"""UPDATE flight
                            SET Departure_time='{new_departure_time}', Arrival_time='{new_arrival_time}'
                            WHERE flight_num={flight_id[2:]} AND IATA_code='{flight_id[:2]}'
                          """)
        
        
        if result['Departure_time'] < datetime.strptime(new_departure_time, "%Y-%m-%dT%H:%M"):
            cursor.execute(f"""UPDATE flight
                                SET status='Delayed'
                                WHERE flight_num={flight_id[2:]} AND IATA_code='{flight_id[:2]}'
                            """)
        conn.commit()
        cursor.close()

        print(f"Flight {flight_id} departure time changed to {new_departure_time} and arrival time changed to {new_arrival_time} by {session['username']}")
        flights = utils.retrieve_flights(conn, airline=session['airline'], dept_time_from=datetime.now())
        return render_template('change_status.html', flights=flights, msg=[True, f"Flight {flight_id} departure time changed to {new_departure_time} and arrival time changed to {new_arrival_time} by {session['username']}"])

    if request.method == 'POST' and request.form.get("Cancel"):
        flight_id = request.form['flight_id']
        if flight_id[:2] != session['airline']:
            flights = utils.retrieve_flights(conn, airline=session['airline'], dept_time_from=datetime.now())
            return render_template('change_status.html', flights=flights, msg=[True, f"Flight {flight_id} does not belong to {session['airline']}"])
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM flight WHERE flight_num={flight_id[2:]} AND IATA_code='{flight_id[:2]}'")
        if not cursor.fetchone():
            cursor.close()
            flights = utils.retrieve_flights(conn, airline=session['airline'], dept_time_from=datetime.now())

            return render_template('change_status.html', flights=flights, msg=[True, f"Flight {flight_id} does not exist"])
        cursor.execute(f"""UPDATE flight
                            SET status='Cancelled'
                            WHERE flight_num={flight_id[2:]} AND IATA_code='{flight_id[:2]}'
                       """)
        conn.commit()
        cursor.close()
        print(f"Flight {flight_id} cancelled by {session['username']}")
        flights = utils.retrieve_flights(conn, airline=session['airline'], dept_time_from=datetime.now())
        return render_template('change_status.html', flights=flights, msg=[True, f"Flight {flight_id} cancelled by {session['username']}"])

    print(datetime.now())
    flights = utils.retrieve_flights(conn, airline=session['airline'], dept_time_from=datetime.now())
    return render_template('change_status.html', msg=[False], flights=flights)

@app.route('/add_new_plane', methods=['GET', 'POST'])
def add_new_plane():
    if session["admin"] == False:
        return render_template('home.html', msg=[True, "No admin permission"])
    if request.method == 'POST':
        seat_count = request.form['seats']
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO Airplane (seats, IATA_code) VALUES ({seat_count}, '{session['airline']}')")
        conn.commit()
        cursor.close()
        return render_template('add_new_plane.html', msg=[True, f"New plane added with {seat_count} seats"])
    return render_template('add_new_plane.html', msg=[False])

@app.route('/add_new_airport', methods=['GET', 'POST'])
def add_new_airport():
    if session["admin"] == False:
        return render_template('home.html', msg=[True, "No admin permission"])
    if request.method == 'POST':
        airport_name = request.form['airport_name']
        city = request.form['airport_city']
        cursor = conn.cursor()
        try:
            cursor.execute(f"INSERT INTO airport (Airport_name, city) VALUES ('{airport_name}', '{city}')")
            conn.commit()
            cursor.close()
        except:
            cursor.close()
            return render_template('add_new_airport.html', msg=[True, f"Airport {airport_name} already exists"])
        
        print(f"New airport added with name {airport_name} in {city} by {session['username']}")
        return render_template('add_new_airport.html', msg=[True, f"New airport added with name {airport_name} in {city}"])
    return render_template('add_new_airport.html', msg=[False])

@app.route('/manage_agents', methods=['GET', 'POST'])
def manage_agents():
    if request.method == 'POST' and request.form.get("Search"):
        date_from = request.form['from_date']
        date_to = request.form['date_to']
        agents = utils.retrieve_agents(conn, session['airline'], date_from, date_to)
        print(f"Searching for agents from {date_from} to {date_to}")
        return render_template('manage_agents.html', agents=agents, msg=[True, f"Searching for agents from {date_from} to {date_to}"])  
    if request.method == 'POST' and request.form.get("Add"):
        email = request.form['email']
        cursor = conn.cursor()
        try:
            cursor.execute(f"INSERT INTO Agent_work_for VALUES ('{email}', '{session['airline']}')")
            conn.commit()
            cursor.close()
        except:
            cursor.close()
            agents = utils.retrieve_agents(conn, session['airline'])
            return render_template('manage_agents.html', agents=agents, msg=[True, f"Agent {email} not exists or already working for you"])
        return render_template('manage_agents.html', msg=[True, f"Agent {email} added by {session['username']}"])    
    
    agents = utils.retrieve_agents(conn, session['airline'])
    return render_template('manage_agents.html', agents=agents, msg=[False])

@app.route('/view_frequent_customers', methods=['GET', 'POST'])
def view_frequent_customers():
    if request.method == 'POST' and request.form.get("Search"):
        date_from = request.form['from_date']
        date_to = request.form['date_to']
        print(f"Searching for customers from {date_from} to {date_to}")
        customers = utils.retrieve_frequent_customers(conn, session['airline'], date_from, date_to)
        return render_template('view_frequent_customers.html', customers=customers, msg=[True, f"Searching for agents from {date_from} to {date_to}"])
    
    customers = utils.retrieve_frequent_customers(conn, session['airline'], date_from=datetime.now()-timedelta(days=365), date_to=datetime.now())
    return render_template('view_frequent_customers.html', customers=customers, msg=[False]) 

@app.route('/view_reports', methods=['GET', 'POST'])
def view_reports():
    
    if request.method == 'POST' and request.form.get("Search"):
        date_from = request.form['from_date']
        date_to = request.form['date_to']
        date_from = utils.month(date_from)
        date_to = utils.month(date_to)
        ttl_tickets, filename = utils.view_report(conn, session['airline'], date_from=date_from, date_to=date_to)
        img_url = url_for('static', filename=f"{filename}.png")
        return render_template('view_reports.html', ttl_tickets=ttl_tickets, date_from=date_from, date_to=date_to, filename=img_url, msg=[False])
    
    ttl_tickets, filename = utils.view_report(conn, session['airline'], date_from=(datetime.now()-timedelta(days=365)), date_to=(datetime.now()))
    img_url = url_for('static', filename=f"{filename}.png")
    return render_template('view_reports.html', msg=[False], ttl_tickets=ttl_tickets, filename=img_url, date_from=None, date_to=None)

@app.route('/manage_staff', methods=['GET', 'POST'])
def manage_staff():
    if request.method == "POST":
        username = request.form['username']
        premission = request.form['permission']

        staff_lst = utils.retrieve_staff(conn, session['airline'])

        cursor = conn.cursor()
        try:
            cursor.execute(f"UPDATE AirlineStaff SET {premission} = 1 WHERE aStaff_username='{username}'")
            conn.commit()
            cursor.close()
        except:
            cursor.close()
            return render_template('manage_staff.html', staff_lst=staff_lst, msg=[True, f"User {username} not exists"])
        
        staff_lst = utils.retrieve_staff(conn, session['airline'])
        return render_template('manage_staff.html', staff_lst=staff_lst, msg=[True, f"User {username} has been granted {premission} by {session['username']}"])
    

    staff_lst = utils.retrieve_staff(conn, session['airline'])
    return render_template('manage_staff.html', staff_lst=staff_lst, msg=[False])

@app.route('/upload/<filename>')
def send_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(debug=True)

