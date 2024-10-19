import unittest
from flask import Flask
from frest import restful
from frest.core import include, exclude
from pydantic import BaseModel

class TestCore(unittest.TestCase):
    
    def setUp(self) -> None:
        app = Flask(__name__)
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.runner = app.test_cli_runner()
        self.app = app
        self.app.json.sort_keys = False

    def test_app_exist(self):
        self.assertIsNotNone(self.app)
    
    def test_app_is_testing(self):
        self.assertTrue(self.app.config['TESTING'])
    
    def test_restful_input(self):

        class Person(BaseModel):
            name: str
            age: int

        @self.app.post('/person')
        @restful
        def create_person(person: Person):
            return person
        
        resp = self.client.post('/person', json=dict(
            name='test', age=12
        ))
        self.assertEqual(resp.get_json(),
                         dict(name='test', age=12))
    
    def test_include(self):
        class Person(BaseModel):
            name: str
            age: int
            height: float
        
        @self.app.get('/person')
        @restful
        def list_person():
            person = Person(name='xx', age=12, height=50.1)
            return include(person, ['name', 'height'])
        
        resp = self.client.get('/person')

        self.assertEqual(resp.get_json(),
                         dict(name='xx', height=50.1))

    def test_exclude(self):
        class Dog(BaseModel):
            name: str
            age: int
            weight: float

        @self.app.get('/dog')
        @restful
        def list_dog():
            dog = Dog(name='puppy', age=12, weight=12.44)
            return exclude(dog, ['age'])
        
        resp = self.client.get('/dog')

        self.assertEqual(resp.get_json(), dict(name='puppy', weight=12.44))
        


if __name__ == '__main__': 
    unittest.main()


