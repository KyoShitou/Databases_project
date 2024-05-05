import pymysql.cursors

conn = pymysql.connect(host="localhost", user="root", password="", db="Airplane_Management", charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor)


cursor = conn.cursor()
cursor.execute("SELECT customer_email, COUNT(ticket_id) FROM purchase GROUP BY customer_email ORDER BY COUNT(ticket_id) DESC LIMIT 1")
result = cursor.fetchall()
ticket_count = result[0]['COUNT(ticket_id)']
best_customer = result[0]['customer_email']
cursor.execute(f"SELECT * FROM customer WHERE email = '{best_customer}'")
result = cursor.fetchone()
print(f"Suggest customer account:\nEmail: {result['email']}\npassword: {result['password']}\nTicket_count: {ticket_count}\n\n")

cursor.execute("SELECT agent_email, COUNT(ticket_id) FROM purchase WHERE agent_email IS NOT NULL GROUP BY agent_email ORDER BY COUNT(ticket_id) DESC LIMIT 1")
result = cursor.fetchall()
ticket_count = result[0]['COUNT(ticket_id)']
best_agent = result[0]['agent_email']
cursor.execute(f"SELECT * FROM BookingAgent WHERE email = '{best_agent}'")
result = cursor.fetchone()
print(f"Suggest agent account:\nEmail: {result['email']}\npassword: {result['password']}\nTicket_count: {ticket_count}\n\n")