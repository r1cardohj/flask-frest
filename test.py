import unittest
from flask import Flask
from frest import restful
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


if __name__ == '__main__': 
    unittest.main()


