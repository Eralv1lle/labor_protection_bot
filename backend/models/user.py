from peewee import Model, BigIntegerField, CharField, DateTimeField
from datetime import datetime
from .base import db

class User(Model):
    telegram_id = BigIntegerField(unique=True, index=True)
    username = CharField(max_length=255, null=True)
    first_name = CharField(max_length=255, null=True)
    last_name = CharField(max_length=255, null=True)
    created_at = DateTimeField(default=datetime.now)
    last_active = DateTimeField(default=datetime.now)
    
    class Meta:
        database = db
        table_name = 'users'
    
    def to_dict(self):
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_active': self.last_active.strftime('%Y-%m-%d %H:%M:%S')
        }
