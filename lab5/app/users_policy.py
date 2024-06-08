from flask_login import current_user

class UsersPolicy:
    def __init__(self, record):
        self.record = record

    def create(self):
       return current_user.is_admin()
    
    def view(self):
        if current_user.is_admin():
            return True
        return str(current_user.id) == str(self.record.id)
    
    def edit(self):
        if current_user.is_admin():
            return True
        return str(current_user.id) == str(self.record.id)
    
    def delete(self):
        return current_user.is_admin()
    
    def show_statistics(self):
        return current_user.is_admin()