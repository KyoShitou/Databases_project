INSERT INTO Airline VALUES("China Eastern", "MU");
INSERT INTO Airline VALUES("All Nippon Airways", "NH");
INSERT INTO Airline VALUES("American Airlines", "AA");
INSERT INTO Airline VALUES("Delta Air Lines", "DL");
INSERT INTO Airline VALUES("United Airlines", "UA");
INSERT INTO Airline VALUES("Emirates", "EK");
INSERT INTO Airline VALUES("Qatar Airways", "QR");
INSERT INTO Airline VALUES("Singapore Airlines", "SQ");
INSERT INTO Airline VALUES("Cathay Pacific", "CX");
INSERT INTO Airline VALUES("British Airways", "BA");
INSERT INTO Airline VALUES("Lufthansa", "LH");
INSERT INTO Airline VALUES("Air France", "AF");
INSERT INTO Airline VALUES("KLM Royal Dutch Airlines", "KL");
INSERT INTO Airline VALUES("Turkish Airlines", "TK");
INSERT INTO Airline VALUES("Air Canada", "AC");
INSERT INTO Airline VALUES("Qantas", "QF");
INSERT INTO Airline VALUES("Southwest Airlines", "WN");
INSERT INTO Airline VALUES("JetBlue Airways", "B6");
INSERT INTO Airline VALUES("ANA Wings", "EH");
INSERT INTO Airline VALUES("Alaska Airlines", "AS");
INSERT INTO Airline VALUES("Etihad Airways", "EY");


INSERT INTO Airport VALUES("JFK", "New York");
INSERT INTO Airport VALUES("PVG", "Shanghai");
INSERT INTO Airport VALUES("LAX", "Los Angeles");
INSERT INTO Airport VALUES("LHR", "London");
INSERT INTO Airport VALUES("CDG", "Paris");
INSERT INTO Airport VALUES("SIN", "Singapore");
INSERT INTO Airport VALUES("HND", "Tokyo");
INSERT INTO Airport VALUES("SYD", "Sydney");
INSERT INTO Airport VALUES("PEK", "Beijing");
INSERT INTO Airport VALUES("DXB", "Dubai");
INSERT INTO Airport VALUES("IST", "Istanbul");
INSERT INTO Airport VALUES("ATL", "Atlanta");
INSERT INTO Airport VALUES("ORD", "Chicago");
INSERT INTO Airport VALUES("DFW", "Dallas");
INSERT INTO Airport VALUES("DEN", "Denver");
INSERT INTO Airport VALUES("AMS", "Amsterdam");
INSERT INTO Airport VALUES("FRA", "Frankfurt");
INSERT INTO Airport VALUES("MUC", "Munich");
INSERT INTO Airport VALUES("MAD", "Madrid");
INSERT INTO Airport VALUES("BCN", "Barcelona");
INSERT INTO Airport VALUES("FCO", "Rome");
INSERT INTO Airport VALUES("MXP", "Milan");
INSERT INTO Airport VALUES("NRT", "Tokyo");
INSERT INTO Airport VALUES("ICN", "Seoul");
INSERT INTO Airport VALUES("HKG", "Hong Kong");
INSERT INTO Airport VALUES("SFO", "San Francisco");
INSERT INTO Airport VALUES("SEA", "Seattle");
INSERT INTO Airport VALUES("YYZ", "Toronto");
INSERT INTO Airport VALUES("YVR", "Vancouver");



INSERT INTO Customer VALUES("rc@nyu.edu", "Romaine Corcolle", "rc", 1150, "Century Ave.", "Paris", "France", 00000000, 00000000, "2099-12-31", "France", "1900-01-01");
INSERT INTO Customer VALUES("pm@nyu.edu", "Paul Mellies", "pm", 888, "Yangsi Rd.", "Paris", "France", 00000000, 00000000, "2099-12-31", "France", "1900-01-01");
INSERT INTO Airplane (IATA_code, seats) VALUES("MU", 355);
INSERT INTO Airplane (IATA_code, seats) VALUES("MU", 400);
INSERT INTO Airplane (IATA_code, seats) VALUES("NH", 300);
INSERT INTO Airplane (IATA_code, seats) VALUES("AA", 400);
INSERT INTO BookingAgent VALUES("Agt@Agt.com", "agt" , 0);
INSERT INTO AirlineStaff VALUES("staff", "staff", "airline", "staff", "1800-01-01", FALSE, FALSE, "MU");


INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_Airport, Arrival_Airport)
    VALUES("MU", "2024-03-01 00:00:00", "2024-03-02 00:00:00", 1000, "upcoming", 1, "JFK", "PVG");
INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_Airport, Arrival_Airport)
    VALUES("MU", "2024-03-02 00:00:00", "2024-03-03 00:00:00", 2000, "in-progress", 1, "JFK", "PVG");
INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_Airport, Arrival_Airport)
    VALUES("MU", "2024-03-03 00:00:00", "2024-03-04 00:00:00", 1000, "delayed", 1, "JFK", "PVG");

INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_Airport, Arrival_Airport)
    VALUES("MU", "2024-03-01 00:00:00", "2024-03-02 00:00:00", 1000, "upcoming", 2, "PVG", "HND");

INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_Airport, Arrival_Airport)
    VALUES("NH", "2024-03-01 00:00:00", "2024-03-02 00:00:00", 1000, "upcoming", 3, "HND", "PVG");

INSERT INTO flight (IATA_code, Departure_time, Arrival_time, price, status, Airplane_id, Departure_Airport, Arrival_Airport)
    VALUES("AA", "2024-03-01 00:00:00", "2024-03-02 00:00:00", 1000, "upcoming", 4, "LAX", "JFK");


INSERT INTO ticket (flight_num, IATA_code) VALUES(1, "MU");
INSERT INTO ticket (flight_num, IATA_code) VALUES(1, "MU");
INSERT INTO purchase VALUES(1, "rc@nyu.edu", "Agt@Agt.com", "2024-02-28");
INSERT INTO purchase VALUES(2, "pm@nyu.edu", NULL, "2024-02-28");