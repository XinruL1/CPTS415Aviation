from flask import Flask, render_template, url_for, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.Aviation
airports_collection = db.Airports

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/airports')
def airports():
  return render_template('airports.html')

@app.route('/airlines')
def airlines():
  return render_template('airlines.html')

@app.route('/aggregation')
def aggregation():
  return render_template('aggregation.html')

@app.route('/recommendation')
def recommendation():
  return render_template('recommendation.html')

@app.route('/search_airports', methods=['GET','POST'])
def search_airports():
  query = {}

  #read user inputs
  country = request.args.get('country')
  city = request.args.get('city')
  iata = request.args.get('iata-code')
  icao = request.args.get('icao-code')
  name = request.args.get('airport-name')

  #construct a query to filter based on all provided inputs
  query = {
    "Country": country,
    "City": city,
    "IATA": iata,
    "ICAO": icao,
    "Name": name
  }
  #drop keys with empty values
  query = {key:value for key, value in query.items() if value}

  #perform the query on the collection
  airport_data = list(airports_collection.find(query))
  return render_template('airportsinfo.html',airports = airport_data)
  
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)