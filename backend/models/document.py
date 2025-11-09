from peewee import Model, CharField, TextField, DateTimeField
from datetime import datetime
from .base import db

class Document(Model):
    filename = CharField(max_length=255, unique=True)
    content = TextField()
    upload_date = DateTimeField(default=datetime.now)
    file_path = CharField(max_length=512)
    pages_count = CharField(null=True)
    
    class Meta:
        database = db
        table_name = 'documents'
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_date': self.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            'pages_count': self.pages_count,
            'content_length': len(self.content) if self.content else 0
        }
