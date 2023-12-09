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

@app.route('/recommendation', methods=['GET'])
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

  query = {
    "SourceCountry": source_country,
    "SourceCity": source_city,
    "SourceAirport": source_airport,
    "DestinationCountry": destination_country,
    "DestinationCity": destination_city,
    "DestinationAirport": destination_airport,
    "AirlineName": airline_name,
    "Stops": stops
  }

  #drop keys with empty values
  query = {key: value for key, value in query.items() if value}

  pipeline = [
    
    {"$lookup": {
        "from": "Airports",
        "localField": "Source_AirportID",
        "foreignField": "AirportID",
        "as": "sourceAirport"
    }},
    {"$lookup": {
        "from": "Airports",
        "localField": "Destination_AirportID",
        "foreignField": "AirportID",
        "as": "destinationAirport"
    }},
    {"$lookup": {
        "from": "Airlines",
        "localField": "AirlineID",
        "foreignField": "AirlineID",
        "as": "airline"
    }},
    {"$unwind": "$sourceAirport"},
    {"$unwind": "$destinationAirport"},
    {"$unwind": "$airline"},
    {"$project": {
        "SourceCountry": "$sourceAirport.Country",
        "SourceCity": "$sourceAirport.City",
        "SourceAirport": "$sourceAirport.Name",
        "DestinationCountry": "$destinationAirport.Country",
        "DestinationCity": "$destinationAirport.City",
        "DestinationAirport": "$destinationAirport.Name",
        "AirlineName": "$airline.Name",
        "Stops": "$Stops"
    }},
    {"$match": query}
  ]

  # Execute the aggregation pipeline
  routes_data = list(db.routes.aggregate(pipeline))

  return render_template('tripinfo.html',trips = routes_data)

"""
  # emits key-value pairs based on specific fields from the documents in the routes collection,
  # where '_id' is the key of each document, and the value is an object containing 'sourceAirportID', 'destinationAirportID', 'airlineID', and 'stops'.
  # using triple quotes to embed JavaScript code directly into the python code
  mapper = '''
    function () {

      emit(this._id, {
        // assigning the value of source_airportID from the document to the key sourceAirportID in the emitted object
        sourceAirportID : this.Source_AirportID,
        destinationAirportID : this.Destination_AirportID,
        airlineID : this.AirlineID,
        stops : this.Stops

      });
    }
  '''

  # aggregating values associated with a specific key emitted by the mapper
  reducer = '''
    function(key, values){
      var result = {
        SourceCountry: null,
        SourceCity: null,
        SourceAirport: null,
        DestinationCountry: null,
        DestinationCity: null,
        DestinationAirport: null,
        AirlineName: null,
        Stops: null
      };

      values.forEach(function (value) {
        // retrieve airport and airline infoprmation based on IDs
        var sourceAirport = scope.Airports.findOne({ AirportID: value.sourceAirportID });
        var destinationAirport = scope.Airports.findOne({ AirportID: value.destinationAirportID });
        var airline = scope.Airlines.findOne({ AirlineID: value.airlineID});

        // if all three entities exist in their respective collections, 
        // then valid information is retrieved from the database for the associated IDs
        if (sourceAirport && destinationAirport && airline){
          // check conditions based on user input
          if (
            (!source_country || sourceAirport.Country === source_country) &&
            (!source_city || sourceAirport.City === source_city) &&
            (!source_airport || sourceAirport.Name === source_airport) &&
            (!destination_country || destinationAirport.Country === destination_country) &&
            (!destination_city || destinationAirport.City === destination_city) &&
            (!destination_airport || destinationAirport.Name === destination_airport) &&
            (!airline_name || airline.Name === airline_name) &&
            (!stops || value.stops === stops)
          ) {
            result.SourceCountry = sourceAirport.Country;
            result.SourceCity = sourceAirport.City;
            result.SourceAirport = sourceAirport.Name;
            result.DestinationCountry = destinationAirport.Country;
            result.DestinationCity = destinationAirport.City;
            result.DestinationAirport = destinationAirport.Name;
            result.AirlineName = airline.Name;
            result.Stops = value.stops;
          }
        }
      });
      return result;
    }
  '''

  # Define the scope
  scope = {
    'Airports': db.Airports,
    'Airlines': db.Airlines
  }

  # Run the map-reduce operation with the scope parameter
  result = db.routes.mapReduce(mapper, reducer, "trip_collection", scope=scope)

  # Retrieve the results from the "trip_collection"
  routes_data = list(db.trip_collection.find())
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
