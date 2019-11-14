from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import logging as logger
from datetime import datetime
import json

logger.basicConfig(level="DEBUG")
app = Flask(__name__)


@app.route('/api')
def hello_world():
    return jsonify({'msg': "Hello World!!!"})


# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://teleuser:tele1!!qwer!Q@192.168.10.100/betbrightflask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)


# Match Class/Model
class Match(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(200))
    url = db.Column(db.String(200))
    startTime = db.Column(db.DateTime)
    sport = db.Column(db.JSON)
    sport_id = db.Column(db.BigInteger)
    market = db.Column(db.JSON)
    market_id = db.Column(db.BigInteger)
    created = db.Column(db.DateTime)

    def __init__(self, id, name, url, startTime, sport, market):
        self.id = id
        self.name = name
        self.url = url
        self.startTime = startTime
        self.sport = sport
        self.sport_id = sport['id']
        self.market = market
        self.market_id = market['id']
        self.created = datetime.now()


# Match Schema
class MatchSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'url', 'startTime', 'sport', 'sport_id', 'market', 'market_id', 'created')


# Part Match Schema
class PartMatchSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'url', 'startTime')


# Sport Class/Model
class Sport(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(40))

    def __init__(self, id, name):
        self.id = id
        self.name = name


class SportSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name')


# Market Class/Model
class Market(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(40))
    selections = db.Column(db.JSON)
    created = db.Column(db.DateTime)

    def __init__(self, id, name, selections):
        self.id = id
        self.name = name
        self.selections = selections
        self.created = datetime.now()


# Market Schema
class MarketSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'selections', 'created')


# Selections Class/Model
class Selections(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(40))
    odds = db.Column(db.Float)
    market_id = db.Column(db.BigInteger)
    created = db.Column(db.DateTime)
    last_modified = db.Column(db.DateTime)

    def __init__(self, id, name, odds, market_id):
        self.id = id
        self.name = name
        self.odds = odds
        self.market_id = market_id
        self.created = datetime.now()
        self.last_modified = datetime.now()


# Selections Schema
class SelectionsSchema(ma.Schema):
    class Meta:
        field = ('id', 'name', 'odds', 'market_id', 'created', 'last_modified')


# Message Class/Model
class Message(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    type = db.Column(db.String(20))
    eventId = db.Column(db.BigInteger)
    created = db.Column(db.DateTime)

    def __init__(self, id, type, eventId):
        self.id = id
        self.type = type
        self.eventId = eventId
        self.created = datetime.now()


# Message Schema
class MessageSchema(ma.Schema):
    class Meta:
        field = ('id', 'type', 'eventId', 'created')


# Before running the following code, initialize DB with several above tables first
# >>> from app import db
# >>> db.create_all()

# Init schema (Important!!!)
match_schema = MatchSchema()
matches_schema = MatchSchema(many=True)

sport_schema = SportSchema()
sports_schema = SportSchema(many=True)

market_schema = MarketSchema()
markets_schema = MarketSchema(many=True)

selections_schema = SelectionsSchema(many=True)

message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)


# Get all match
@app.route('/api/match/all', methods=['GET'])
def get_matches():
    all_matches = Match.query.all()
    result = matches_schema.dump(all_matches)
    return matches_schema.jsonify(result)


# Retrieve matches by filter conditions
@app.route("/api/match/", methods=['GET'])
def retrieve_match():
    sport_name = request.args.get('sport', None)
    ordering = request.args.get("ordering", None)
    name = request.args.get("name", None)
    part_matches_schema = PartMatchSchema(many=True)
    print(sport_name)
    if sport_name is not None and ordering is not None:
        sport = Sport.query.filter_by(name=sport_name)[0]
        print("sport:{}".format(sport))
        matches = Match.query.filter_by(sport_id=sport.id).order_by(ordering)
    elif name is not None:
        matches = Match.query.filter_by(name=name)
    else:
        matches = []
    return part_matches_schema.jsonify(part_matches_schema.dump(matches))


# Get one match
@app.route("/api/match/<id>", methods=['GET'])
def get_match(id):
    match = match_schema.dump(Match.query.get(id))
    match_body = {
        'id': match['id'],
        'url': match['url'],
        'name': match['name'],
        'startTime': match['startTime'],
        'sport': match['sport'],
        'markets': match['market']
    }
    if len(match) == 0:
        return "ID not found", 404
    else:
        return jsonify(match_body)


# Update Event
@app.route('/api/match/message', methods=['GET', 'PUT'])
def update_event():
    try:
        message_id = request.json['id']
        message_type = request.json['message_type']
        event = request.json['event']
    except KeyError as e:
        return {'Error': "{} is not provided".format(e)}, 500
    if message_type != 'UpdateOdds':
        return {'Error': "Wrong message type: {}".format(message_type)}, 500
    try:
        event_id = event['id']
        event_name = event['name']
        startTime = event['startTime']
        sport = event['sport']
        market = event['markets'][0]

        sport_id = sport['id']
        sport_name = sport['name']

        market_id = market['id']
        market_name = market['name']
        selections = market['selections']

    except Exception as e:
        return {'Error: {}'.format(str(e))}, 500

    try:
        # update selections
        for selection in selections:
            selection_obj = db.session.query(Selections).filter_by(id=selection['id'], market_id=market_id)[0]
            print("selection_obj: {}".format(selection_obj))
            selection_obj.odds = selection['odds']
            selection_obj.last_modified = datetime.now()
            db.session.commit()

        # update market
        market_obj = Market.query.filter_by(id=market_id)[0]
        market_obj.selections = selections
        db.session.commit()

        # update match
        match_obj = Match.query.filter_by(id=event_id)[0]
        match_obj.sport = sport
        match_obj.market = market
        db.session.commit()
    except Exception as e:
        return {"error": str(e)}, 500

    return jsonify({"id": message_id, "message_type": message_type, "event": event})


# POST NewEvent
@app.route('/api/match/message', methods=['GET', 'POST'])
def create_event():
    try:
        message_id = request.json['id']
        message_type = request.json['message_type']
        event = request.json['event']
    except KeyError as e:
        return {'Error': "{} is not provided".format(e)}, 500
    # print("Step 1")
    try:
        event_id = event['id']
        event_name = event['name']
        startTime = event['startTime']
        sport = event['sport']
        market = event['markets'][0]

        sport_id = sport['id']
        sport_name = sport['name']

        market_id = market['id']
        market_name = market['name']
        selections = market['selections']

    except Exception as e:
        return {'Error: {}'.format(str(e))}, 500
    # print("step 2")
    new_match = Match(event_id,
                      event_name,
                      "http://127.0.0.1:6000/api/match/{}".format(event_id),
                      startTime,
                      sport,
                      market)
    new_sport = Sport(sport_id, sport_name)
    new_market = Market(market_id, market_name, selections)
    new_message = Message(message_id, message_type, event_id)
    new_selections = []
    # print("selections: {}".format(selections))
    for selection in selections:
        s_id = selection['id']
        s_name = selection['name']
        s_odds = selection['odds']
        s_market_id = market_id
        new_selection = Selections(s_id, s_name, s_odds, s_market_id)
        new_selections.append(new_selection)

    commit_group = [new_match, new_market, new_message] + new_selections
    orgi_sport = Sport.query.filter_by(id=sport_id).count()
    if orgi_sport == 0:
        commit_group.append(new_sport)

    for one_commit in commit_group:
        try:
            db.session.add(one_commit)
            db.session.commit()
        except Exception as e:
            if 'Duplicate entry' in str(e):
                logger.debug(str(e))
                return jsonify(message_schema.dump({}))
            else:
                return str(e), 500
    return jsonify({"id": message_id, "message_type": message_type, "event": event}), 201


if __name__ == '__main__':
    logger.debug("Start the application")
    app.run(host="0.0.0.0", port=6000, debug=True, use_reloader=True)
