from flask import Flask
from flask.templating import render_template

app = Flask(__name__)

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
  
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)