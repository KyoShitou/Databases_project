import matplotlib.pyplot as plt
import datetime
import os
from copy import deepcopy



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
            restrictions.append(f"IATA_code IN {tuple(airline)}")
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

    return data

def retrieve_flights_with_passengers(conn, agent=None, staff=None, customer=None, date_from=None, date_to=None):
    cursor = conn.cursor()
    if (agent == None) and (staff == None) and (customer == None):
        return None
    if customer:
        cursor.execute(f"""SELECT flight_num, IATA_code
                       FROM ticket
                       WHERE ticket_id IN (
                            SELECT ticket_id
                            FROM purchase
                            WHERE customer_email='{customer}'
                       )""")
        result = cursor.fetchall()
        ret = []
        for f in result:
            t = retrieve_flights(conn, num=f["flight_num"], airline=f["IATA_code"], dept_time_from=date_from, dept_time_to=date_to)
            if len(t) != 0:
                ret.append(t[0])
            else:
                continue
        
    if agent:
        cursor.execute(f"""SELECT flight_num, IATA_code
                       FROM ticket 
                       WHERE ticket_id IN (
                            SELECT ticket_id
                            FROM purchase
                            WHERE agent_email='{agent}'
                       )""")
        result = cursor.fetchall()
        print(result)
        ret = []
        for f in result:
            ret.append(retrieve_flights(conn, num=f["flight_num"], airline=f["IATA_code"], dept_time_from=date_from, dept_time_to=date_to)[0])
            cursor.execute(f"""SELECT customer.name as name
                           FROM flight NATURAL JOIN ticket NATURAL JOIN purchase JOIN customer ON purchase.customer_email = customer.email
                            WHERE flight_num={f["flight_num"]} AND IATA_code='{f["IATA_code"]}' AND agent_email='{agent}'   """)
            passengers_ = cursor.fetchall()
            passengers = []
            for p in passengers_:
                passengers.append(p["name"])
            passengers = ', '.join(passengers)
            ret[-1]["passengers"] = passengers
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