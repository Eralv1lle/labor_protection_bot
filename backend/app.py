from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from backend.routes import api, admin
from backend.models import init_db
import config
import os

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
CORS(app)

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(admin, url_prefix='/admin')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    init_db()

    from backend.services.embeddings import EmbeddingsService

    embeddings = EmbeddingsService()
    if embeddings.index.ntotal == 0:
        embeddings.rebuild_index()

    print(f"Starting Flask server on {config.FLASK_HOST}:{config.FLASK_PORT}")
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
        ssl_context='adhoc'
    )
