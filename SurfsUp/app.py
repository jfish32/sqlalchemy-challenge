# Import the dependencies.
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime as dt
import numpy as np
import pandas as pd
import json


#################################################
# Database Setup
#################################################
engine = create_engine(f"sqlite:///resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine,reflect=True)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station
# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
###homepage and show available places to go
@app.route('/')
def home():
    """This is homepage.  Here are the available routes below"""
    return(
        f"Homepage<br/>"
        f"<br/>Available paths:<br/>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a><br/>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a><br/>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a><br/>"
        f"<br/><br/>Enter date ranges below (YYYY-MM-DD):<br/>"
        f"(2010-01-01 to 2017-08-23)<br/><br/>"
        f"<br/>/api/v1.0/start-date<br/>"
        f"/api/v1.0/start-date/end-date"
        f"<br/><br/><br />Example:<br/>"
        f"<a href='/api/v1.0/2012-06-12'>/api/v1.0/2012-06-12</a><br/>"
        f"<a href='/api/v1.0/2012-06-12/2016-05-18'>/api/v1.0/2012-06-12/2016-05-18/</a><br/>"
    )

#2
###convert results from last 12 months into a dictionary: date as the key and prcp as the value
@app.route("/api/v1.0/precipitation")
def precipitation():
    #create link from python to the database
    session= Session(engine)

    #precipitation
    results = session.query(measurement.date,measurement.prcp).all()

    session.close()

    #creating dictionary from the data in the rows and adding to list
    prcp_list = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict['date']=date
        prcp_dict['precipitation'] = prcp
        prcp_list.append(prcp_dict)

    #Jsonify list
    return jsonify(prcp_list)

#3
#return a JSON list of stations from dataset
@app.route('/api/v1.0/stations')
def stations():
    #session link
    session = Session(engine)

    #query
    stations = session.query(station.id,station.station,station.name).all()

    session.close()

    all_stations = list(np.ravel(stations))

    #Jsonify
    return jsonify(all_stations)

#4
#Query date and temps of most active station for previous year and return JSON list
@app.route('/api/v1.0/tobs')
def tobs():
    session = Session(engine)

    most_active = session.query(measurement.station,func.count(measurement.station)).group_by(measurement.station)\
        .order_by(func.count(measurement.station).desc()).first()
    
    active_station = most_active[0]

    #query to grab last 12 months of prcp data to plot
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first().date

    #get the date one year previous to last date
    last_year = dt.datetime.strptime(last_date,'%Y-%m-%d')-dt.timedelta(days=365)

    tobs = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station==active_station).\
        filter(measurement.date >= last_year).\
        order_by(measurement.date).all()

    session.close()

    # create list comprehension for date, temperature
    temp_date = [result[0] for result in tobs]
    temp_data = [result[1] for result in tobs]

    # place data in pd.DataFrame 
    temp_df = pd.DataFrame({
            "Date": temp_date, 
            "Temperature": temp_data})

    # load dataframe as JSON 
    temp_df = json.loads(temp_df.to_json(orient='records'))

    # return dictionary with key containing each date, temperature data in JSON 
    return jsonify(temp_df)

#5
#Return JSON list of min, avg, and max temp for a specified start or start-end range
#For a specified start calculate TMIN, TAVG, and TMAX for all dates greater than or equal to start
#For specified start and end date calculate TMIN, TAVG and TMAX for the dates from the start to end date

@app.route("/api/v1.0/<start>")
def start(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # create a query to list all dates from Measurement
    dates = session.query(measurement.date)
    
    session.close()
    
    date_list =[date[0] for date in dates]

    # check if start date in date_list 
    if start in date_list:

        # perform calculation using query 
        results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).all()

        # create empty list to store results
        result_calculations = []

        # create dictionary for results
        for min, avg, max in results:
            calculation_start = {}
            calculation_start["Minimum Temperature"] = min
            calculation_start["Avg Temperature"] = avg
            calculation_start["Max Temperature"] = max
            result_calculations.append(calculation_start)
        
        # return results in JSON
        return jsonify(result_calculations)

    # return error message if start date not in dates database
    else:
        return jsonify({"error": f"Start Date on {start} not found."}), 404


#5 part 2
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # create query to list all dates from Measurement
    dates = session.query(measurement.date)
    date_list =[date[0] for date in dates]

    # check if start and end date in date_list 
    if start in date_list and end in date_list:

        # perform calculation 
        results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
            filter(measurement.date >= start).\
            filter(measurement.date <= end).all()

        # create empty list to store results
        final_calculations = []

        # create dictionary for results
        for min, avg, max in results:
            calculation_dict = {}
            calculation_dict["Minimum Temperature"] = min
            calculation_dict["Avg Temperature"] = avg
            calculation_dict["Max Temperature"] = max
            final_calculations.append(calculation_dict)

            # return results in JSON
            return jsonify(final_calculations)
    
    # return an error message if start date or end date are not in the dates database
    else: 
        return jsonify({"error": f"Start Date on {start} or End Date {end} not found."}), 404 


if __name__ == '__main__':
    app.run(debug=True)