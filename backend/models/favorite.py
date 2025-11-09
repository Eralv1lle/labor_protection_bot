from peewee import Model, ForeignKeyField, TextField, DateTimeField
from datetime import datetime
from .base import db
from .user import User


class Favorite(Model):
    user = ForeignKeyField(User, backref='favorites', on_delete='CASCADE')
    question = TextField()
    answer = TextField()
    title = TextField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = 'favorites'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user.id,
            'question': self.question,
            'answer': self.answer,
            'title': self.title,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }