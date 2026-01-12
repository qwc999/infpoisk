from flask import Flask, render_template_string, request, jsonify
import json
import threading
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from web_crawler import WebCrawler

app = Flask(__name__)

crawler_instance = None
crawl_thread = None
crawl_status = {
    'running': False,
    'progress': 0,
    'stats': None,
    'error': None
}


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Crawler - Information Retrieval System</title>
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
            border-bottom: 3px solid #4CAF50;
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
        input[type="text"], input[type="number"], textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            box-sizing: border-box;
        }
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 4px;
            display: none;
        }
        .status.running {
            background-color: #e3f2fd;
            border-left: 4px solid #2196F3;
            display: block;
        }
        .status.success {
            background-color: #e8f5e9;
            border-left: 4px solid #4CAF50;
            display: block;
        }
        .status.error {
            background-color: #ffebee;
            border-left: 4px solid #f44336;
            display: block;
        }
        .stats {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
        }
        .stats h3 {
            margin-top: 0;
            color: #333;
        }
        .stats-item {
            margin: 10px 0;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }
        .stats-label {
            font-weight: bold;
            color: #666;
        }
        .stats-value {
            color: #333;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Web Crawler</h1>
        
        <form id="crawlForm">
            <div class="form-group">
                <label for="seedUrls">Seed URLs (one per line):</label>
                <textarea id="seedUrls" name="seedUrls" required placeholder="https://example.com/page1&#10;https://example.com/page2"></textarea>
            </div>
            
            <div class="form-group">
                <label for="maxPages">Maximum Pages:</label>
                <input type="number" id="maxPages" name="maxPages" value="100" min="1" max="10000" required>
            </div>
            
            <div class="form-group">
                <label for="maxDepth">Maximum Depth:</label>
                <input type="number" id="maxDepth" name="maxDepth" value="3" min="1" max="10" required>
            </div>
            
            <div class="form-group">
                <label for="outputDir">Output Directory:</label>
                <input type="text" id="outputDir" name="outputDir" value="corpus/crawled" required>
            </div>
            
            <div class="form-group">
                <label for="minContentLength">Minimum Content Length:</label>
                <input type="number" id="minContentLength" name="minContentLength" value="500" min="100" required>
            </div>
            
            <button type="submit" id="startBtn">Start Crawl</button>
            <button type="button" id="stopBtn" disabled>Stop Crawl</button>
        </form>
        
        <div id="status" class="status"></div>
        
        <div id="stats" class="stats" style="display: none;">
            <h3>Crawl Statistics</h3>
            <div id="statsContent"></div>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('crawlForm');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusDiv = document.getElementById('status');
        const statsDiv = document.getElementById('stats');
        const statsContent = document.getElementById('statsContent');
        
        let statusInterval = null;
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const seedUrls = formData.get('seedUrls').split('\\n').filter(url => url.trim());
            const data = {
                seedUrls: seedUrls,
                maxPages: parseInt(formData.get('maxPages')),
                maxDepth: parseInt(formData.get('maxDepth')),
                outputDir: formData.get('outputDir'),
                minContentLength: parseInt(formData.get('minContentLength'))
            };
            
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusDiv.className = 'status running';
            statusDiv.textContent = 'Crawling in progress...';
            statsDiv.style.display = 'none';
            
            try {
                const response = await fetch('/api/crawl/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusInterval = setInterval(checkStatus, 2000);
                } else {
                    statusDiv.className = 'status error';
                    statusDiv.textContent = 'Error: ' + (result.error || 'Unknown error');
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                }
            } catch (error) {
                statusDiv.className = 'status error';
                statusDiv.textContent = 'Error: ' + error.message;
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        });
        
        stopBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/crawl/stop', { method: 'POST' });
                stopBtn.disabled = true;
            } catch (error) {
                console.error('Error stopping crawl:', error);
            }
        });
        
        async function checkStatus() {
            try {
                const response = await fetch('/api/crawl/status');
                const status = await response.json();
                
                if (!status.running) {
                    clearInterval(statusInterval);
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                    
                    if (status.error) {
                        statusDiv.className = 'status error';
                        statusDiv.textContent = 'Error: ' + status.error;
                    } else if (status.stats) {
                        statusDiv.className = 'status success';
                        statusDiv.textContent = 'Crawl completed successfully!';
                        displayStats(status.stats);
                    }
                } else {
                    statusDiv.textContent = `Crawling in progress... Pages crawled: ${status.progress || 0}`;
                }
            } catch (error) {
                console.error('Error checking status:', error);
            }
        }
        
        function displayStats(stats) {
            statsDiv.style.display = 'block';
            statsContent.innerHTML = `
                <div class="stats-item">
                    <span class="stats-label">Documents Saved:</span>
                    <span class="stats-value">${stats.documents_saved || 0}</span>
                </div>
                <div class="stats-item">
                    <span class="stats-label">URLs Visited:</span>
                    <span class="stats-value">${stats.urls_visited || 0}</span>
                </div>
                <div class="stats-item">
                    <span class="stats-label">URLs Failed:</span>
                    <span class="stats-value">${stats.urls_failed || 0}</span>
                </div>
                <div class="stats-item">
                    <span class="stats-label">URLs Skipped:</span>
                    <span class="stats-value">${stats.urls_skipped || 0}</span>
                </div>
                <div class="stats-item">
                    <span class="stats-label">Pages Crawled:</span>
                    <span class="stats-value">${stats.pages_crawled || 0}</span>
                </div>
                <div class="stats-item">
                    <span class="stats-label">Start Time:</span>
                    <span class="stats-value">${stats.start_time || 'N/A'}</span>
                </div>
                <div class="stats-item">
                    <span class="stats-label">End Time:</span>
                    <span class="stats-value">${stats.end_time || 'N/A'}</span>
                </div>
            `;
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/crawl/start', methods=['POST'])
def start_crawl():
    global crawler_instance, crawl_thread, crawl_status
    
    if crawl_status['running']:
        return jsonify({'success': False, 'error': 'Crawl already in progress'})
    
    data = request.json
    seed_urls = data.get('seed_urls', [])
    max_pages = data.get('max_pages', 100)
    max_depth = data.get('max_depth', 3)
    output_dir = data.get('output_dir', 'corpus/crawled')
    min_content_length = data.get('min_content_length', 500)
    
    if not seed_urls:
        return jsonify({'success': False, 'error': 'No seed URLs provided'})
    
    crawl_status = {
        'running': True,
        'progress': 0,
        'stats': None,
        'error': None
    }
    
    def crawl_worker():
        global crawler_instance, crawl_status
        try:
            crawler_instance = WebCrawler(output_dir=output_dir)
            crawler_instance.min_content_length = min_content_length
            
            stats = crawler_instance.crawl(
                seed_urls=seed_urls,
                max_pages=max_pages,
                max_depth=max_depth
            )
            
            crawl_status['running'] = False
            crawl_status['stats'] = stats
        except Exception as e:
            crawl_status['running'] = False
            crawl_status['error'] = str(e)
    
    crawl_thread = threading.Thread(target=crawl_worker)
    crawl_thread.daemon = True
    crawl_thread.start()
    
    return jsonify({'success': True})


@app.route('/api/crawl/stop', methods=['POST'])
def stop_crawl():
    global crawl_status
    crawl_status['running'] = False
    return jsonify({'success': True})


@app.route('/api/crawl/status', methods=['GET'])
def get_status():
    global crawl_status
    return jsonify(crawl_status)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
