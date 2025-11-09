from peewee import SqliteDatabase
import config

db = SqliteDatabase(config.DATABASE_PATH)


def init_db():
    from .document import Document
    from .user import User
    from .stats import Stats
    from .favorite import Favorite
    import os

    db.connect()
    db.create_tables([Document, User, Stats, Favorite], safe=True)

    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    existing_files = set(f for f in os.listdir(docs_dir) if f.endswith('.pdf'))
    db_documents = {doc.filename: doc for doc in Document.select()}

    for filename in db_documents:
        if filename not in existing_files:
            db_documents[filename].delete_instance()

    for filename in existing_files:
        if filename not in db_documents:
            from backend.services.file_parser import FileParser
            file_path = os.path.join(docs_dir, filename)
            result = FileParser.parse_pdf(file_path)

            if result['success']:
                Document.create(
                    filename=filename,
                    content=result['content'],
                    file_path=file_path,
                    pages_count=result['pages_count']
                )

    db.close()