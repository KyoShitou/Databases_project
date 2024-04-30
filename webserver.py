from flask import Flask, render_template, request, session, url_for, redirect, render_template_string, flash
import pymysql.cursors

app = Flask(__name__)
app.secret_key = "DATABASES"

conn = pymysql.connect(host="localhost", user="root", password="", db="Airplane_Management", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)

def searchFlight(dept_city=None, dept_apt=None, arrival_city=None, arrival_ap=None, date=None):
    condition = []
    if dept_city != None:
        condition.append(f"Dept_Airport.City = '{dept_city}'")
    if dept_apt != None:
        condition.append(f"Departure_Airport = '{dept_apt}'")
    if arrival_city != None:
        condition.append(f"Arri_Airport.City = '{arrival_city}'")
    if arrival_ap != None:
        condition.append(f"Arrival_Airport = '{arrival_ap}'")
    if date != None:
        condition.append(f"Departure_time LIKE '{date}%'")
    
    cursor = conn.cursor()
    if condition == []:
        query = '''SELECT flight_num, IATA_code, Airplane_id, Airline_name, Departure_time, Arrival_time, price, status,
                        Departure_Airport, Dept_Airport.City AS Dept_City, 
                        Arrival_Airport, Arri_Airport.City AS Arri_City,
                        CASE 
                        WHEN status = 'cancelled' THEN 'cancelled'
                        WHEN Arrival_time < NOW() THEN 'completed'
                        WHEN status = 'delayed' THEN 'delayed'
                        WHEN Departure_time > NOW() THEN 'upcoming'
                        ELSE 'in-progress'
                    END AS status_now
                    FROM flight
                        LEFT JOIN Airport AS Dept_Airport ON flight.Departure_Airport = Dept_Airport.Airport_name
                        LEFT JOIN Airport AS Arri_Airport ON flight.Arrival_Airport = Arri_Airport.Airport_name
                        NATURAL JOIN Airline'''
    else:
        condition = " AND ".join(condition)
        query = f"""SELECT flight_num, IATA_code, Airplane_id, Airline_name, Departure_time, Arrival_time, price, status,
                        Departure_Airport, Dept_Airport.City AS Dept_City, 
                        Arrival_Airport, Arri_Airport.City AS Arri_City,
                        CASE 
                        WHEN status = 'cancelled' THEN 'cancelled'
                        WHEN Arrival_time < NOW() THEN 'completed'
                        WHEN Departure_time > NOW() THEN 'upcoming'
                        WHEN status = 'delayed' THEN 'delayed'
                        ELSE 'in-progress'
                    END AS status_now
                    FROM flight
                        LEFT JOIN Airport AS Dept_Airport ON flight.Departure_Airport = Dept_Airport.Airport_name
                        LEFT JOIN Airport AS Arri_Airport ON flight.Arrival_Airport = Arri_Airport.Airport_name
                        NATURAL JOIN Airline
                    WHERE {condition}"""
    cursor.execute(query)
    data = cursor.fetchall()

    for flight in data:
        flight_num = flight['flight_num']
        airline_code = flight['IATA_code']
        cursor.execute(f''' SELECT COUNT(*) as cnt
                            FROM ticket
                            WHERE flight_num={flight_num} AND IATA_code='{airline_code}'
                       ''')
        seats_sold = cursor.fetchall()[0]
        cursor.execute(f"SELECT seats FROM airplane WHERE Airplane_id = {flight['Airplane_id']}")
        total_seats = cursor.fetchone()
        flight['remaining_seats'] = total_seats["seats"] - seats_sold["cnt"]
        
    cursor.close()




    return data

@app.route('/', endpoint="home", methods=['GET', 'POST'])
def DisplayUpcomingFlight():
    data = searchFlight()

    cursor = conn.cursor()
    cursor.execute(' SELECT Airport_name FROM Airport ')
    airport_lst = cursor.fetchall()
    cursor.execute(' SELECT DISTINCT City FROM Airport ')
    city_lst = cursor.fetchall()
    cursor.close()

    city_pulldown_msg = ""
    airport_pulldown_lst = ""

    for city in city_lst:
        city_pulldown_msg += f"<option value=\"{city['City']}\">{city['City']}</option>\n"

    for airport in airport_lst:
        airport_pulldown_lst += f"<option value=\"{airport['Airport_name']}\">{airport['Airport_name']}</option>\n"
    
    login_status = "NOT LOGGED IN"
    # msg = ''


    # for flight in data:
    #     msg += "<tr>\n"
    #     # msg += f"<td> {flight['IATA_code']} </td>\n"
    #     # msg += f"<td> {flight['flight_num']} </td>\n"
    #     msg += f"<td> {flight['IATA_code']}{flight['flight_num']:03} </td>\n"
    #     msg += f"<td> {flight['Departure_time']} </td>\n"
    #     msg += f"<td> {flight['Arrival_time']} </td>\n"
    #     msg += f"<td "
    #     if flight['status_now'] == 'completed':
    #         msg += "style=\"color: grey;\">"
    #     elif flight['status_now'] == 'cancelled':
    #         msg += "style=\"color: red;\">"
    #     elif flight['status_now'] == 'upcoming':
    #         msg += "style=\"color: green;\">"
    #     elif flight['status_now'] == 'delayed':
    #         msg += "style=\"color: orange;\">"
    #     elif flight['status_now'] == 'in-progress':
    #         msg += "style=\"color: green;\">"
    #     msg += f"{flight['status_now']} </td>\n"
    #     msg += f"<td> {flight['remaining_seats']} </td>\n"
    #     msg += f"<td> {flight['Departure_Airport']} </td>\n"
    #     msg += f"<td> {flight['Dept_City']} </td>\n"
    #     msg += f"<td> {flight['Arrival_Airport']} </td>\n"
    #     msg += f"<td> {flight['Arri_City']} </td>\n"
    #     msg += "</tr>\n"
        
    f = open("templates/home_alt.html")
    h = f.read()
    f.close()
    return render_template("home_alt.html", flights=data, city_pulldown_msg=city_pulldown_msg, airport_pulldown_lst=airport_pulldown_lst
                           , login_status=login_status, city_lst=city_lst, airport_lst=airport_lst)
    # return render_template_string(h.replace("{msg}", msg).replace("{city_pulldown_msg}", city_pulldown_msg))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form["username"]
            email = request.form["email"]
            password = request.form["password"]
            user_type = request.form["Identity"]

            if user_type == "Customer":
                return redirect(url_for("register_customer", username=username, password=password, email=email))
            elif user_type == "Agent":
                return redirect(url_for("register_agent", username=username, password=password, email=email)) 
        except:
            return render_template("register.html")   
        
    return render_template("register.html")

@app.route('/register/customer', endpoint="register_customer", methods=['GET', 'POST'])
def customer_reg():
    username = request.args.get('username')
    email = request.args.get('email')
    password = request.args.get('password')

    return render_template("register_customer.html", username=username, email=email, password=password)

@app.route('/register/agent', endpoint="register_agent", methods=['GET', 'POST'])
def agent_reg():
    username = request.args.get('username')
    email = request.args.get('email')
    password = request.args.get('password')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Airline")
    airlines = cursor.fetchall()
    cursor.close()

    airlines_dict = {}
    airlines_lst = []
    for airline in airlines:
        airlines_dict[airline["Airline_name"]] = airline["IATA_code"]
        airlines_lst.append(airline["Airline_name"])

    if request.method == "POST":
        user_name = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        checked__company = request.form.getlist("company")

        err_flag = False

        cursor = conn.cursor()
        try:
            cursor.execute(f"""INSERT INTO Customer (email, name, password)
                           VALUES('{email}', '{user_name}',
                           '{password}')""")        
            print(f"""EXECUTED INSERT INTO BookingAgent (email, name, password)
                           VALUES('{email}', '{user_name}',
                           '{password}')""")
        except:
            err_flag = True
            flash(f"Error: {email} already exists")
        finally:
            cursor.close()

        unknown_err_flag = False

        if err_flag:
            pass
        else:
            for company in checked__company:
                cursor = conn.cursor()
                try:
                    cursor.execute(f"""INSERT INTO Agent_work_for (agent_email, IATA_code)
                                   VALUES('{email}', '{airlines_dict[company]}')""")
                except:
                    unknown_err_flag = True
                finally:
                    cursor.close()

            if unknown_err_flag:
                flash(f"Error: Unknown Error")
                redirect(url_for("register_agent", username=username, email=email, password=password))
            else:
                flash(f"Success: {email} has been registered as an agent for {checked__company}")
                return redirect(url_for("home"))


    return render_template("register_agent.html", username=username, email=email, password=password, airline_names=airlines_lst)

def staff_reg():
    return

if __name__ == "__main__":
    app.run("127.0.0.1", 5000, debug=True)
    
