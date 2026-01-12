from flask import Flask, render_template_string, request, jsonify
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from boolean_index import BooleanIndex
from tokenizer import Tokenizer
from stemmer import Stemmer

app = Flask(__name__)

index_instance = None
index_path = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boolean Index - Information Retrieval System</title>
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
            border-bottom: 3px solid #E91E63;
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
        input[type="text"], input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }
        button {
            background-color: #E91E63;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
            margin-top: 10px;
        }
        button:hover {
            background-color: #C2185B;
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
            padding: 15px;
            background: white;
            border-radius: 4px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .stat-card {
            padding: 15px;
            background: #f0f0f0;
            border-radius: 4px;
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #E91E63;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .query-results {
            margin-top: 15px;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }
        .doc-list {
            margin-top: 10px;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
        }
        .doc-item {
            padding: 5px;
            margin: 2px 0;
            background: white;
            border-radius: 3px;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Boolean Index</h1>
        
        <div id="status"></div>
        
        <div class="form-group">
            <label>Index Status:</label>
            <div id="indexStatus">No index loaded</div>
        </div>
        
        <form id="buildForm">
            <h3>Build Index</h3>
            <div class="form-group">
                <label for="corpusDir">Corpus Directory:</label>
                <input type="text" id="corpusDir" name="corpusDir" placeholder="corpus" required>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="useStemming" name="useStemming">
                    Use stemming
                </label>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="removeStopwords" name="removeStopwords">
                    Remove stop words
                </label>
            </div>
            
            <button type="submit">Build Index</button>
        </form>
        
        <form id="loadForm" style="margin-top: 30px;">
            <h3>Load Index</h3>
            <div class="form-group">
                <label for="indexFile">Index File:</label>
                <input type="text" id="indexFile" name="indexFile" placeholder="boolean_index.json" required>
            </div>
            
            <button type="submit">Load Index</button>
        </form>
        
        <form id="queryForm" style="margin-top: 30px;">
            <h3>Query Index</h3>
            <div class="form-group">
                <label for="queryTerm">Term:</label>
                <input type="text" id="queryTerm" name="queryTerm" placeholder="Enter term to search" required>
            </div>
            
            <button type="submit">Search</button>
        </form>
        
        <div id="results" class="results">
            <h3>Results</h3>
            <div id="stats" class="stats"></div>
            <div id="queryResults" class="query-results"></div>
        </div>
    </div>
    
    <script>
        const buildForm = document.getElementById('buildForm');
        const loadForm = document.getElementById('loadForm');
        const queryForm = document.getElementById('queryForm');
        const statusDiv = document.getElementById('status');
        const indexStatusDiv = document.getElementById('indexStatus');
        const resultsDiv = document.getElementById('results');
        const statsDiv = document.getElementById('stats');
        const queryResultsDiv = document.getElementById('queryResults');
        
        function showStatus(message, type) {
            statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
            setTimeout(() => {
                statusDiv.innerHTML = '';
            }, 5000);
        }
        
        function updateIndexStatus() {
            fetch('/api/index/status')
                .then(response => response.json())
                .then(data => {
                    if (data.loaded) {
                        indexStatusDiv.innerHTML = `
                            <strong>Index loaded:</strong> ${data.total_documents} documents, 
                            ${data.total_terms} terms
                        `;
                    } else {
                        indexStatusDiv.innerHTML = 'No index loaded';
                    }
                });
        }
        
        buildForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(buildForm);
            const data = {
                corpus_dir: formData.get('corpusDir'),
                use_stemming: document.getElementById('useStemming').checked,
                remove_stopwords: document.getElementById('removeStopwords').checked
            };
            
            try {
                const response = await fetch('/api/index/build', {
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
                
                showStatus('Index built successfully!', 'success');
                updateIndexStatus();
                
                // Show statistics
                if (result.statistics) {
                    statsDiv.innerHTML = `
                        <h4>Index Statistics:</h4>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${result.statistics.total_documents}</div>
                                <div class="stat-label">Documents</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${result.statistics.total_terms}</div>
                                <div class="stat-label">Terms</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${result.statistics.index_size}</div>
                                <div class="stat-label">Index Size</div>
                            </div>
                        </div>
                    `;
                    resultsDiv.classList.add('show');
                }
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            }
        });
        
        loadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(loadForm);
            const data = {
                index_file: formData.get('indexFile')
            };
            
            try {
                const response = await fetch('/api/index/load', {
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
                
                if (result.statistics) {
                    statsDiv.innerHTML = `
                        <h4>Index Statistics:</h4>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${result.statistics.total_documents}</div>
                                <div class="stat-label">Documents</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${result.statistics.total_terms}</div>
                                <div class="stat-label">Terms</div>
                            </div>
                        </div>
                    `;
                    resultsDiv.classList.add('show');
                }
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            }
        });
        
        queryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(queryForm);
            const data = {
                term: formData.get('queryTerm')
            };
            
            try {
                const response = await fetch('/api/index/query', {
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
                
                queryResultsDiv.innerHTML = `
                    <h4>Query Results for "${data.term}":</h4>
                    <p><strong>Found in ${result.document_count} documents</strong></p>
                    <div class="doc-list">
                        ${result.document_ids.slice(0, 100).map(id => 
                            `<div class="doc-item">Document ${id}</div>`
                        ).join('')}
                        ${result.document_count > 100 ? 
                            `<div class="doc-item">... and ${result.document_count - 100} more</div>` : ''}
                    </div>
                `;
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


@app.route('/api/index/build', methods=['POST'])
def build_index():
    global index_instance, index_path
    
    try:
        data = request.json
        corpus_dir = data.get('corpus_dir', 'corpus')
        use_stemming = data.get('use_stemming', False)
        remove_stopwords = data.get('remove_stopwords', False)
        
        index_instance = BooleanIndex()
        
        tokenizer = Tokenizer(
            lowercase=True,
            min_length=1,
            remove_stopwords=remove_stopwords
        )
        
        stemmer = None
        if use_stemming:
            stemmer = Stemmer(language='russian')
        
        corpus_path = Path(corpus_dir)
        build_stats = index_instance.build_from_corpus(corpus_path, tokenizer, stemmer)

        index_path = Path('boolean_index.json')
        index_instance.save(index_path)
        
        return jsonify({
            'success': True,
            'statistics': build_stats['index_statistics'],
            'build_stats': build_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/index/load', methods=['POST'])
def load_index():
    global index_instance, index_path
    
    try:
        data = request.json
        index_file = data.get('index_file', 'boolean_index.json')
        
        index_instance = BooleanIndex()
        index_path = Path(index_file)
        index_instance.load(index_path)
        
        return jsonify({
            'success': True,
            'statistics': index_instance.get_index_statistics()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/index/status', methods=['GET'])
def get_status():
    global index_instance
    
    if index_instance is None:
        return jsonify({'loaded': False})
    
    stats = index_instance.get_index_statistics()
    return jsonify({
        'loaded': True,
        'total_documents': stats['total_documents'],
        'total_terms': stats['total_terms']
    })


@app.route('/api/index/query', methods=['POST'])
def query_index():
    global index_instance
    
    if index_instance is None:
        return jsonify({'error': 'No index loaded'}), 400
    
    try:
        data = request.json
        term = data.get('term', '')
        
        if not term:
            return jsonify({'error': 'No term provided'}), 400
        
        doc_ids = index_instance.get_documents(term)
        doc_list = sorted(list(doc_ids))
        
        return jsonify({
            'term': term,
            'document_count': len(doc_ids),
            'document_ids': doc_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
