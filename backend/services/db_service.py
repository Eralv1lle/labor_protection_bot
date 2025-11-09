from datetime import datetime
from typing import Optional, List, Dict
from backend.models import db, Document, User, Stats
from peewee import DoesNotExist

class DatabaseService:
    @staticmethod
    def get_or_create_user(telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None) -> User:
        with db.atomic():
            user, created = User.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name
                }
            )
            
            if not created:
                user.username = username or user.username
                user.first_name = first_name or user.first_name
                user.last_name = last_name or user.last_name
                user.last_active = datetime.now()
                user.save()

            Stats.get_or_create(user=user)
            
            return user
    
    @staticmethod
    def increment_user_queries(telegram_id: int):
        user = User.get(User.telegram_id == telegram_id)
        stats, _ = Stats.get_or_create(user=user)
        
        stats.queries_count += 1
        stats.last_request_at = datetime.now()
        stats.save()
    
    @staticmethod
    def add_document(filename: str, content: str, file_path: str, pages_count: int) -> Document:
        with db.atomic():
            doc = Document.create(
                filename=filename,
                content=content,
                file_path=file_path,
                pages_count=pages_count
            )
            return doc
    
    @staticmethod
    def get_document(filename: str) -> Optional[Document]:
        try:
            return Document.get(Document.filename == filename)
        except DoesNotExist:
            return None
    
    @staticmethod
    def delete_document(filename: str) -> bool:
        try:
            doc = Document.get(Document.filename == filename)
            doc.delete_instance()
            return True
        except DoesNotExist:
            return False
    
    @staticmethod
    def list_documents() -> List[Document]:
        return list(Document.select().order_by(Document.upload_date.desc()))
    
    @staticmethod
    def get_all_documents_text() -> str:
        documents = Document.select()
        return "\n\n---DOCUMENT SEPARATOR---\n\n".join([doc.content for doc in documents if doc.content])
    
    @staticmethod
    def get_statistics() -> Dict:
        total_docs = Document.select().count()
        total_users = User.select().count()
        total_queries = Stats.select(Stats.queries_count).count()

        top_users = (Stats
                    .select(Stats, User)
                    .join(User)
                    .order_by(Stats.queries_count.desc())
                    .limit(10))
        
        top_users_list = []
        for stat in top_users:
            top_users_list.append({
                'username': stat.user.username or f"User {stat.user.telegram_id}",
                'queries': stat.queries_count
            })

        recent_users = (User
                       .select()
                       .order_by(User.last_active.desc())
                       .limit(5))
        
        recent_users_list = []
        for user in recent_users:
            recent_users_list.append({
                'username': user.username or f"User {user.telegram_id}",
                'last_active': user.last_active.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            'total_documents': total_docs,
            'total_users': total_users,
            'total_queries': total_queries,
            'top_users': top_users_list,
            'recent_users': recent_users_list
        }