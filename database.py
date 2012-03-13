from __future__ import unicode_literals
import datetime
import sys
from urllib2 import urlopen, HTTPError
from urllib import urlencode, quote
import simplejson as json
import cherrypy


from pymongo import Connection 
from bson import json_util
from pymongo.errors import ConnectionFailure, OperationFailure

import redis
from redis import ConnectionError

ideas_for_mongo_db = """

IDEAS FOR USE
{Collections}= [users, groups, goals, awards]
Things to think about:
a) embed one to many relationships within the one
b) what needs to be queried the most often
c) catching typing errors before model insertion
d) indexing over multiple properties (aka shared key)

"""

###########################
### Generaic Functions  ###
###########################

def redis_connect():
    try:
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        r.ping()
        sys.stdout.write(" ** Redis connected **\n")
    except ConnectionError, e:
        sys.stderr.write("Could note connect to Redis: %s\n" %e)
        sys.exit(1)

def mongo_connect(name,extra=False):
    """ Connect to a MongoDB database, and write to stdio if failure. 
    Params: 
        name: the database name to connect to EX: test
    """
    try:
        #global connection
        connection = Connection()
        #database connection 
        db = connection[name]
        if extra:
            sys.stdout.write(" ** MongoDB connected to %s **\n" % name)

        # Good time to ensure that we have fast indexs, or should I wait?? 
        #db.users.ensureIndex({'username':1}, {unique: True})
        return db
    except ConnectionFailure, e:
        sys.stderr.write("Could Not connect to MongoDB: %s\n" %e)
        sys.exit(1)

def graph_facebook(query,a_token=None, args={}):
    """Helper for calling url of facebook graph api.

    Params: 
        query: the string for the specific graph endpoint.
        a_token: the acces_token 
        args: The query string args 

    Success: dict of query response.
    Failure: False. """


    if a_token:
        s = ("https://graph.facebook.com%s?"% query) + a_token +urlencode(args)
        try:
            return json.load(urlopen(s))
        except HTTPError, e:
            return e 
    else:
        return "NO ACCEsS_TOKEN"
    #TODO:else: get acces_token from db



#####################################################
### Functions needed for logging in a simple user ###
#####################################################

def facebook_2nd_leg(code, config):
    """Helper to complete Auth dance by using the acess_token needed for
    querying the facebook graph on a given user's information.

    Params:
        code: access_token from Facebook login dance
        config: the flask app.config 

    Success: auth_token.  
    Failure: returns False."""

    s = "{0:s}".format(config['FACEBOOK_ENDPOINT']) +\
        "/oauth/access_token?client_id={0:s}".format(config['FACEBOOK_ID']) +\
        "&redirect_uri={0:s}&client_secret={1:s}&code={2:s}".format(
                quote(config['FACEBOOK_REDIRECT']),
                config['FACEBOOKSECRET'], code)
    try:
        f = urlopen(s)
        token= f.read()
        return token
    except HTTPError, e:
        return False

    # TODO:store id
    # TODO: create User in DB


def cache_user(db, userdata, scaffold=False):
    """ Put  the id of the user into some sort of db
    """
    if userdata.get('id',False):
        user = {'id':userdata['id'],'type':'facebook'}
    # What are other solutions for state management?
    # Optimaizing response times?
    else:
        user = {'id':userdata, 'type':'default'}

##########################################
### Classes for Exposed REST Interface ###
##########################################

# Rember no templates, redirects, just simple json return values
# mongo.(type)s ** type is always plural

# first case is the object and no identifier -> returns collection
# '/api/user' or '/api/goal'
# second case is a specific object identifier -> returns object specified
# '/api/user/219df93' or '/api/user?uid=219df93' 
# '/api/goal/13213' or '/api/goal/?gid=13213'


class Welcome(object):

    exposed = True

    def default(self, extras='', more=''):
        return 'Hello World plus: %s' % extras, more
    default.exposed = True

class Home(object):
    pass

class API(object):

    def __init__(self, mongo):
        self.user = User(mongo)
        self.group = Group()
        self.award = Award()
        self.goal = Goal(mongo)

    def error(self, code,extras=None):
        
        if code== -1:
            reason = ['Server Error', code]
        elif code == 0:
            reason == ['Wrong input', code ,extras]
        elif code == 1:
            reason = ['Incorrect Permissions', code]
        return json.dumps({"Error": reason})

        pass


class User(object):
    # Could possibley remove all the explict uid varibales
    #TODO: create a staticmethods  

    __slots__ =('mongo','goal','_id', 'type', 'is_alive')

    def __init__(self, mongo, uid, type):
        self.mongo = mongo
        self.type = type
        self.is_alive = True
        self._id = {'_id':uid}


    ### Functions needed for a simple user ###

    @staticmethod
    def create(mongo, user, type='default', scaffold=True):
            """
            Used to add a new user into a mongo users Collection.

            Success: class with _id populated .
            Failure: False if mongo write fails.

            Id keys, can be either a "googleid" or "facebook_id" if using the
            scaffold, or you can put whatever into the users collection if scaffold
            is false. """
            try:
                if not scaffold:
                    # Important that we have safe write?? 
                    # save time without or too risky?
                    # for for a user profile write?
                    return User(mongo, mongo.users.insert(user,
                        safe=True),type)
                else:
                    # This is the most basic thing I could think of... 
                    # Yet I should test the amount of space this small thing takes up,
                    # Don't want to waste or wait on longer io times 
                    user_scaffold ={
                            'str_type': type,
                            'str_name': user.get('name',None),
                            'date_joindate': str(datetime.datetime.utcnow()),
                            'int_awardCount':0,
                            'int_completedGoals':0,
                            'int_startedGoals':0,
                            '_id_goals':[],
                            '_id_groups':[],
                            'awards':[],
                            }
                    if type != 'default':
                        user_scaffold['_social_id'] = user.get('id')
                    if type == 'facebook':
                        user_scaffold['facebook'] = {
                                        'location': user.get('location',None),
                                        'id': user.get('id'),
                                }
                    elif type == 'google':
                        user_scaffold['google'] = {
                                    'id':user.get('googleid'),
                                    }
                    return User(mongo, mongo.users.insert(user_scaffold,
                        safe=True), type)
            except OperationFailure, e:
                return False

    @staticmethod
    def find(mongo,  uid, type='default'):
        # only return the _id for User constructor
        if  type == 'default':
            user = mongo.users.find_one({'_id':uid},{'_id':1})
            if isinstance(user,dict):
                return User(mongo, user['_id'], type)
            else: return None
        else: 
            user = mongo.users.find_one({'_social_id':uid}, {'_id':1})
            if isinstance(user,dict):
                return  User(mongo, user['_id'], type)

    @property
    def info(self):
        if self.is_alive:
            return self.mongo.users.find_one(self._id, {'str_name':1,
            'int_awardCount':1})
        else: return None

    def delete(self):
            # if err msg None remove was a success 
            if not self.mongo.users.remove(self._id, safe=True)['err']:
                self.is_alive = False
                return True
            else: 
                return False

    def edit(self,  what_to_change):
        """  what_to_change is a dict of properties and
        their values to change
        """
        return self.mongo.users.update(self._id ,{"$set": what_to_change }, safe=True)

    def add_goal(self):
        pass
        
    ### Functions needed for a REST Interface ###

    def GET(self, uid=None, type='default' ):
        """ gets a specific user or  all users if no uid """
        if not uid:
            #TODO: stream response and limit query 
            users =[]
            for u in self.mongo.users.find():
                users.append(u)
            return users
        else:
            return self.find_one(uid, type)

    def POST():
        pass

    def PUT():
        pass

    def DELETE():
        pass

class Goal(object):

    __slots__ =('mongo')
    exposed = True

    def __init__(self, mongo):
        self.mongo = mongo

    ######################################################
    ### Functions that would munilpulate a goal object ###
    ######################################################

    def create(self, uid, goal, scaffold=True):

        """Used to add a new goal into a mongo goals Collection.

        Params: 
            goal: document to add 
            scaffold: Bool, whether to add default scaffold to embedded doc

            Success: _id of inserted doc.
            Failure: False if mongo write fails.

        
         """
        try:
            if not scaffold:
                return self.mongo.goals.insert(goal,safe=True)
            else:
                goal_scaffold = {
                    '_user_id': uid,
                     ## Array of ancestors
                    u'_id_tasks':[],
                    # Embedded user data ie; name id etc
                    u'motivators':[],
                    'descrip':{
                      u'str_who':None, u'str_what':None, 
                      u'str_where':None, u'str_why':None,
                        },
                    u'tags':[],
                   u'int_diffuculty':int(0),
                    u'date_start':datetime.datetime.utcnow(),
                    u'date_target':0,
                    u'int_votes':int(0),
                    u'bool_completed':False,
                }
                return self.mongo.goals.insert(goal_scaffold,safe=True)
        except OperationFailure:
            return False

    def delete(id):
        pass

    def finish(id):
        pass


    #############################################
    ### Functions needed for a REST Interface ###
    #############################################

    def GET():
        pass
    
    def POST():
        pass

    def PUT():
        pass

    def DELETE():
        pass



class Group(object):

    def GET():
        pass
    
    def POST():
        pass

    def PUT():
        pass

    def DELETE():
        pass

class Award(object):

    def GET():
        pass
    
    def POST():
        pass

    def PUT():
        pass

    def DELETE():
        pass


##############################################
### Functions that work with group objects ###
##############################################

def add_group(group, meta_data):
    pass

def add_group_memeber(id, user):
    pass

def merge_group(group1, group2, new):
    pass

##############################################
### Functions that work with Award objects ###
##############################################

def new_award(doc, award, scaffold=True):

    """ Used to add a new award into a mongo users Collection as a embedded doc.
    Params: 
        doc: query match document
        award: document to add 
        scaffold: Bool, whether to add default scaffold to embedded doc

        Success: _id of inserted doc.
        Failure: False if mongo write fails."""


    try:
        if not scaffold:
            return self.db.users.update(doc, {"$push":{'awards':award}},
                    safe=True)

        else:
            award_scaffold = {
                    'name': None,
                    'startDate':datetime.datetime.utcnow(),
                    'completedDate':0,
                    'value': int(0),
                    }
            return self.db.users.update(doc, {"$push":{'awards':award_scaffold}},
                    safe=True)
    except OperationFailure:
        return False



