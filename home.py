from flask import Flask, render_template, request, session, url_for, redirect, render_template_string, flash
import pymysql.cursors
from utils import *

def DisplayUpcomingFlight(conn):
    data = searchFlight(conn)
    
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
    
    if session['logged_in']:
        login_status = ["LOGGED IN", session['username'], session['user_type']]
    else:
        login_status = ["NOT LOGGED IN"]
    

    return "<h1>hello</h1>"
    return render_template("home_alt.html", flights=data
                           , login_status=login_status, city_lst=city_lst, airport_lst=airport_lst)
