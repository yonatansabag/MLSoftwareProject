from flask_login import UserMixin

class DummyUser(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

    @property
    def is_authenticated(self):
        return True