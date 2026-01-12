from flask import Flask, render_template_string, request, jsonify, send_file
import json
import base64
import io
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from zipf_analyzer import ZipfAnalyzer
from tokenizer import Tokenizer

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zipf's Law Analyzer - Information Retrieval System</title>
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
            border-bottom: 3px solid #9C27B0;
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
            background-color: #9C27B0;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #7B1FA2;
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
            color: #9C27B0;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .top-words {
            margin-top: 15px;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }
        .word-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .word-table th, .word-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .word-table th {
            background-color: #9C27B0;
            color: white;
        }
        .word-table tr:hover {
            background-color: #f5f5f5;
        }
        .plot-container {
            margin-top: 20px;
            text-align: center;
        }
        .plot-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Zipf's Law Analyzer</h1>
        
        <form id="zipfForm">
            <div class="form-group">
                <label for="inputText">Input Text:</label>
                <textarea id="inputText" name="inputText" required placeholder="Enter text to analyze..."></textarea>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="tokenize" name="tokenize" checked>
                    Tokenize input text first
                </label>
            </div>
            
            <button type="submit">Analyze Zipf's Law</button>
        </form>
        
        <div id="results" class="results">
            <h3>Analysis Results</h3>
            
            <div id="stats" class="stats"></div>
            
            <div id="topWords" class="top-words"></div>
            
            <div id="plots" class="plot-container"></div>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('zipfForm');
        const resultsDiv = document.getElementById('results');
        const statsDiv = document.getElementById('stats');
        const topWordsDiv = document.getElementById('topWords');
        const plotsDiv = document.getElementById('plots');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = {
                text: formData.get('inputText'),
                tokenize: document.getElementById('tokenize').checked
            };
            
            try {
                const response = await fetch('/api/analyze', {
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
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">${result.total_tokens.toLocaleString()}</div>
                            <div class="stat-label">Total Tokens</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${result.unique_tokens.toLocaleString()}</div>
                            <div class="stat-label">Unique Tokens</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${result.zipf_constant.toFixed(2)}</div>
                            <div class="stat-label">Zipf Constant (C)</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${result.correlation.toFixed(4)}</div>
                            <div class="stat-label">Correlation</div>
                        </div>
                    </div>
                `;
                
                // Display top words
                if (result.top_words && result.top_words.length > 0) {
                    let tableHTML = '<h4>Top 10 Words:</h4>';
                    tableHTML += '<table class="word-table"><thead><tr><th>Rank</th><th>Token</th><th>Frequency</th><th>Relative Frequency</th></tr></thead><tbody>';
                    result.top_words.forEach(word => {
                        tableHTML += `<tr>
                            <td>${word.rank}</td>
                            <td>${word.token}</td>
                            <td>${word.frequency.toLocaleString()}</td>
                            <td>${(word.relative_frequency * 100).toFixed(2)}%</td>
                        </tr>`;
                    });
                    tableHTML += '</tbody></table>';
                    topWordsDiv.innerHTML = tableHTML;
                }
                
                // Display plots if available
                if (result.plot1 && result.plot2) {
                    plotsDiv.innerHTML = `
                        <h4>Visualizations:</h4>
                        <div style="margin-bottom: 20px;">
                            <h5>Zipf's Law (Log-Log Scale)</h5>
                            <img src="data:image/png;base64,${result.plot1}" alt="Zipf's Law Plot">
                        </div>
                        <div>
                            <h5>Rank vs Frequency (Top 100)</h5>
                            <img src="data:image/png;base64,${result.plot2}" alt="Rank Frequency Plot">
                        </div>
                    `;
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


@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        text = data.get('text', '')
        tokenize = data.get('tokenize', True)
        
        if not text:
            return jsonify({'error': 'No text provided'})
        
        analyzer = ZipfAnalyzer()
        
        if tokenize:
            tokenizer = Tokenizer(lowercase=True, min_length=1)
            tokens = tokenizer.tokenize(text)
        else:
            tokens = text.split()
        
        analyzer.calculate_frequencies(tokens)
        analyzer.get_ranked_frequencies()
        stats = analyzer.get_statistics()

        plot1_base64 = None
        plot2_base64 = None
        
        try:
            import io
            import base64

            plot1_path = analyzer.plot_zipf_law(Path('temp_zipf1.png'), max_rank=1000)
            with open(plot1_path, 'rb') as f:
                plot1_base64 = base64.b64encode(f.read()).decode('utf-8')
            Path(plot1_path).unlink()

            plot2_path = analyzer.plot_rank_frequency(Path('temp_zipf2.png'), max_rank=100)
            with open(plot2_path, 'rb') as f:
                plot2_base64 = base64.b64encode(f.read()).decode('utf-8')
            Path(plot2_path).unlink()
        except Exception as e:
            pass
        
        return jsonify({
            **stats,
            'plot1': plot1_base64,
            'plot2': plot2_base64
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
