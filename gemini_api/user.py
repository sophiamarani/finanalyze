class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username

    def get_user_id(self):
        return self.id