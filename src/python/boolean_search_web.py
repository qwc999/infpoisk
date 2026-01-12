from flask import Flask, render_template_string, request, jsonify
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from boolean_search import BooleanSearchEngine
from boolean_index import BooleanIndex

app = Flask(__name__)

search_engine = None
index_path = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boolean Search - Information Retrieval System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #607D8B;
            padding-bottom: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
            box-sizing: border-box;
        }
        button {
            background-color: #607D8B;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #455A64;
        }
        .examples {
            margin: 15px 0;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 4px;
            font-size: 14px;
        }
        .examples h4 {
            margin-top: 0;
        }
        .examples code {
            background: #e0e0e0;
            padding: 2px 6px;
            border-radius: 3px;
        }
        .results {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
            display: none;
        }
        .results.show {
            display: block;
        }
        .stats {
            margin: 15px 0;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }
        .result-list {
            margin-top: 15px;
        }
        .result-item {
            padding: 12px;
            margin: 8px 0;
            background: white;
            border-radius: 4px;
            border-left: 4px solid #607D8B;
        }
        .result-item .doc-id {
            font-weight: bold;
            color: #607D8B;
            font-size: 18px;
        }
        .result-item .title {
            margin-top: 5px;
            color: #333;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .status.success {
            background-color: #e8f5e9;
            border-left: 4px solid #4CAF50;
        }
        .status.error {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
        }
        .status.info {
            background-color: #e3f2fd;
            border-left: 4px solid #2196F3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Boolean Search</h1>
        
        <div id="status"></div>
        
        <div class="form-group">
            <label>Index Status:</label>
            <div id="indexStatus">No index loaded</div>
        </div>
        
        <form id="loadForm" style="margin-bottom: 30px;">
            <h3>Load Index</h3>
            <div class="form-group">
                <label for="indexFile">Index File:</label>
                <input type="text" id="indexFile" name="indexFile" placeholder="boolean_index.json" required>
            </div>
            
            <button type="submit">Load Index</button>
        </form>
        
        <form id="searchForm">
            <h3>Search</h3>
            <div class="form-group">
                <label for="query">Query:</label>
                <input type="text" id="query" name="query" placeholder="cat AND dog" required>
            </div>
            
            <button type="submit">Search</button>
        </form>
        
        <div class="examples">
            <h4>Query Examples:</h4>
            <ul>
                <li><code>cat AND dog</code> - Documents containing both "cat" and "dog"</li>
                <li><code>cat OR dog</code> - Documents containing "cat" or "dog"</li>
                <li><code>cat AND NOT dog</code> - Documents containing "cat" but not "dog"</li>
                <li><code>(cat OR dog) AND bird</code> - Documents containing ("cat" or "dog") and "bird"</li>
            </ul>
            <p><strong>Operators:</strong> AND, OR, NOT (case-insensitive)</p>
        </div>
        
        <div id="results" class="results">
            <h3>Search Results</h3>
            
            <div id="stats" class="stats"></div>
            
            <div id="resultList" class="result-list"></div>
        </div>
    </div>
    
    <script>
        const loadForm = document.getElementById('loadForm');
        const searchForm = document.getElementById('searchForm');
        const statusDiv = document.getElementById('status');
        const indexStatusDiv = document.getElementById('indexStatus');
        const resultsDiv = document.getElementById('results');
        const statsDiv = document.getElementById('stats');
        const resultListDiv = document.getElementById('resultList');
        
        function showStatus(message, type) {
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
            setTimeout(() => {
                statusDiv.innerHTML = '';
            }, 5000);
        }
        
        function updateIndexStatus() {
            fetch('/api/search/status')
                .then(response => response.json())
                .then(data => {
                    if (data.loaded) {
                        indexStatusDiv.innerHTML = `
                            <strong>Index loaded:</strong> ${data.total_documents} documents, 
                            ${data.total_terms} terms
                        `;
                        searchForm.style.display = 'block';
                    } else {
                        indexStatusDiv.innerHTML = 'No index loaded';
                        searchForm.style.display = 'none';
                    }
                });
        }
        
        loadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(loadForm);
            const data = {
                index_file: formData.get('indexFile')
            };
            
            try {
                const response = await fetch('/api/search/load', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.error) {
                    showStatus('Error: ' + result.error, 'error');
                    return;
                }
                
                showStatus('Index loaded successfully!', 'success');
                updateIndexStatus();
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            }
        });
        
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(searchForm);
            const data = {
                query: formData.get('query')
            };
            
            try {
                const response = await fetch('/api/search/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.error) {
                    showStatus('Error: ' + result.error, 'error');
                    return;
                }
                
                // Display statistics
                statsDiv.innerHTML = `
                    <strong>Query:</strong> ${result.query}<br>
                    <strong>Results:</strong> ${result.result_count} documents found
                `;
                
                // Display results
                if (result.results && result.results.length > 0) {
                    let html = '';
                    result.results.slice(0, 100).forEach(res => {
                        const docId = res.doc_id;
                        const metadata = res.metadata || {};
                        const title = metadata.title || 'No title';
                        html += `
                            <div class="result-item">
                                <div class="doc-id">Document ${docId}</div>
                                <div class="title">${title}</div>
                            </div>
                        `;
                    });
                    
                    if (result.result_count > 100) {
                        html += `<div class="result-item">... and ${result.result_count - 100} more documents</div>`;
                    }
                    
                    resultListDiv.innerHTML = html;
                } else {
                    resultListDiv.innerHTML = '<div class="result-item">No documents found</div>';
                }
                
                resultsDiv.classList.add('show');
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            }
        });
        
        // Update status on load
        updateIndexStatus();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/search/load', methods=['POST'])
def load_index():
    global search_engine, index_path
    
    try:
        data = request.json
        index_file = data.get('index_file', 'boolean_index.json')
        
        index_path = Path(index_file)
        search_engine = BooleanSearchEngine(index_path=index_path)
        
        return jsonify({
            'success': True,
            'total_documents': search_engine.index.stats['total_documents'],
            'total_terms': search_engine.index.stats['total_terms']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/status', methods=['GET'])
def get_status():
    global search_engine
    
    if search_engine is None:
        return jsonify({'loaded': False})
    
    return jsonify({
        'loaded': True,
        'total_documents': search_engine.index.stats['total_documents'],
        'total_terms': search_engine.index.stats['total_terms']
    })


@app.route('/api/search/query', methods=['POST'])
def search():
    """Search for documents."""
    global search_engine
    
    if search_engine is None:
        return jsonify({'error': 'No index loaded'}), 400
    
    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 100)
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        result = search_engine.search(query, limit=limit)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
