from flask import Blueprint, request, jsonify
from backend.services import GigaChatClient, DatabaseService, EmbeddingsService
from backend.models import User, Stats, Favorite
from datetime import datetime
import config

api = Blueprint('api', __name__)

giga_client = GigaChatClient()
embeddings_service = EmbeddingsService()


@api.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json

        if not data or 'question' not in data:
            return jsonify({'success': False, 'error': 'Question is required'}), 400

        question = data['question']
        telegram_id = data.get('telegram_id')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        system_prompt = data.get('system_prompt')

        if telegram_id:
            user = DatabaseService.get_or_create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            DatabaseService.increment_user_queries(telegram_id)

        if system_prompt:
            result = giga_client.ask(question, context=None, system_prompt=system_prompt)
        else:
            result = giga_client.ask_with_rag(question, embeddings_service)

        if result['success']:
            return jsonify({
                'success': True,
                'answer': result['response'],
                'context_used': result.get('context_used', False),
                'tokens_used': result.get('tokens_used', 0)
            })
        else:
            return jsonify({'success': False, 'error': result['error']})

    except Exception as e:
        import traceback
        print(f"Error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api.route('/stats', methods=['GET'])
def get_stats():
    try:
        stats = DatabaseService.get_statistics()
        embeddings_stats = embeddings_service.get_stats() if embeddings_service else {}

        return jsonify({
            'success': True,
            'database': stats,
            'embeddings': embeddings_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/documents', methods=['GET'])
def list_documents():
    try:
        documents = DatabaseService.list_documents()
        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in documents]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@api.route('/init_user', methods=['POST'])
def init_user():
    try:
        data = request.json

        telegram_id = data.get('telegram_id')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not telegram_id:
            return jsonify({
                'success': False,
                'error': 'telegram_id is required'
            }), 400

        user = DatabaseService.get_or_create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )

        return jsonify({
            'success': True,
            'user': user.to_dict()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/profile/<int:telegram_id>', methods=['GET'])
def get_profile(telegram_id):
    try:
        user = User.get(User.telegram_id == telegram_id)
        stats = Stats.get(Stats.user == user)
        favorites_count = Favorite.select().where(Favorite.user == user).count()

        return jsonify({
            'success': True,
            'profile': {
                'user': user.to_dict(),
                'stats': stats.to_dict(),
                'favorites_count': favorites_count
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/favorites', methods=['POST'])
def add_favorite():
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        question = data.get('question')
        answer = data.get('answer')
        title = data.get('title', question[:50] + '...')

        if not all([telegram_id, question, answer]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        user = User.get(User.telegram_id == telegram_id)

        favorite = Favorite.create(
            user=user,
            question=question,
            answer=answer,
            title=title
        )

        return jsonify({
            'success': True,
            'favorite': favorite.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/favorites/<int:telegram_id>', methods=['GET'])
def get_favorites(telegram_id):
    try:
        user = User.get(User.telegram_id == telegram_id)
        favorites = Favorite.select().where(Favorite.user == user).order_by(Favorite.created_at.desc())

        return jsonify({
            'success': True,
            'favorites': [fav.to_dict() for fav in favorites]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api.route('/favorites/<int:favorite_id>', methods=['DELETE'])
def delete_favorite(favorite_id):
    try:
        favorite = Favorite.get_by_id(favorite_id)
        favorite.delete_instance()

        return jsonify({
            'success': True,
            'message': 'Favorite deleted'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500