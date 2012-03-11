from cherrypy.test.webtest import WebCase
import unittest
from database import mongo_connect, redis_connect, create_user
from helpers import testuser 
import simplejson as json

mongo = mongo_connect('test', extra=True)
redis = redis_connect()

class TestApp(WebCase):

    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        mongo.connection.drop_database('test')

        
    def test_welcome(self):
        self.getPage('/')
        self.assertInBody('Hello World')

    def test_User(self):
        testuser_id = create_user(mongo,  testuser, 'facebook')

        #make sure that query or url vars are capable
        self.getPage('/api/user?uid=100000220742923&type=facebook')
        self.assertInBody('Matthew Donavan Clemens')
        self.assertInBody('100000220742923')

        self.getPage('/api/user/100000220742923/facebook')
        self.assertInBody('Matthew Donavan Clemens')
        self.assertInBody('100000220742923')

        self.getPage('/api/user/')



if __name__ == '__main__':
    unittest.main()
