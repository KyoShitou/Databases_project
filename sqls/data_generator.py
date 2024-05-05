from faker import Faker
import pymysql.cursors
import datetime

conn = pymysql.connect(host="localhost", user="root", password="", db="Airplane_Management", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)

fake = Faker()

Airlines = ["AA", "AC", "AF", "AS", "B6", "BA", "CX", "DL", "EH",
 "EK", "EY", "KL", "LH", "MU", "NH", "QF", "QR", "SQ", "TK", "UA", "WN"]

def generate_airplane(airline):
    return f"INSERT INTO Airplane (IATA_code, seats) VALUES('{airline}', {fake.random_int(min=100, max=500)});\n"
    

def generate_Customer():
    email = fake.email()
    name = fake.name()
    password = fake.password()
    address = fake.address().split()[0]
    city = fake.city()
    state = fake.state()
    phone_number = fake.phone_number()
    passport_number = fake.random_int(min=100000000, max=999999999)
    passport_expiration = fake.date_between(start_date='today', end_date='+5y')
    passport_country = fake.country()
    dob = fake.date_of_birth(minimum_age=18, maximum_age=65)
    return f'INSERT INTO Customer VALUES("{email}", "{name}", "{password}", "{address}", "{city}", "{state}", "{phone_number}", "{passport_number}", "{passport_expiration}", "{passport_country}", "{dob}");\n'

cursor = conn.cursor()
cursor.execute(f"SELECT Airport_name FROM Airport")
airports = cursor.fetchall()
cursor.close()

airports = [airport["Airport_name"] for airport in airports]

def generate_flights(airports, airlines):
    # randomly select one from airlines
    airline = fake.random_element(airlines)
    # randomly select two from airports
    departure_airport = fake.random_element(airports)
    arrival_airport = fake.random_element(airports)
    # randomly select a departure time
    departure_time = fake.date_time_this_year(before_now=True, after_now=False)
    # randomly select an arrival time
    arrival_time = fake.date_time_between_dates(datetime_start=departure_time, datetime_end=departure_time + datetime.timedelta(days=1))

    # randomly select a price
    price = fake.random_int(min=100, max=500)

    cursor = conn.cursor()
    cursor.execute(f"SELECT Airplane_id FROM Airplane WHERE IATA_code = '{airline}'")
    airplane_id = cursor.fetchall()
    cursor.close()
    airplane_id = fake.random_element(airplane_id)["Airplane_id"]
    return f"""INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_airport, Arrival_airport)
    VALUES('{airline}', '{departure_time}', '{arrival_time}', {price}, 'Upcoming', {airplane_id}, '{departure_airport}', '{arrival_airport}');\n"""


def generate_Agent():
    email = fake.email()
    username = fake.user_name()
    password = fake.password()
    # select multiple airlines
    airlines = fake.random_elements(elements=Airlines, unique=True)

    querys = []
    querys.append(f"INSERT INTO BookingAgent (email, username, password) VALUES('{email}', '{username}', '{password}');\n")
    for airline in airlines:
        querys.append(f"INSERT INTO Agent_work_for VALUES('{email}', '{airline}');\n")
    return '\n'.join(querys)

def generate_staff():
    email = fake.email()
    username = fake.user_name()
    password = fake.password()
    firstname = fake.first_name()
    lastname = fake.last_name()
    dob = fake.date_of_birth(minimum_age=18, maximum_age=65)
    airline = fake.random_element(Airlines)
    Admin_perm = fake.random_element([0, 1])
    Oper_perm = fake.random_element([0, 1])

    return f"""INSERT INTO AirlineStaff VALUES('{username}', '{email}', '{password}', '{firstname}', '{lastname}', '{dob}', {Admin_perm}, {Oper_perm}, '{airline}');\n"""


def generate_tickets():
    cursor = conn.cursor()
    cursor.execute(f"SELECT email FROM Customer")
    customers = cursor.fetchall()
    cursor.execute(f"SELECT email FROM BookingAgent")
    agents = cursor.fetchall()
    cursor.execute(f"""SELECT flight_num, IATA_code
                        FROM flight""")
    flights = cursor.fetchall()
    cursor.close()

    f = open("tickets_and_purchase.sql", "w")
    for i in range(1, 6000):
        flight = fake.random_element(flights)
        customer = fake.random_element(customers)
        if fake.random_int(min=0, max=7) == 0:
            agent = "NULL"
        else:
            agent = f"'{fake.random_element(agents)['email']}'"
        f.write(f"INSERT INTO ticket VALUES ({i}, {flight['flight_num']}, '{flight['IATA_code']}');\n")
        f.write(f"INSERT INTO purchase VALUES ({i}, '{customer['email']}', {agent}, '{fake.date_this_year(before_today=True, after_today=False)}');\n")
    f.close()

def filling_seats():
    f = open("filling_seats.sql", "w")
    for i in range(134):
        f.write(f"INSERT INTO ticket VALUES ({i} + 6000, 13, 'AC');\n")
        f.write(f"INSERT INTO purchase VALUES ({i} + 6000, 'lopezcalvin@example.com', NULL, '2021-04-01');\n")
    f.close()

filling_seats()