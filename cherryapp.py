import os
import cherrypy
import redis
import pymongo
import simplejson as json


from database import *
from bson import json_util
import simplejson as json

os.path.join(os.path.dirname(__file__),'')
mongo = mongo_connect('test', extra=True)
redis = redis_connect()
FACEBOOK_ENDPOINT ='https://graph.facebook.com'
FACEBOOK_ID = '250775514988009'
FACEBOOK_REDIRECT = 'http://localhost:5000/fbauth'
FACEBOOKSECRET = '650141692b0c5b9815b1b24c1c620231'

restful_api = API(mongo)

def f_login():
    """ First step in login process for Facebook Auth and user info """

    # check if we already have this id and key
    id = session.get('user_id', None) 
    # We have already done handshake nothing else to do.
    if id:
        return redirect(url_for('home'))
    # we must direct to facebook app permisions web based dialogue
    else:
        return redirect(
            "https://www.facebook.com/dialog/oauth?"+ 
            "client_id={0:s}&redirect_uri={1:s}&scope=read_stream".format(
                app.config['FACEBOOK_ID'], app.config['FACEBOOK_REDIRECT']))

def f_auth():
    """ 2nd part of login through facebook oauth2. """

    # get first step auth code
    code = request.args.get('code',False)

    # Facebook request for auth permission denied
    # TODO: need to handle various cases of user actions with oauth dialog
    if not code:

        # Logg errors here??
        # Flash("error")??
        return redirect(url_for('welcome'))

    # Finish auth process and procced to user creation and caching
    else:

        # flash("Creating User")??
        access_token = facebook_2nd_leg(code, app.config)
        if access_token:
            fuser = graph_facebook('/me', access_token)
        else: 
            return redirect(url_for('welcome'))

        uid = create_user(mongo,fuser, 'facebook')
        # Interchangable??
        # store id of service type? aka facebook or google or others 'id'??
        cache_user(redis, fuser)
        session.modified = True
        return redirect(url_for('home'))

################################################################################
### Cherrypy Custom Tools and Hooks ############################################
################################################################################

def json_handler(*args, **kwargs):
    value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
    return json_en(value)


json_en = json.JSONEncoder(default=json_util.default).iterencode
root = Welcome()
root.api = restful_api
conf = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8000,
    },
    '/api': {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.json_out.on' : True ,
        'tools.json_out.handler' : json_handler,
    }
}

cherrypy.engine.autoreload.on = True
cherrypy.quickstart(root, '/', conf)
