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
        ret = retrieve_flights(conn, airline=airline["IATA_code"])
        for f in ret:
            cursor.execute(f"""SELECT customer.name as name
                           FROM flight NATURAL JOIN ticket NATURAL JOIN purchase JOIN customer ON purchase.customer_email = customer.email
                            WHERE flight_num={f["flight_num"]} AND IATA_code='{f["IATA_code"]}'    """)
            passengers_ = cursor.fetchall()
            passengers = []
            for p in passengers_:
                passengers.append(p["name"])
            f["passengers"] = passengers
        
    cursor.close()
    return ret