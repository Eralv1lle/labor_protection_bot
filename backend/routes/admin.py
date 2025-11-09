from flask import Blueprint, request, jsonify
from backend.services import DatabaseService, FileParser, EmbeddingsService
import os
import config

admin = Blueprint('admin', __name__)

_embeddings_service = None


def get_embeddings_service():
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service


@admin.route('/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are supported'}), 400

        import urllib.parse
        filename = urllib.parse.unquote(file.filename)

        existing_doc = DatabaseService.get_document(filename)
        if existing_doc:
            return jsonify({'success': False, 'error': 'Document with this name already exists'}), 400

        file_path = os.path.join(config.DOCS_DIR, filename)
        file.save(file_path)

        parse_result = FileParser.parse_pdf(file_path)

        if not parse_result['success']:
            os.remove(file_path)
            return jsonify({'success': False, 'error': f"Failed to parse PDF: {parse_result['error']}"}), 500

        doc = DatabaseService.add_document(
            filename=filename,
            content=parse_result['content'],
            file_path=file_path,
            pages_count=parse_result['pages_count']
        )

        try:
            get_embeddings_service().add_document(
                text=parse_result['content'],
                filename=filename
            )
        except Exception as e:
            return jsonify({'success': False, 'error': f"Embeddings error: {str(e)}"}), 500

        return jsonify({
            'success': True,
            'message': f"Document '{filename}' uploaded successfully",
            'document': doc.to_dict()
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Upload error: {error_details}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin.route('/delete/<filename>', methods=['DELETE'])
def delete_document(filename):
    try:
        success = DatabaseService.delete_document(filename)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404

        file_path = os.path.join(config.DOCS_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        get_embeddings_service().rebuild_index()

        return jsonify({
            'success': True,
            'message': f"Document '{filename}' deleted successfully"
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin.route('/rebuild', methods=['POST'])
def rebuild_embeddings():
    try:
        get_embeddings_service().rebuild_index()
        stats = get_embeddings_service().get_stats()

        return jsonify({
            'success': True,
            'message': 'Embeddings rebuilt successfully',
            'stats': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500