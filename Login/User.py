from flask_login import UserMixin


class User(UserMixin):
    def __init__(self):
        self.id = None
        self.first_name = None
        self.last_name = None
        self.email = None

    def setUser(self, id, first_name, last_name, email):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

    def getUser(self):
        return self

    def getFirstName(self):
        return self.first_name

    def getLastName(self):
        return self.last_name
