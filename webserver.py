from flask import Flask, render_template, request, session, url_for, redirect, render_template_string, flash
import pymysql.cursors
import os
from utils import *
from home import *

app = Flask(__name__)
app.secret_key = "DATABASES"

conn = pymysql.connect(host="localhost", user="root", password="", db="Airplane_Management", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)

@app.route('/', endpoint="home", methods=['GET', 'POST'])
def home():
    return DisplayUpcomingFlight(conn)
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
    app.config['SECRET_KEY'] = "DATABASES" 
    session['logged_in'] = "NOT LOGGED IN"
    app.run("127.0.0.1", 5000, debug=True)
