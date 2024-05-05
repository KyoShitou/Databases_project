CREATE TABLE Airline (
    Airline_name    VARCHAR(50) NOT NULL,
    IATA_code       VARCHAR(50) NOT NULL,
    PRIMARY KEY (IATA_code)
);

CREATE TABLE Airplane (
    Airplane_id  INT AUTO_INCREMENT NOT NULL,
    IATA_code    VARCHAR(50) NOT NULL,
    seats           INT,
    PRIMARY KEY (Airplane_id),
    FOREIGN KEY (IATA_code) REFERENCES Airline(IATA_code)
        ON DELETE CASCADE
);

CREATE TABLE AirlineStaff (
    aStaff_username VARCHAR(50) NOT NULL,
    email           VARCHAR(50) NOT NULL,
    password        VARCHAR(50) NOT NULL,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    date_of_birth   DATE,
    Admin_perm      BOOLEAN NOT NULL,
    Oper_perm       BOOLEAN NOT NULL,
    IATA_code    VARCHAR(50) NOT NULL,
    PRIMARY KEY (email),
    FOREIGN KEY (IATA_code) REFERENCES Airline(IATA_code)
);

CREATE TABLE Airport (
    Airport_name    VARCHAR(50) NOT NULL,
    City            VARCHAR(50) NOT NULL,
    PRIMARY KEY (Airport_name)
);

CREATE TABLE flight(
    flight_num      INT NOT NULL,
    IATA_code       VARCHAR(50) NOT NULL,
    Departure_time  DATETIME NOT NULL,
    Arrival_time    DATETIME NOT NULL,
    price           NUMERIC(10, 2) NOT NULL,
    status          VARCHAR(50) NOT NULL,
    Airplane_id     INT NOT NULL,
    Departure_Airport     VARCHAR(50) NOT NULL,
    Arrival_Airport       VARCHAR(50) NOT NULL,
    PRIMARY KEY (flight_num, IATA_code),
    FOREIGN KEY (IATA_code) REFERENCES Airline(IATA_code)
        ON DELETE CASCADE,
    FOREIGN KEY (Airplane_id) REFERENCES Airplane(Airplane_id),
    FOREIGN KEY (Departure_Airport) REFERENCES Airport(Airport_name)
        ON DELETE CASCADE,
    FOREIGN KEY (Arrival_Airport) REFERENCES Airport(Airport_name)
        ON DELETE CASCADE
);



CREATE TABLE ticket(
    ticket_id INT AUTO_INCREMENT NOT NULL,
    flight_num INT NOT NULL,
    IATA_code VARCHAR(50) NOT NULL,
    PRIMARY KEY (ticket_id),
    FOREIGN KEY (flight_num, IATA_code) REFERENCES flight(flight_num, IATA_code)
        ON DELETE CASCADE
);


CREATE TABLE Customer (
    email       VARCHAR(50) NOT NULL,
    name        VARCHAR(50) NOT NULL,
    password    VARCHAR(50) NOT NULL,
    address        VARCHAR(50),
    city           VARCHAR(50),
    state          VARCHAR(50),
    phone_number   VARCHAR(50),
    passport_number VARCHAR(50),
    passport_expiration DATE,
    passport_country VARCHAR(50),
    date_of_birth   DATE,
    PRIMARY KEY (email)
);

CREATE TABLE BookingAgent(
    email      VARCHAR(50) NOT NULL,
    username   VARCHAR(50) NOT NULL,
    password   VARCHAR(50) NOT NULL,
    booking_agent_id INT,
    PRIMARY KEY (email)
);

CREATE TABLE purchase(
    ticket_id       INT NOT NULL,
    customer_email  VARCHAR(50) NOT NULL,
    agent_email     VARCHAR(50),
    date            DATE NOT NULL,
    PRIMARY KEY (ticket_id, customer_email),
    FOREIGN KEY (customer_email) REFERENCES Customer(email),
    FOREIGN KEY (agent_email) REFERENCES BookingAgent(email),
    FOREIGN KEY (ticket_id) REFERENCES ticket(ticket_id)
);

CREATE TABLE Agent_work_for(
    agent_email VARCHAR(50) NOT NULL,
    IATA_code VARCHAR(50) NOT NULL,
    PRIMARY KEY (agent_email, IATA_code),
    FOREIGN KEY (agent_email) REFERENCES BookingAgent(email),
    FOREIGN KEY (IATA_code) REFERENCES Airline(IATA_code)
);


DELIMITER //
CREATE TRIGGER auto_flight_num BEFORE INSERT ON flight
FOR EACH ROW
BEGIN
    DECLARE auto_flight_num INT;
    SET auto_flight_num = (SELECT MAX(flight_num) FROM flight WHERE IATA_code = NEW.IATA_code);
    IF auto_flight_num IS NULL THEN
        SET auto_flight_num = 0;
    END IF;
    SET NEW.flight_num = auto_flight_num + 1;
END;//
DELIMITER ;