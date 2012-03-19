from cherrypy.test.webtest import WebCase
import unittest
from database import mongo,  User, Goal
from helpers import testuser 
import simplejson as json

class TestAPI(WebCase):

    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        mongo.connection.drop_database('test')

    def setUp(self):
        mongo.users.remove()



    def test_mongo_user(self):
        user = User.create(testuser,'facebook')
        self.assertTrue( user ) 
        self.assertIsInstance(user , User )
        self.assertIn('str_name', user.info())

        uid = user._id 

        usersame = User.find(uid)
        self.assertEqual(usersame.info(), user.info())
        self.assertIsInstance(user.info(), dict)

        #edit
        self.assertTrue( user.edit({'str_name':'BurgerKing'}) )
        self.assertIn('BurgerKing', str(user.info()))
        self.assertIn('facebook', str(user.info(['str_type'])))

        # Remove does it return True? if so sucessful remove.
        self.assertTrue( user.delete() )
        self.assertFalse( user.is_alive)
        self.assertFalse( user.info())
        self.assertFalse(User.find(uid))

    def test_mongo_goal(self):
        pass
        user = User.create( testuser,'facebook')
        goal = user.add_goal()
        self.assertTrue(goal._id)




    def _test_welcome(self):
        self.getPage('/')
        self.assertInBody('Hello World')

    def _test_User(self):
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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAPI)
    unittest.TextTestRunner(verbosity=2).run(suite)
