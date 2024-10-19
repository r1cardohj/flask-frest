"""
Author: r1cardohj
Email: houjun447@gmail.com

frest is more like a Unix-style Flask plugin support hot swap at any time
basically it just do two thing:
    1. Automatically serialize and deserialize json
    2. provide some helpful until to make your restful app

let us make flask be better if you don't like fastapi...(●'◡'●)
"""

from functools import wraps
import typing as t

from pydantic import ValidationError, BaseModel
from flask import request, Flask


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
    body_type = None
    if func_types:=func.__annotations__:
        types = list(func_types.items())
        args_name, body_type= types[0]

        if not issubclass(body_type, BaseModel) or args_name == "return":
            body_type = None
        
    @wraps(func)
    def wrapped(*args, **kwargs):
        if body_type:
            try:
                model = body_type(**request.json)
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


def include(model: BaseModel, include_fields: t.Iterable[str]) -> dict:
    """a shortcut for model_dump(include...)
    """
    return model.model_dump(include=include_fields)


def exclude(model: BaseModel, exclude_fields: t.Iterable[str]) -> dict:
    """a shortcut for model_dump(exclude=?)
    """
    return model.model_dump(exclude=exclude_fields)

