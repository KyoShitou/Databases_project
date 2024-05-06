import matplotlib.pyplot as plt
import datetime
import os
from copy import deepcopy


def query_anti_injection(query):
    query = query.replace("'", "\\'")
    query = query.replace('"', '\\"')
    query = query.replace(";", "")
    return query

def gen_date_restriction(date_from, date_to, name="date"):
    if date_from and date_to:
        date_restriction = f"AND {name} BETWEEN '{date_from}' AND '{date_to}'"
    elif date_from:
        date_restriction = f"AND {name} >= '{date_from}'"
    elif date_to:
        date_restriction = f"AND {name} <= '{date_to}'"
    else:
        date_restriction = ""
    return date_restriction

def retrieve_airlines(conn):
    cursor = conn.cursor()
    cursor.execute(f"""
                    SELECT * FROM Airline
                   """)
    data = cursor.fetchall()
    cursor.close()
    return data

def retrieve_airports_and_city(conn):
    cursor = conn.cursor()
    cursor.execute(f"""
                    SELECT * FROM Airport
                   """)
    data = cursor.fetchall()
    cursor.close()
    airport_city_dict = {}
    airport_lst = []
    city_lst = []

    for p in data:
        airport_city_dict.update({p["Airport_name"]: p["City"]})
        airport_lst.append(p["Airport_name"])
        city_lst.append(p["City"])
        
    return airport_city_dict, airport_lst, city_lst

def retrieve_airplanes(conn, airline):
    cursor = conn.cursor()
    cursor.execute(f"SELECT Airplane_id, seats FROM Airplane WHERE IATA_code='{airline}'")
    data = cursor.fetchall()
    cursor.close()
    return data

def retrieve_flights(conn, airline=None, num=None, dept_city=None, dept_ap=None, arri_city=None, arri_ap=None, 
                     dept_time_from=None, dept_time_to=None):
    cursor = conn.cursor()
    restrictions = []
    if airline:
        if type(airline) == str:
            restrictions.append(f"IATA_code='{airline}'")
        if type(airline) == list:
            airline_str = ', '.join([f"'{a}'" for a in airline])
            restrictions.append(f"IATA_code IN ({airline_str})")
    if num:
        restrictions.append(f"flight_num={num}")
    if dept_time_from and dept_time_to:
        restrictions.append(f"Departure_time BETWEEN '{dept_time_from}' AND '{dept_time_to}'")
    elif dept_time_from:
        restrictions.append(f"Departure_time >= '{dept_time_from}'")
    elif dept_time_to:
        restrictions.append(f"Departure_time <= '{dept_time_to}'")
    
    if dept_city != "None" and dept_city:
        restrictions.append(f"Dept_Airport.City='{dept_city}'")
    if dept_ap != "None" and dept_city:
        restrictions.append(f"Departure_Airport='{dept_ap}'")
    if arri_city != "None" and dept_city:
        restrictions.append(f"Arri_Airport.City='{arri_city}'")
    if arri_ap != "None" and dept_city:
        restrictions.append(f"Arrival_Airport='{arri_ap}'")

    query = """SELECT flight_num, IATA_code, Airplane_id, Airline_name, Departure_time, Arrival_time, price, status,
                        Departure_Airport, Dept_Airport.City AS Departure_city, 
                        Arrival_Airport, Arri_Airport.City AS Arrival_city,
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
                        NATURAL JOIN Airline"""

    if restrictions:
        query += "\nWHERE " + " AND ".join(restrictions)
    print(query)
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

    data.sort(key=lambda x : x["Departure_time"])
    return data

def retrieve_flights_with_passengers(conn, agent=None, staff=None, customer=None, date_from=None, date_to=None):
    cursor = conn.cursor()
    if (agent == None) and (staff == None) and (customer == None):
        return None
    date_restriction = gen_date_restriction(date_from, date_to, name='Departure_time')
    if customer:
        cursor.execute(f"""SELECT DISTINCT flight_num, IATA_code
                       FROM purchase NATURAL JOIN ticket NATURAL JOIN flight
                        WHERE customer_email='{customer}' {date_restriction}
                       """)
        result = cursor.fetchall()
        ret = []
        for f in result:
            t = retrieve_flights(conn, num=f["flight_num"], airline=f["IATA_code"])
            if len(t) != 0:
                ret.append(t[0])
            else:
                continue
        ret.sort(key=lambda x : x["Departure_time"])
        
    if agent:
        cursor.execute(f"""SELECT DISTINCT flight_num, IATA_code
                       FROM ticket NATURAL JOIN purchase NATURAL JOIN flight
                        WHERE agent_email='{agent}' {date_restriction}
                       """)
        result = cursor.fetchall()
        print(result)
        ret = []
        for f in result:
            ret.append(retrieve_flights(conn, num=f["flight_num"], airline=f["IATA_code"])[0])
            cursor.execute(f"""SELECT customer.name as name
                           FROM flight NATURAL JOIN ticket NATURAL JOIN purchase JOIN customer ON purchase.customer_email = customer.email
                            WHERE flight_num={f["flight_num"]} AND IATA_code='{f["IATA_code"]}' AND agent_email='{agent}'   """)
            passengers_ = cursor.fetchall()
            passengers = []
            for p in passengers_:
                passengers.append(p["name"])
            passengers = ', '.join(passengers)
            ret[-1]["passengers"] = passengers
            ret.sort(key=lambda x : x["Departure_time"])
    if staff:
        cursor.execute(f"SELECT IATA_code FROM AirlineStaff WHERE email='{staff}'")
        airline = cursor.fetchone()
        ret = retrieve_flights(conn, airline=airline["IATA_code"], dept_time_from=date_from, dept_time_to=date_to)
        for f in ret:
            cursor.execute(f"""SELECT customer.name as name
                           FROM flight NATURAL JOIN ticket NATURAL JOIN purchase JOIN customer ON purchase.customer_email = customer.email
                            WHERE flight_num={f["flight_num"]} AND IATA_code='{f["IATA_code"]}'    """)
            passengers_ = cursor.fetchall()
            passengers = []
            for p in passengers_:
                passengers.append(p["name"])
            if passengers:
                passengers = ', '.join(passengers)
            else:
                passengers = "No passengers"
            f["passengers"] = passengers
        
        ret.sort(key=lambda x : x["Departure_time"])
        
    cursor.close()
    return ret

class month:
    def __init__(self, string):
        self.year = int(string[:4])
        self.month = int(string[5:7])
    
    def __lt__(self, other):
        if self.year < other.year:
            return True
        if self.year == other.year:
            if self.month < other.month:
                return True
        return False
    
    def __eq__(self, other):
        return self.year == other.year and self.month == other.month
    
    def __gt__(self, other):
        return (not self < other) and (not self == other)
    
    def __le__(self, other):
        return self < other or self == other
    
    def __str__(self) -> str:
        return f"{self.year}-{self.month:02d}"
    
    def addmonth(self, n):
        self.month += n
        while self.month > 12:
            self.year += 1
            self.month -= 12
        return self

def monthly_spendings(conn, date_from, date_to, customer):
    cursor = conn.cursor()
    date_from = month(date_from)
    date_to = month(date_to)
    
    months = []
    ret = []

    while date_from <= date_to:
        months.append(str(date_from))
        q = f"""SELECT SUM(price) as total
                           FROM purchase NATURAL JOIN ticket NATURAL JOIN flight
                           WHERE customer_email='{customer}' AND date LIKE '{date_from}%'"""
        date_from.addmonth(1)
        print(q)
        cursor.execute(q)
        result = cursor.fetchone()


        if result["total"] == None:
            ret.append(0)
        else:
            ret.append(int(result["total"]))
    
    cursor.close()

    # plot a bar char of the monthly spendings and save it to "filename.png"

    plt.bar(range(len(ret)), ret)
    plt.xlabel('Month')
    plt.ylabel('Total Spendings')
    plt.title('Monthly Spendings')
    plt.xticks(range(len(ret)), months)
    filename = str(datetime.datetime.now())
    # Get the current directory of the script
    current_directory = os.path.dirname(os.path.realpath(__file__))

    # Create the path to the static folder
    static_folder_path = os.path.join(current_directory, 'static')

    # Create the static folder if it doesn't exist
    if not os.path.exists(static_folder_path):
        os.makedirs(static_folder_path)

    # Save the plot to the static folder
    plt.savefig(os.path.join(static_folder_path, f'{filename}.png'))
    plt.close()
    
    return filename

def top_customers(conn, date_from, date_to, agent):
    date_restriction = []
    if date_from:
        date_restriction.append(f"date >= '{date_from}'")
    if date_to:
        date_restriction.append(f"date <= '{date_to}'")
    
    date_restriction = " AND ".join(date_restriction)

    cursor = conn.cursor()
    cursor.execute(f""" SELECT customer_email, name FROM purchase JOIN Customer ON purchase.customer_email=Customer.email
                   WHERE agent_email='{agent}' AND {date_restriction}
                   """)
    customers = cursor.fetchall()
    customers = [[c["customer_email"], c["name"]] for c in customers]
    ret = []
    for customer in customers:
        ret.append([customer[0]])
        cursor.execute(f""" SELECT SUM(price) as total
                       FROM purchase NATURAL JOIN ticket NATURAL JOIN flight
                       WHERE customer_email='{customer[0]}' AND agent_email='{agent}' 
                       AND {date_restriction}
                   """)
        ret[-1].append(float(cursor.fetchone()["total"]) * 0.1)
        cursor.execute(f""" SELECT COUNT(*) as total
                       FROM purchase NATURAL JOIN ticket
                       WHERE customer_email='{customer[0]}' AND agent_email='{agent}' 
                       AND {date_restriction}
                   """)
        ret[-1].append(cursor.fetchone()["total"])
        ret[-1].append(customer[1])
    cursor.close()
    
    if len(ret) <= 5:
        # Plotting two bar charts vertically arranged
        fig, ax = plt.subplots(2, 1, figsize=(8, 8))
        
        # First bar chart
        ret.sort(key=lambda x : x[1])
        ax[0].bar(range(len(ret)), [item[1] for item in ret])
        ax[0].set_ylabel('Total Commission')
        ax[0].set_title('Top Customers - Total Commission')
        ax[0].set_xticks(range(len(ret)))
        ax[0].set_xticklabels([item[3] for item in ret], rotation=45)
        
        # Second bar chart
        ret.sort(key=lambda x : x[2])
        ax[1].bar(range(len(ret)), [item[2] for item in ret])
        ax[1].set_xlabel('Customer')
        ax[1].set_ylabel('Total Tickets')
        ax[1].set_title('Top Customers - Total Tickets')
        ax[1].set_xticks(range(len(ret)))
        ax[1].set_xticklabels([item[3] for item in ret], rotation=45)
        
        # Adjust spacing between subplots
        plt.subplots_adjust(hspace=0.5)
        # Get the current directory of the script
        current_directory = os.path.dirname(os.path.realpath(__file__))

        # Create the path to the static folder
        static_folder_path = os.path.join(current_directory, 'static')

        # Create the static folder if it doesn't exist
        if not os.path.exists(static_folder_path):
            os.makedirs(static_folder_path)
        
        # Save the plot to the static folder
        filename = str(datetime.datetime.now())
        plt.savefig(os.path.join(static_folder_path, f'{filename}.png'))
        plt.close()

    # ret: [[customer_email, total_commission, total_tickets]]
    
    else:
        # Plotting two bar charts vertically arranged
        fig, ax = plt.subplots(2, 1, figsize=(8, 8))
        
        # First bar chart
        tmp = deepcopy(ret)
        tmp.sort(key=lambda x : x[1], reverse=True)
        tmp = tmp[:5]

        ax[0].bar(range(len(tmp)), [item[1] for item in tmp])
        ax[0].set_ylabel('Total Commission')
        ax[0].set_title('Top Customers - Total Commission')
        ax[0].set_xticks(range(len(tmp)))
        ax[0].set_xticklabels([item[3] for item in tmp], rotation=45)
        
        # Second bar chart
        tmp = deepcopy(ret)
        tmp.sort(key=lambda x : x[2], reverse=True)
        tmp = tmp[:5]
        ax[1].bar(range(len(tmp)), [item[2] for item in tmp])
        ax[1].set_xlabel('Customer')
        ax[1].set_ylabel('Total Tickets')
        ax[1].set_title('Top Customers - Total Tickets')
        ax[1].set_xticks(range(len(tmp)))
        ax[1].set_xticklabels([item[3] for item in tmp], rotation=45)
        
        # Adjust spacing between subplots
        plt.subplots_adjust(hspace=0.5)
        # Get the current directory of the script
        current_directory = os.path.dirname(os.path.realpath(__file__))

        # Create the path to the static folder
        static_folder_path = os.path.join(current_directory, 'static')

        # Create the static folder if it doesn't exist
        if not os.path.exists(static_folder_path):
            os.makedirs(static_folder_path)
        
        # Save the plot to the static folder
        filename = str(datetime.datetime.now())
        plt.savefig(os.path.join(static_folder_path, f'{filename}.png'))
        plt.close()

    return filename

def create_new_flights(conn, dept_ap, arri_ap, dept_time, arri_time, price, plane_id, IATA_code):
    cursor = conn.cursor()

    # INTEGRITY CHECK: if departure time is before arrival time
    if dept_time >= arri_time:
        cursor.close()
        return 2
    
    # INTEGRITY CHECK: if the plane is available
    cursor.execute(f"""
SELECT * FROM flight WHERE Airplane_id={plane_id} AND Arrival_time > '{dept_time}'  AND Departure_time < '{arri_time}'
                   """)
    if cursor.fetchall():
        cursor.close()
        return 1
    
    cursor.execute(f"""
INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_Airport, Arrival_Airport)
VALUES ('{IATA_code}', '{dept_time}', '{arri_time}', {price}, 'upcoming', {plane_id}, '{dept_ap}', '{arri_ap}')
                   """)
    
    print(f"""
INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_Airport, Arrival_Airport)
VALUES ('{IATA_code}', '{dept_time}', '{arri_time}', {price}, 'upcoming', {plane_id}, '{dept_ap}', '{arri_ap}')
                   """)
    conn.commit()
    cursor.close()
    return 0

def retrieve_agents(conn, airline, date_from=None, date_to=None):

    if date_from and date_to:
        date_restriction = f"AND date BETWEEN '{date_from}' AND '{date_to}'"
    elif date_from:
        date_restriction = f"AND date >= '{date_from}'"
    elif date_to:
        date_restriction = f"AND date <= '{date_to}'"
    else:
        date_restriction = ""

    cursor = conn.cursor()
    cursor.execute(f"""SELECT email, username 
                   FROM BookingAgent JOIN Agent_work_for ON BookingAgent.email=Agent_work_for.agent_email
                   WHERE IATA_code='{airline}'""")
    data = cursor.fetchall()
    for agent in data:
        email = agent["email"]
        cursor.execute(f"""SELECT COUNT(*) as total
                       FROM purchase NATURAL JOIN ticket
                       WHERE agent_email='{email}' AND IATA_code='{airline}' {date_restriction}""")
        agent["tickets"] = cursor.fetchone()["total"]
        cursor.execute(f"""SELECT SUM(price) as total
                          FROM purchase NATURAL JOIN ticket NATURAL JOIN flight
                          WHERE agent_email='{email}' AND IATA_code='{airline}' {date_restriction}""")
        comm = cursor.fetchone()["total"]
        if comm:
            agent["commission"] = float(comm) * 0.1
        else:
            agent["commission"] = 0
        
    cursor.close()
    data.sort(key=lambda x : x["commission"], reverse=True)
    return data

def retrieve_frequent_customers(conn, airline, date_from=None, date_to=None):
    if date_from and date_to:
        date_restriction = f"AND date BETWEEN '{date_from}' AND '{date_to}'"
    elif date_from:
        date_restriction = f"AND date >= '{date_from}'"
    elif date_to:
        date_restriction = f"AND date <= '{date_to}'"
    else:
        date_restriction = ""

    cursor = conn.cursor()
    cursor.execute(f"""SELECT email, name, date_of_birth
                   FROM Customer
                   WHERE email IN (
                        SELECT customer_email
                        FROM purchase NATURAL JOIN ticket
                        WHERE IATA_code='{airline}' {date_restriction}
                   )""")
    data = cursor.fetchall()
    for customer in data:
        cursor.execute(f"""SELECT COUNT(*) as total
                       FROM purchase NATURAL JOIN ticket
                       WHERE customer_email='{customer["email"]}' AND IATA_code='{airline}' {date_restriction}""")
        customer["tickets"] = cursor.fetchone()["total"]
        cursor.execute(f"""SELECT flight_num, IATA_code
                       FROM purchase NATURAL JOIN ticket
                       WHERE customer_email='{customer["email"]}' AND IATA_code='{airline}' {date_restriction}""")
        flights = cursor.fetchall()
        flights = [f'{f["IATA_code"]}{f["flight_num"]:03}' for f in flights]
        flights = ', '.join(flights)
        customer["flights"] = flights
    cursor.close()

    data.sort(key=lambda x : x["tickets"], reverse=True)
    return data

def ticket_info(conn, airline, date_from=None, date_to=None):
    '''ticket_info -> (ttl_tickets, [revenue_per_month])'''
    if date_to.month in (1, 3, 5, 7, 8, 10, 12):
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-31")
    elif date_to.month in (4, 6, 8, 9, 11):
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-30")
    else:
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-28")
    print(date_restriction)
    cursor = conn.cursor()
    cursor.execute(f"""SELECT COUNT(*) AS total
                    FROM ticket NATURAL JOIN purchase
                    WHERE IATA_code='{airline}' {date_restriction}""")
    ttl_tickets = cursor.fetchone()["total"]
    revenue_per_month = []
    date_from_iter = month(f"{date_from.year}-{date_from.month:02d}")
    while date_from_iter <= date_to:
        cursor.execute(f"""SELECT SUM(price) AS revenue
                        FROM purchase NATURAL JOIN ticket NATURAL JOIN flight
                        WHERE IATA_code='{airline}' AND date LIKE '{date_from_iter}%'""")
        revenue = cursor.fetchone()["revenue"]
        if revenue == None:
            revenue = 0
        revenue_per_month.append(revenue)
        date_from_iter.addmonth(1)
    cursor.close()
    return ttl_tickets, revenue_per_month


def revenue_partition(conn, airline, date_from=None, date_to=None):
    '''revenue_partition -> (total_direct_sales, total_agent_sales)'''
    if date_to.month in (1, 3, 5, 7, 8, 10, 12):
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-31")
    elif date_to.month in (4, 6, 8, 9, 11):
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-30")
    else:
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-28")
    cursor = conn.cursor()
    cursor.execute(f"""SELECT SUM(price) AS total
                    FROM purchase NATURAL JOIN ticket NATURAL JOIN flight
                    WHERE IATA_code='{airline}' AND agent_email IS NULL {date_restriction}""")
    total_direct_sales = cursor.fetchone()["total"]
    cursor.execute(f"""SELECT SUM(price) AS total
                    FROM purchase NATURAL JOIN ticket NATURAL JOIN flight
                    WHERE IATA_code='{airline}' AND agent_email IS NOT NULL {date_restriction}""")
    total_agent_sales = cursor.fetchone()["total"]
    cursor.close()
    return total_direct_sales, total_agent_sales

def top_destination(conn, airline, date_from=None, date_to=None):
    '''top_destination -> ((destination1, destination2, destination3), (freq1, freq2, freq3))'''
    if date_to.month in (1, 3, 5, 7, 8, 10, 12):
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-31", name="Departure_time")
    elif date_to.month in (4, 6, 8, 9, 11):
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-30", name="Departure_time")
    else:
        date_restriction = gen_date_restriction(f"{date_from}-01", f"{date_to}-28", name="Departure_time")
    cursor = conn.cursor()
    cursor.execute(f"""SELECT Arrival_Airport, COUNT(*) AS freq
                    FROM flight
                    WHERE IATA_code='{airline}' {date_restriction}
                    GROUP BY Arrival_Airport
                    ORDER BY freq DESC
                    LIMIT 3""")
    destinations = []
    frequencies = []
    for row in cursor.fetchall():
        destinations.append(row["Arrival_Airport"])
        frequencies.append(row["freq"])
    cursor.close()
    return destinations, frequencies

def view_report(conn, airline, date_from=None, date_to=None):
    if date_from is None and date_to is None:
        date_from = datetime.datetime.now()
        date_to = datetime.datetime.now() - datetime.timedelta(days=365)
    elif date_from is None:
        date_from = datetime.datetime.now() - datetime.timedelta(days=365)
    elif date_to is None:
        date_to = datetime.datetime.now()

    print(date_from, date_to)

    date_from = month(f"{date_from.year}-{date_from.month:02d}")
    date_from_iter = month(f"{date_from.year}-{date_from.month:02d}")
    date_to = month(f"{date_to.year}-{date_to.month:02d}")

    months = []
    while date_from_iter <= date_to:
        months.append(str(date_from_iter))
        date_from_iter.addmonth(1)

        
    ttl_tickets, revenue_per_month = ticket_info(conn, airline, date_from, date_to)
    ttl_direct_sale, ttl_agent_sale = revenue_partition(conn, airline, date_from, date_to)
    destinations, frequencies = top_destination(conn, airline, date_from, date_to)

    print(date_from, date_to)
    print(ttl_tickets, revenue_per_month, ttl_direct_sale, ttl_agent_sale, destinations, frequencies)
    
    # Plot 1: Bar chart of revenue per month
    plt.subplot(3, 1, 1)
    plt.bar(range(len(revenue_per_month)), revenue_per_month)
    plt.xlabel('Month')
    plt.ylabel('Revenue')
    plt.xticks(range(len(revenue_per_month)), months, rotation=45)
    plt.title('Revenue per Month')

    # Plot 2: Pie chart of total direct sales vs. total agent sales
    plt.subplot(3, 1, 2)
    labels = ['Direct Sales', 'Agent Sales']
    sizes = [ttl_direct_sale, ttl_agent_sale]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.gcf().set_size_inches(8, 8)
    plt.title('Total Direct Sales vs. Total Agent Sales')

    # Plot 3: Pie chart of frequencies annotated by destinations
    plt.subplot(3, 1, 3)
    plt.pie(frequencies, labels=destinations, autopct='%1.1f%%')
    plt.title('Frequencies by Destinations')

    # Adjust the layout to avoid overlapping
    plt.tight_layout()

    # Show the plots
    filename = str(datetime.datetime.now())
    # Get the current directory of the script
    current_directory = os.path.dirname(os.path.realpath(__file__))

    # Create the path to the static folder
    static_folder_path = os.path.join(current_directory, 'static')

    # Create the static folder if it doesn't exist
    if not os.path.exists(static_folder_path):
        os.makedirs(static_folder_path)

    # Save the plot to the static folder
    plt.savefig(os.path.join(static_folder_path, f'{filename}.png'))
    plt.close()
    
    return ttl_tickets, filename

def retrieve_staff(conn, airline):
    cursor = conn.cursor()
    cursor.execute(f"""SELECT email, first_name, last_name, Admin_perm, Oper_perm, date_of_birth, aStaff_username AS username
                   FROM AirlineStaff
                   WHERE IATA_code='{airline}'""")
    data = cursor.fetchall()
    cursor.close()
    return data


def retrieve_flights_for_customers(conn, customer, airline=None, num=None, dept_city=None, dept_ap=None, arri_city=None, arri_ap=None, 
                     dept_time_from=None, dept_time_to=None):
    cursor = conn.cursor()
    restrictions = []
    restrictions.append(f"customer_email='{customer}'")
    if airline:
        if type(airline) == str:
            restrictions.append(f"IATA_code='{airline}'")
        if type(airline) == list:
            airline_str = ', '.join([f"'{a}'" for a in airline])
            restrictions.append(f"IATA_code IN ({airline_str})")
    if num:
        restrictions.append(f"flight_num={num}")
    if dept_time_from and dept_time_to:
        restrictions.append(f"Departure_time BETWEEN '{dept_time_from}' AND '{dept_time_to}'")
    elif dept_time_from:
        restrictions.append(f"Departure_time >= '{dept_time_from}'")
    elif dept_time_to:
        restrictions.append(f"Departure_time <= '{dept_time_to}'")
    
    if dept_city != "None" and dept_city:
        restrictions.append(f"Dept_Airport.City='{dept_city}'")
    if dept_ap != "None" and dept_city:
        restrictions.append(f"Departure_Airport='{dept_ap}'")
    if arri_city != "None" and dept_city:
        restrictions.append(f"Arri_Airport.City='{arri_city}'")
    if arri_ap != "None" and dept_city:
        restrictions.append(f"Arrival_Airport='{arri_ap}'")

    query = """SELECT flight_num, IATA_code, Departure_time, Arrival_time, price, status,
                        Departure_Airport, Dept_Airport.City AS Departure_city, 
                        Arrival_Airport, Arri_Airport.City AS Arrival_city, ticket_id,
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
                        NATURAL JOIN ticket NATURAL JOIN purchase"""

    if restrictions:
        query += "\nWHERE " + " AND ".join(restrictions)
    print(query)
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()

    data.sort(key=lambda x : x["Departure_time"])
    return data