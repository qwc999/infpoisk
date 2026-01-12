from flask import Flask, render_template_string, request, jsonify
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from tokenizer import Tokenizer

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tokenizer - Information Retrieval System</title>
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
            border-bottom: 3px solid #2196F3;
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
        input[type="text"], textarea {
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
            background-color: #2196F3;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #1976D2;
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
        .tokens {
            margin-top: 15px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            max-height: 400px;
            overflow-y: auto;
        }
        .token {
            display: inline-block;
            margin: 2px;
            padding: 4px 8px;
            background: #e3f2fd;
            border-radius: 3px;
            font-size: 12px;
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
            background-color: #2196F3;
            color: white;
        }
        .freq-table tr:hover {
            background-color: #f5f5f5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Text Tokenizer</h1>
        
        <form id="tokenizeForm">
            <div class="form-group">
                <label for="inputText">Input Text:</label>
                <textarea id="inputText" name="inputText" required placeholder="Enter text to tokenize..."></textarea>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="lowercase" name="lowercase" checked>
                    Convert to lowercase
                </label>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="removePunctuation" name="removePunctuation">
                    Remove punctuation
                </label>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="removeStopwords" name="removeStopwords">
                    Remove stop words
                </label>
            </div>
            
            <div class="form-group">
                <label for="minLength">Minimum Token Length:</label>
                <input type="number" id="minLength" name="minLength" value="1" min="1" max="20">
            </div>
            
            <button type="submit">Tokenize</button>
        </form>
        
        <div id="results" class="results">
            <h3>Tokenization Results</h3>
            
            <div id="stats" class="stats"></div>
            
            <div id="tokens" class="tokens"></div>
            
            <div id="frequencies"></div>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('tokenizeForm');
        const resultsDiv = document.getElementById('results');
        const statsDiv = document.getElementById('stats');
        const tokensDiv = document.getElementById('tokens');
        const frequenciesDiv = document.getElementById('frequencies');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = {
                text: formData.get('inputText'),
                lowercase: document.getElementById('lowercase').checked,
                remove_punctuation: document.getElementById('removePunctuation').checked,
                remove_stopwords: document.getElementById('removeStopwords').checked,
                min_length: parseInt(formData.get('minLength'))
            };
            
            try {
                const response = await fetch('/api/tokenize', {
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
                        <span class="stats-label">Total Tokens:</span>
                        <span class="stats-value">${result.total_tokens}</span>
                    </div>
                    <div class="stats-item">
                        <span class="stats-label">Unique Tokens:</span>
                        <span class="stats-value">${result.unique_tokens}</span>
                    </div>
                `;
                
                // Display tokens
                tokensDiv.innerHTML = '<h4>Tokens:</h4>';
                result.tokens.forEach(token => {
                    const span = document.createElement('span');
                    span.className = 'token';
                    span.textContent = token;
                    tokensDiv.appendChild(span);
                });
                
                // Display frequencies
                if (result.frequencies && Object.keys(result.frequencies).length > 0) {
                    const sortedFreq = Object.entries(result.frequencies)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 20);
                    
                    let tableHTML = '<h4>Top 20 Most Frequent Tokens:</h4>';
                    tableHTML += '<table class="freq-table"><thead><tr><th>Token</th><th>Frequency</th></tr></thead><tbody>';
                    sortedFreq.forEach(([token, freq]) => {
                        tableHTML += `<tr><td>${token}</td><td>${freq}</td></tr>`;
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


@app.route('/api/tokenize', methods=['POST'])
def tokenize():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'})
        
        tokenizer = Tokenizer(
            lowercase=data.get('lowercase', True),
            remove_punctuation=data.get('remove_punctuation', False),
            min_length=data.get('min_length', 1),
            remove_stopwords=data.get('remove_stopwords', False)
        )
        
        tokens = tokenizer.tokenize(text)
        frequencies = tokenizer.get_token_frequencies(tokens)
        vocabulary = tokenizer.get_vocabulary(tokens)
        
        return jsonify({
            'tokens': tokens,
            'total_tokens': len(tokens),
            'unique_tokens': len(vocabulary),
            'frequencies': frequencies
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tokenize/corpus', methods=['POST'])
def tokenize_corpus():
    try:
        data = request.json
        corpus_dir = data.get('corpus_dir', 'corpus')
        
        tokenizer = Tokenizer(
            lowercase=data.get('lowercase', True),
            remove_punctuation=data.get('remove_punctuation', False),
            min_length=data.get('min_length', 1),
            remove_stopwords=data.get('remove_stopwords', False)
        )
        
        corpus_path = Path(corpus_dir)
        output_dir = Path(data.get('output_dir', 'tokenized_output'))
        
        stats = tokenizer.tokenize_corpus(corpus_path, output_dir)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
