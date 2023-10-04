# Import the dependencies.
import pandas as pd
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
base = automap_base()

# reflect the tables
base.prepare(engine, reflect=True)

# Save references to each table
measurement = base.classes.measurement
station = base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Helper Functions
#################################################

# This function queries the database and finds the date exactly 1 year before the latest observation data
def get_previous_year(): 
    most_recent_data = session.execute("SELECT MAX(date) FROM measurement").fetchone()
    most_recent_date = dict(most_recent_data)['MAX(date)']
    return  dt.datetime.strptime(most_recent_date, '%Y-%m-%d').date() - dt.timedelta(days=365)

# Get previous year date

#################################################
# Flask Routes
#################################################

# Home page route, will display a list of possible routes available via the api.
@app.route("/")
def welcome():
	return(
        f"This application will display climate analysis for Hawaii to help your perfect trip<br/>"
        f"Available Analysis:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/temp/start/end<br/>"
	)

# This route will return date and precipitation data for the last 12 months
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Get previous year
    prev_year = get_previous_year()

    # Query for the dates and prcp observations from the last year.
    date_precipitation_query = session.query(measurement.date, measurement.prcp).filter(measurement.date >= prev_year).all()

    precipitation_data = {}
    for data in date_precipitation_query:
       date, precipitation = data # get date and precipitation
       precipitation_data[date] = precipitation # add to dictionary

    return jsonify(precipitation_data)

# This route will return a list of all stations
@app.route("/api/v1.0/stations")
def stations():
    # Get all station information
    station_query = session.query(station.station, station.name).all()
    stations = list(map(lambda station: {"ID": station[0], "Name": station[1]}, station_query ))
    return jsonify(stations)

# This route will return date and temperature data from the last year
@app.route("/api/v1.0/tobs")
def tobs():
    # Get previous year
    prev_year = get_previous_year()

    # Get most acitve station
    most_active_station_id = session.query(measurement.station, func.count(measurement.station)).group_by(measurement.station).order_by(func.count(measurement.station).desc()).all()[0][0]    

    # Query for the dates and prcp observations from the last year.
    twelve_month_temperature_query = session.query(measurement.date, measurement.tobs).filter(measurement.date >= prev_year, measurement.station == most_active_station_id ).all()
    
    temperature_data = {}
    for data in twelve_month_temperature_query:
       date, temperature  = data # get date and temperature
       temperature_data[date] = temperature
    return jsonify(temperature_data)

#This route will return a list of the minimum temperature, the average temperature, and the maximum temperature for a specified start date
@app.route("/api/v1.0/<start>")
def tstart(start):
    # get minimum temperature, the average temperature, and the maximum temperature for a specified start date
    start_date_query = session.query(
        func.min(measurement.tobs),
        func.avg(measurement.tobs),
        func.max(measurement.tobs)
    ).filter(measurement.date >= start).all()

    # Extract data    
    min_temp, avg_temp, max_temp = start_date_query[0]

    # Write response
    temp_analysis = {
        "Start Date": start,
        "Minimum Temperature": min_temp,
        "Average Temperature": avg_temp,
        "Max Temperature": max_temp
    }
    return jsonify(temp_analysis)

##This route will return a list of the minimum temperature, the average temperature, and the maximum temperature for a specified start and end date
@app.route("/api/v1.0/<start>/<end>")
def tstartend(start,end):         
    # minimum temperature, the average temperature, and the maximum temperature for a specified start and end date
    start_end_date_query = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).filter(measurement.date.between(start, end)).order_by(measurement.date.desc()).all()
    
    # Extract data    
    min_temp, avg_temp, max_temp = start_end_date_query[0]

    # Write response
    temp_analysis = {
        "Date": f"{start} to ${end}",
        "Minimum Temperature": min_temp,
        "Average Temperature": avg_temp,
        "Max Temperature": max_temp
    }   
    return jsonify(temp_analysis)

if __name__ == '__main__':
    app.run(debug=True)