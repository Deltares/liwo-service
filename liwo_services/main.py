import json
import logging
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker

from flask_sqlalchemy import SQLAlchemy

# side effect loads the env
import settings

logger = logging.getLogger(__name__)

def create_app_db():
    """load the dot env values"""
    # Create the application instance
    settings.load_env()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
    logger.info("loaded database %s", app.config['SQLALCHEMY_DATABASE_URI'])
    db = SQLAlchemy(app)
    CORS(app)
    return app, db


app, db = create_app_db()

# Create a URL route in our application for "/"
@app.route('/')
def home():
    """
    This function just responds to the browser ULR
    localhost:5000/

    :return:        the rendered template 'home.html'
    """
    return 'liwo_service'


@app.route('/liwo.ws/Authentication.asmx/Login', methods=["OPTIONS", "POST"])
def loadLayerSets():
    """
    returns maplayersets. Login is not used anymore, but frontend still expects this.
    frontend will send body {
    username: 'anonymous@rws.nl',
    password: '',
    mode: ''}

    TODO: remove Login part and only return json generated by postgresql function
    """


    rs = db.session.execute('SELECT website.sp_selectjson_maplayersets_groupedby_mapcategories()')

    result = rs.fetchall()

    layersets_dict = {
        "mode": "open",
        "layersets": result[0][0],
        "loggedIn": False,
        "liwokey": "-1",
        "error": "",
        "user": {
            "email": "",
            "message": "",
            "role": "Guest",
            "name": "",
            "organisation": "",
            "tools": [],
            "mymaps": [],
            "mapextent": "",
            "webserviceURL": os.environ['WEBSERVICE_URL'],
            "administrator": "false"
        }
    }

    layersets_string = json.dumps(layersets_dict)

    return {"d": layersets_string}

@app.route('/liwo.ws/Tools/FloodImage.asmx/GetScenariosPerBreachGeneric', methods=["POST"])
def loadBreachLayer():
    """
    Return Scenarios for a breachlocation.

    body: {
      breachid: breachId,
      layername: layerName
    })

     Based on layername a setname is defined.
     In the database function this is directly converted back to the layername.
     TODO: remove setname directly use layerName.
    """

    body = request.get_json()

    # Setnames according to c-sharp backend
    setnames = {
        "waterdiepte": "Waterdiepte_flood_scenario_set",
        "stroomsnelheid": "Stroomsnelheid_flood_scenario_set",
        "stijgsnelheid": "Stijgsnelheid_flood_scenario_set",
        "schade": "Schade_flood_scenario_set",
        "slachtoffers": "Slachtoffers_flood_scenario_set",
        "getroffenen": "Getroffenen_flood_scenario_set",
        "aankomsttijd": "Aankomsttijd_flood_scenario_set"
    }

    # Default value for setname
    default_setname = "Waterdiepte_flood_scenario_set"
    setname = setnames.get(body['layername'], default_setname)
    breachid = body['breachid']


    # TODO: parameters in query parameters
    query = "SELECT website.sp_selectjson_maplayerset_floodscen_breachlocation_id_generic({}, '{}')".format(breachid, setname)

    rs = db.session.execute(query)
    result = rs.fetchall()
    return {"d": json.dumps(result[0][0])}


@app.route('/liwo.ws/Maps.asmx/GetLayerSet', methods=["POST"])
def loadLayerSetById():
    """
    body: { id }
    """
    body = request.get_json()
    id = body['id']

    # TODO: use params option in execute.
    query = "SELECT website.sp_selectjson_layerset_layerset_id({})".format(id)

    rs = db.session.execute(query)
    result = rs.fetchall()
    return {"d": json.dumps(result[0][0])}

@app.route('/liwo.ws/Maps.asmx/GetBreachLocationId', methods=["POST"])
def getFeatureIdByScenarioId():
    """
    body:{ mapid: scenarioId }
    """
    body = request.get_json()
    floodsimulationid = body['floodsimulationid']

    # TODO: use params option in execute
    query = "SELECT static_information.sp_selectjson_breachlocationid({})".format(floodsimulationid)

    rs = db.session.execute(query)
    result = rs.fetchall()

    return {"d": json.dumps(result[0][0])}

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80, threaded=True)

