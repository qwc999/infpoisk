from flask import Flask, render_template_string, request, jsonify
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from stemmer import Stemmer
from tokenizer import Tokenizer

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stemmer - Information Retrieval System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
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
            border-bottom: 3px solid #FF9800;
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
        input[type="text"], textarea, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }
        textarea {
            min-height: 200px;
            resize: vertical;
            font-family: monospace;
        }
        input[type="checkbox"] {
            margin-right: 5px;
        }
        button {
            background-color: #FF9800;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #F57C00;
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
        .stats-item {
            margin: 8px 0;
            padding: 8px;
        }
        .stats-label {
            font-weight: bold;
            color: #666;
        }
        .stats-value {
            color: #333;
            font-size: 18px;
        }
        .stems {
            margin-top: 15px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            max-height: 400px;
            overflow-y: auto;
        }
        .stem {
            display: inline-block;
            margin: 2px;
            padding: 4px 8px;
            background: #fff3e0;
            border-radius: 3px;
            font-size: 12px;
        }
        .mapping {
            margin-top: 15px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
        }
        .mapping-item {
            padding: 5px;
            border-bottom: 1px solid #eee;
        }
        .freq-table {
            margin-top: 15px;
            width: 100%;
            border-collapse: collapse;
        }
        .freq-table th, .freq-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .freq-table th {
            background-color: #FF9800;
            color: white;
        }
        .freq-table tr:hover {
            background-color: #f5f5f5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Text Stemmer</h1>
        
        <form id="stemForm">
            <div class="form-group">
                <label for="inputText">Input Text:</label>
                <textarea id="inputText" name="inputText" required placeholder="Enter text to stem..."></textarea>
            </div>
            
            <div class="form-group">
                <label for="language">Language:</label>
                <select id="language" name="language">
                    <option value="russian">Russian</option>
                    <option value="english">English</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="tokenize" name="tokenize" checked>
                    Tokenize input text first
                </label>
            </div>
            
            <button type="submit">Stem</button>
        </form>
        
        <div id="results" class="results">
            <h3>Stemming Results</h3>
            
            <div id="stats" class="stats"></div>
            
            <div id="stems" class="stems"></div>
            
            <div id="mapping" class="mapping"></div>
            
            <div id="frequencies"></div>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('stemForm');
        const resultsDiv = document.getElementById('results');
        const statsDiv = document.getElementById('stats');
        const stemsDiv = document.getElementById('stems');
        const mappingDiv = document.getElementById('mapping');
        const frequenciesDiv = document.getElementById('frequencies');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = {
                text: formData.get('inputText'),
                language: formData.get('language'),
                tokenize: document.getElementById('tokenize').checked
            };
            
            try {
                const response = await fetch('/api/stem', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.error) {
                    alert('Error: ' + result.error);
                    return;
                }
                
                // Display statistics
                statsDiv.innerHTML = `
                    <div class="stats-item">
                        <span class="stats-label">Total Stems:</span>
                        <span class="stats-value">${result.total_stems}</span>
                    </div>
                    <div class="stats-item">
                        <span class="stats-label">Unique Stems:</span>
                        <span class="stats-value">${result.unique_stems}</span>
                    </div>
                `;
                
                // Display stems
                stemsDiv.innerHTML = '<h4>Stems:</h4>';
                result.stems.forEach(stem => {
                    const span = document.createElement('span');
                    span.className = 'stem';
                    span.textContent = stem;
                    stemsDiv.appendChild(span);
                });
                
                // Display token to stem mapping
                if (result.token_to_stem && Object.keys(result.token_to_stem).length > 0) {
                    mappingDiv.innerHTML = '<h4>Token to Stem Mapping (sample):</h4>';
                    const entries = Object.entries(result.token_to_stem).slice(0, 50);
                    entries.forEach(([token, stem]) => {
                        const div = document.createElement('div');
                        div.className = 'mapping-item';
                        div.textContent = `${token} → ${stem}`;
                        mappingDiv.appendChild(div);
                    });
                }
                
                // Display frequencies
                if (result.stem_frequencies && Object.keys(result.stem_frequencies).length > 0) {
                    const sortedFreq = Object.entries(result.stem_frequencies)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 20);
                    
                    let tableHTML = '<h4>Top 20 Most Frequent Stems:</h4>';
                    tableHTML += '<table class="freq-table"><thead><tr><th>Stem</th><th>Frequency</th></tr></thead><tbody>';
                    sortedFreq.forEach(([stem, freq]) => {
                        tableHTML += `<tr><td>${stem}</td><td>${freq}</td></tr>`;
                    });
                    tableHTML += '</tbody></table>';
                    frequenciesDiv.innerHTML = tableHTML;
                }
                
                resultsDiv.classList.add('show');
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/stem', methods=['POST'])
def stem():
    try:
        data = request.json
        text = data.get('text', '')
        language = data.get('language', 'russian')
        tokenize = data.get('tokenize', True)
        
        if not text:
            return jsonify({'error': 'No text provided'})
        
        stemmer = Stemmer(language=language)
        
        if tokenize:
            tokenizer = Tokenizer(lowercase=True, min_length=1)
            tokens = tokenizer.tokenize(text)
        else:
            tokens = text.split()
        
        result = stemmer.process_document(tokens)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
