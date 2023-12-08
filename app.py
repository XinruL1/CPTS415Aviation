from flask import Flask, render_template, url_for, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.Aviation
airports_collection = db.Airports
airlines_collection = db.Airlines
routes_collection = db.routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/airports')
def airports():
    return render_template('airports.html')

@app.route('/airlines')
def airlines():
    return render_template('airlines.html')

@app.route('/aggregation', methods=['GET'])
def aggregation():
    return render_template('aggregation.html')

@app.route('/top_countries_airports', methods=['GET'])
def top_countries_airports():
    pipeline = [
        {
            '$group': {
                '_id': '$Country',
                'count': { '$sum': 1 }
            }
        },
        { '$sort': { 'count': -1 } },
        { '$limit': 5 }
    ]

    result = list(airports_collection.aggregate(pipeline, maxTimeMS=60000, allowDiskUse=True))
    return render_template('aggregation_result.html', result=result, title='Countries with the highest number of airports')

@app.route('/cities_most_airlines', methods=['GET'])
def cities_most_airlines():
    pipeline = [
        {
            '$group': {
                '_id': '$City',
                'count': { '$sum': 1 }
            }
        },
        { '$sort': { 'count': -1 } },
        { '$limit': 5 }
    ]

    result = list(airports_collection.aggregate(pipeline, maxTimeMS=60000, allowDiskUse=True))
    return render_template('aggregation_result.html', result=result, title='Cities with the most incoming/outgoing airlines')


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
    query = {key: value for key, value in query.items() if value}

    #perform the query on the collection
    airport_data = list(airports_collection.find(query))
    return render_template('airportsinfo.html', airports=airport_data)

@app.route('/search_airlines', methods=['GET','POST'])
def search_airlines():
    query = {}

    country = request.args.get('country')
    iata = request.args.get('iata-code')
    icao = request.args.get('icao-code')
    name = request.args.get('airline-name')
    codeshare = request.args.get('codeshare')

    query = {
        "Country": country,
        "IATA": iata,
        "ICAO": icao,
        "Name": name,
        "Active": codeshare
    }
    #drop keys with empty values
    query = {key: value for key, value in query.items() if value}

    #perform the query on the collection
    airline_data = list(airlines_collection.find(query))
    return render_template('airlinesinfo.html', airlines=airline_data)

@app.route('/search_trip', methods=["GET","POST"])
def search_trip():
  source_country = request.args.get('source-country')
  source_city = request.args.get('source-city')
  source_airport = request.args.get('source-airport')
  destination_country = request.args.get('destination-country')
  destination_city = request.args.get('destination-city')
  destination_airport = request.args.get('destination-airport')
  airline_name = request.args.get('airline-name')
  stops = request.args.get('stops')

  pipline = [
    {
      "$lookup": {
        "from": "Airports",
        "localField": "Source_AirportID",
        "foreignField": "AirportID",
        "as": "source_airport_info"
      }
    },
    {
      "$unwind": "$source_airport_info"
    },
    {
      "$lookup": {
        "from": "Airports",
        "localField": "Destination_AirportID",
        "foreignField": "AirportID",
        "as": "destination_airport_info"
      }
    },
    {
      "$unwind":"$destination_airport_info"
    },
    {
      "$lookup": {
        "from": "Airlines",
        "localField": "AirlineID",
        "foreignField": "AirlineID",
        "as": "airline_info"
      }
    },
    {
      "$unwind": "$airline_info"
    },
    {
      "$project":{
        "SourceAirportCountry": "$source_airport_info.Country",
        "SourceAirportCity": "$source_airport_info.city",
        "SourceAirportName": "$source_airport_info.Name",
        "DestinationAirportCountry": "$destination_airport_info.Country",
        "DestinationAirportCity": "$destination_airport_info.City",
        "DestinationAirportName": "$destination_airport_info.Name",
        "AirlineName": "$airline_info.Name"
      }
    },
    {
      "$match": {
        "Stops":stops
      }
    }
  ]
  routes_data = list(routes_collection.aggregate(pipline))

  return render_template('tripinfo.html',trips = routes)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
