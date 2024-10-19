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
import re

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
    if func_types:=func.__annotations__:
        types = list(func_types.items())
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

    ex::
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
        self.openapi_json = {}
        self.info = {}
        self.info['title'] = title
        self.info['description'] = description
        self.info['version'] = version
        self.servers = {}
        # route map
        self.paths = {}
        self.openapi_json['info'] = self.info
        self.openapi_json['openapi'] = '3.0.0'
        self.openapi_json['servers'] = self.servers
        self.openapi_json['paths'] = self.paths

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
                print(f'openapi register (url: {url}, methods: {methods}, endpoint: {endpoint}, view_func: {view_func})')

                self._push_path(url, methods, endpoint, view_func)

                return func(*args, **kwargs)
            return wrapped

        self.app.add_url_rule = _spec_collect_decorator(self.app.add_url_rule)
    
    def _push_path(self,
                   url: str,
                   methods: t.Iterable[str],
                   endpoint: str | None,
                   view_func: t.Callable):
        for http_method in methods:
            url = self._replace_path_param(url)
            path = self.paths.setdefault(url, {})
            method = path.setdefault(http_method, {})
            method['summary'] = view_func.__doc__
            method['description'] = ""
            method['operationId'] = view_func.__name__
            types = view_func.__annotations__


    def _replace_path_param(self, url) -> str:
        """ switch flask url rule to openapi path rule
        """
        flask_pattern = re.compile(r'<([a-zA-Z0-9:]+)>')

        def openapi_replacer(match):
            param = match.groups()[0]
            new_param = param.split(':')[-1]
            return "{" + new_param + "}"

        res = re.sub(flask_pattern, openapi_replacer, url)
        return res



def include(model: BaseModel, include_fields: t.Iterable[str]) -> dict:
    """a shortcut for model_dump(include...)
    """
    return model.model_dump(include=include_fields)


def exclude(model: BaseModel, exclude_fields: t.Iterable[str]) -> dict:
    """a shortcut for model_dump(exclude=?)
    """
    return model.model_dump(exclude=exclude_fields)