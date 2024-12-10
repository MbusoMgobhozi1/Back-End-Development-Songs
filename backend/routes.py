from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health", methods=["GET"])
def get_health():
    return {"status": "ok"}, 200

@app.route("/count", methods=["GET"])
def get_count():
    count_documents = len(songs_list)
    return {"count": count_documents}, 200

@app.route("/song", methods=["GET"])
def songs():
    list_of_songs = json_util.dumps(db.songs.find({}))
    return {"songs": json.loads(list_of_songs)}

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    song = json_util.dumps(db.songs.find_one({"id": id}))
    if not song:
        return {"message": "song with id not found"}, 404

    return json.loads(song), 200

@app.route("/song", methods=["POST"])
def create_song():
    data = request.get_json()

    existing_song = db.songs.find_one({"id": data.get("id")})
    if existing_song:
        return {"Message": f"song with id {data.get('id')} already present"}, 302
    
    inserted_data = db.songs.insert_one(data)
    return {"inserted_id": str(inserted_data.inserted_id)}

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    data = request.get_json()

    existing_song = db.songs.find_one({"id": id})
    if not existing_song:
        return {"message": "song not found"}, 404

    db.songs.update_one({"id": id}, {"$set": data})

    updated_song_data = db.songs.find_one({"id": id})
    return json.loads(json_util.dumps(updated_song_data)), 201

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    existing_song = db.songs.find_one({"id": id})
    if not existing_song:
        return {"message": "song not found"}, 404

    db.songs.delete_one({"id": id})
    return '' ,204