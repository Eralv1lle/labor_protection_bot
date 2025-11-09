from peewee import Model, ForeignKeyField, IntegerField, DateTimeField
from datetime import datetime
from .base import db
from .user import User

class Stats(Model):
    user = ForeignKeyField(User, backref='stats', on_delete='CASCADE')
    queries_count = IntegerField(default=0)
    last_request_at = DateTimeField(default=datetime.now)
    
    class Meta:
        database = db
        table_name = 'stats'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user.id,
            'telegram_id': self.user.telegram_id,
            'username': self.user.username,
            'queries_count': self.queries_count,
            'last_request_at': self.last_request_at.strftime('%Y-%m-%d %H:%M:%S')
        }
