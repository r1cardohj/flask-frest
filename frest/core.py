"""
Author: r1cardohj
Email: houjun447@gmail.com

frest is more like a Unix-style Flask plugin support hot swap at any time
basically it just do two thing:
    1. Automatically serialize and deserialize json
    2. Automatically generate openapi documentation

let us make flask be better if you don't like fastapi...(●'◡'●)
"""

from functools import wraps
import typing as t

from pydantic import ValidationError, BaseModel
from flask import Flask, request


# use `restful` to collect the type annotations in view-func firstly
_meta_endpoint_func_types: t.List = []

def restful(func: t.Callable):
    """ auto valiate and serialize 
        from input/output json schema which 
        define by the subclass of `pydantic.BaseModel`
    example: 

        @app.get('/user')
        @restful
        def list_user(user: User):
            return user
    """
    _type = None
    if func.__annotations__:
        types = list(func.__annotations__.items())
        _, _type = types[0]
        if not issubclass(_type, BaseModel):
            _type = None

    @wraps(func)
    def wrapped(*args, **kwargs):
        if _type:
            try:
                model = _type(**request.json)
            except ValidationError as e:
                return e.errors(), 400
            resp_obj = func(model, *args, **kwargs)
        else:
            resp_obj = func(*args, **kwargs)

        if issubclass(type(resp_obj), BaseModel):
            resp_obj = resp_obj.model_dump()
        # sometime in flask view function will return
        # iter item like tuple (obj, code)
        elif isinstance(resp_obj, tuple):
            first = resp_obj[0]
            if issubclass(type(first), BaseModel):
                resp_obj = first.model_dump(), *resp_obj[1:]
            elif isinstance(first, list):
                new_first = list(first) 
                for idx, item in enumerate(first):
                    if issubclass(type(item), BaseModel):
                        new_first[idx] =new_first[idx].model_dump()
                resp_obj = new_first, *resp_obj[1:]
        # if function return a list, it will serialize all BaseModel obj in list
        elif isinstance(resp_obj, list):
            new_resp_obj = list(resp_obj) 
            for idx, item in enumerate(resp_obj):
                if issubclass(type(item), BaseModel):
                    new_resp_obj[idx] = new_resp_obj[idx].model_dump()
            resp_obj = new_resp_obj
        return resp_obj
    return wrapped


class Swagger:
    """ auto generate swagger document,
    use it like normal flask ext.

    example:
        app = Flask(__name__)
        swagger = Swagger(app)
    """
    

    def __init__(self,
                 app: t.Optional[Flask]=None,
                 title: str='Frest API',
                 description: t.Optional[str]=None,
                 version: str='0.0.1'):
        if app is not None:
            self.init_app(app)

        # openapi metadata
        self.info = {}
        self.info['title'] = title
        self.info['description'] = description
        self.info['version'] = version
        self.servers = {}
        # route map
        self.paths = {}
        self.path_spec_data = []

    def init_app(self, app: Flask):
        self.app = app

        def _spec_collect_decorator(func: t.Callable):
            """wrap flask.add_url_rule for collect openapi meta data
            """
            @wraps(func)
            def wrapped(*args, **kwargs):
                url = args[0]
                methods = kwargs['methods']
                endpoint = args[1]
                view_func = args[2]
                print(url, methods, endpoint, view_func)
                self.path_spec_data.append((url, methods, endpoint, view_func))
                return func(*args, **kwargs)
            return wrapped

        self.app.add_url_rule = _spec_collect_decorator(self.app.add_url_rule)


def include(model: BaseModel, include_fields: t.Iterable[str]) -> dict:
    """a shortcut for model_dump(include...)

    ex::
        @app.post("/")
        @restful
        def list_person(person: Person):
            person = Person(name='xx', age=12)
            # age is a secret...
            return include(person, ["name"])
    """
    return model.model_dump(include=include_fields)


def exclude(model: BaseModel, exclude_fields: t.Iterable[str]) -> dict:
    """a shortcut for model_dump(exclude=?)
    
    ex::
        @app.post("/")
        @restful
        def list_person(person: Person)
            person = Person(name="xx", age=12)
            # age is a secret
            return exclude(person, ["age"])
    """
    return model.model_dump(exclude=exclude_fields)