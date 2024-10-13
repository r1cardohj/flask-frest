# frest

make your flask app become restful and modern

```python
from flask import Flask
from pydantic import BaseModel
from frest import restful

app = Flask(__name__)

class User(BaseModel):
    name: str
    age: int


class Account(BaseModel):
    username: str
    password: str


@app.post('/')
@restful
def create_user(user: User):
    account = Account(username=user.name,
                      password=str(user.age) + "secret key")
    return account
```

**todo list**

- [x] auto serialize input/output json
- [ ] auto generate openapi doc
- [ ] ...
