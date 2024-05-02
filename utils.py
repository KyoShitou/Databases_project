
def searchFlight(conn,
        dept_city=None, dept_apt=None, arrival_city=None, arrival_ap=None, date=None):
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