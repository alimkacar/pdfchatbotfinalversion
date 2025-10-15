from flask import Flask, request, render_template_string, jsonify, session
import os
from datetime import datetime
from pathlib import Path


from config import Config
from core.pdf_processor import PDFProcessor
from core.search_engine import SearchEngine
from core.utils import Validator, PDFProcessingError, SearchError, ValidationError, setup_logger


app = Flask(__name__)
app.config.from_object(Config)
Config.init_folders()


logger = setup_logger(__name__)


pdf_processor = PDFProcessor(
    chunk_size=Config.CHUNK_SIZE,
    overlap=Config.CHUNK_OVERLAP
)
search_engine = SearchEngine()

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF RAG Arama Sistemi</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin-bottom: 20px;
        }
        .upload-btn {
            background: #667eea;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .search-box {
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        .search-btn {
            background: #28a745;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        .result {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
            margin: 15px 0;
        }
        .similarity-score {
            background: #007bff;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
        }
        .status { padding: 15px; margin: 15px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .loading { display: none; text-align: center; padding: 20px; }
        .spinner { 
            border: 4px solid #f3f3f3; 
            border-top: 4px solid #667eea; 
            border-radius: 50%; 
            width: 40px; 
            height: 40px; 
            animation: spin 2s linear infinite; 
            margin: 0 auto; 
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 PDF RAG Arama Sistemi</h1>
        <p>PDF belgelerinizi yükleyin ve içeriğinde arama yapın</p>
    </div>

    <div class="container">
        <h2>📁 PDF Yükleme</h2>
        <div class="upload-area">
            <input type="file" id="fileInput" accept=".pdf" style="display: none;">
            <button class="upload-btn" onclick="document.getElementById('fileInput').click()">PDF Dosyası Seç</button>
        </div>
        <div class="loading" id="uploadLoading">
            <div class="spinner"></div>
            <p>PDF işleniyor...</p>
        </div>
        <div id="uploadStatus"></div>
    </div>

    {% if session.get('current_pdf') %}
    <div class="container">
        <h3>📄 Yüklenen PDF: {{ session.get('current_pdf') }}</h3>
        <p>Chunk Sayısı: {{ session.get('chunk_count', 0) }}</p>
        
        <div style="margin: 20px 0;">
            <input type="text" class="search-box" id="searchQuery" placeholder="Arama yapın...">
            <button class="search-btn" onclick="performSearch()">Ara</button>
        </div>
        
        <div class="loading" id="searchLoading">
            <div class="spinner"></div>
            <p>Arama yapılıyor...</p>
        </div>
    </div>
    <div id="searchResults"></div>
    {% endif %}

    <script>
        document.getElementById('fileInput').addEventListener('change', uploadFile);

        function uploadFile() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('pdf', file);

            document.getElementById('uploadLoading').style.display = 'block';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('uploadLoading').style.display = 'none';
                showStatus(data.message, data.success ? 'success' : 'error');
                if (data.success) setTimeout(() => location.reload(), 1000);
            })
            .catch(error => {
                document.getElementById('uploadLoading').style.display = 'none';
                showStatus('Hata: ' + error, 'error');
            });
        }

        function performSearch() {
            const query = document.getElementById('searchQuery').value.trim();
            if (!query) {
                showStatus('Arama terimi girin', 'error');
                return;
            }

            document.getElementById('searchLoading').style.display = 'block';

            fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({query: query})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('searchLoading').style.display = 'none';
                displayResults(data);
            })
            .catch(error => {
                document.getElementById('searchLoading').style.display = 'none';
                showStatus('Arama hatası: ' + error, 'error');
            });
        }

        function displayResults(data) {
            const resultsDiv = document.getElementById('searchResults');
            
            if (!data.success) {
                showStatus(data.message, 'error');
                return;
            }

            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<div class="container"><div class="status">Sonuç bulunamadı.</div></div>';
                return;
            }

            let html = '<div class="container"><h2>🎯 Sonuçlar (' + data.results.length + ')</h2>';
            
            data.results.forEach(result => {
                const score = (result.similarity_score * 100).toFixed(1);
                html += '<div class="result">';
                html += '<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">';
                html += '<strong>Sonuç #' + result.rank + '</strong>';
                html += '<span class="similarity-score">' + score + '% benzerlik</span>';
                html += '</div>';
                html += '<div>' + result.text + '</div>';
                html += '</div>';
            });
            
            html += '</div>';
            resultsDiv.innerHTML = html;
        }

        function showStatus(message, type) {
            document.getElementById('uploadStatus').innerHTML = 
                '<div class="status ' + type + '">' + message + '</div>';
        }

        // Enter ile arama
        document.addEventListener('DOMContentLoaded', function() {
            const searchBox = document.getElementById('searchQuery');
            if (searchBox) {
                searchBox.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') performSearch();
                });
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    """PDF dosyası yükleme endpoint'i"""
    try:
        
        file = request.files.get('pdf')
        if not file:
            return jsonify({'success': False, 'message': 'Dosya seçilmedi'})
        
       
        filename = Validator.validate_file(file, Config.ALLOWED_EXTENSIONS, Config.MAX_FILE_SIZE)
        
        
        filepath = Config.UPLOAD_FOLDER / filename
        file.save(filepath)
        
        
        processed_doc, error = pdf_processor.process_pdf(filepath, filename.rsplit('.', 1)[0])
        
        if error:
            
            if filepath.exists():
                filepath.unlink()
            return jsonify({'success': False, 'message': error})
        
        
        search_engine.index_document(processed_doc)
        
        
        processed_path = Config.PROCESSED_FOLDER / f"{processed_doc.filename}.pkl"
        pdf_processor.save_processed_document(processed_doc, processed_path)
        
        
        session['current_pdf'] = filename
        session['processed_file'] = f"{processed_doc.filename}.pkl"
        session['chunk_count'] = processed_doc.get_chunk_count()
        
        
        if filepath.exists():
            filepath.unlink()
        
        return jsonify({
            'success': True,
            'message': f'PDF başarıyla işlendi! {processed_doc.get_chunk_count()} chunk oluşturuldu.'
        })
        
    except ValidationError as e:
        return jsonify({'success': False, 'message': str(e)})
    except PDFProcessingError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        logger.error(f"Upload hatası: {e}")
        return jsonify({'success': False, 'message': f'Dosya yükleme hatası: {str(e)}'})

@app.route('/search', methods=['POST'])
def search():
    """Arama endpoint'i"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        
        query = Validator.validate_search_query(query)
        
        
        if not session.get('processed_file'):
            return jsonify({'success': False, 'message': 'Önce PDF yükleyin'})
        
        
        if not search_engine.current_document:
            processed_path = Config.PROCESSED_FOLDER / session['processed_file']
            processed_doc = pdf_processor.load_processed_document(processed_path)
            
            if not processed_doc:
                return jsonify({'success': False, 'message': 'İşlenmiş PDF bulunamadı'})
            
            search_engine.index_document(processed_doc)
        
        
        search_response = search_engine.search(
            query=query,
            max_results=Config.MAX_SEARCH_RESULTS,
            min_similarity=Config.MIN_SIMILARITY
        )
        
        return jsonify({
            'success': True,
            'message': f'{search_response.total_found} sonuç bulundu',
            'results': [result.to_dict() for result in search_response.results],
            'search_time': search_response.search_time,
            'query': query
        })
        
    except ValidationError as e:
        return jsonify({'success': False, 'message': str(e)})
    except SearchError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        logger.error(f"Arama hatası: {e}")
        return jsonify({'success': False, 'message': f'Arama hatası: {str(e)}'})

if __name__ == '__main__':
    logger.info("PDF RAG Chatbot başlatılıyor...")
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
