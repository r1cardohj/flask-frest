import typing as t
from pydantic import ValidationError, BaseModel
from functools import wraps
from flask import request 


def restful(func: t.Callable):
    """ auto valiate and serialize 
        from input/output json schema which 
        define by the subclass of `pydantic.BaseModel`
    example: 

        @app.get('/user')
        @restful
        def list_user_group(user: User):
            return user
    """
    _type = None
    if func.__annotations__:
        _, _type = list(func.__annotations__.items())[0]
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
        # if function return a list, will serialize all BaseModel obj
        elif isinstance(resp_obj, list):
            new_resp_obj = list(resp_obj) 
            for idx, item in enumerate(resp_obj):
                if issubclass(type(item), BaseModel):
                    new_resp_obj[idx] = new_resp_obj[idx].model_dump()
            resp_obj = new_resp_obj
        return resp_obj
    return wrapped

