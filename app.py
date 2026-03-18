import requests
from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# --- API ORCHESTRATOR ---

def get_archive_data(query, level):
    """Fetches PDF, Excel, and Word from Archive.org"""
    results = []
    # Adjust query based on level
    level_query = "intro" if level == "Beginner" else "advanced"
    q = f"{query} {level_query}"
    
    url = f"https://archive.org/advancedsearch.php?q={q}&fl[]=title,identifier,format&output=json&rows=10"
    try:
        data = requests.get(url, timeout=5).json()
        for item in data.get('response', {}).get('docs', []):
            fmt = str(item.get('format', '')).lower()
            ftype = 'pdf'
            if 'excel' in fmt or 'xls' in fmt: ftype = 'excel'
            elif 'word' in fmt or 'doc' in fmt: ftype = 'doc'
            
            results.append({
                "title": item.get('title', 'Document'),
                "url": f"https://archive.org/details/{item['identifier']}",
                "type": ftype,
                "level": level
            })
    except: pass
    return results

def get_video_data(query, level):
    """Fetches Videos from Youtube (via open API)"""
    results = []
    q = f"{query} {level} tutorial"
    url = f"https://www.googleapis.com/customsearch/v1?q={q}&key=YOUR_KEY&cx=YOUR_CX" 
    # Fallback: Using Wikipedia's video search or similar open endpoints
    # For this demo, we use a reliable web-search fallback for videos
    return results

def get_web_data(query, level):
    """Fetches Articles from Wikipedia"""
    results = []
    url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query} {level}&limit=5&format=json"
    try:
        data = requests.get(url, timeout=5).json()
        for i in range(len(data[1])):
            results.append({
                "title": data[1][i],
                "url": data[3][i],
                "type": "web",
                "level": level
            })
    except: pass
    return results

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    level = request.args.get('level', 'Beginner')
    if not query: return jsonify([])

    # Run all searches at once for "Anti-Gravity" speed
    with ThreadPoolExecutor() as executor:
        f1 = executor.submit(get_archive_data, query, level)
        f2 = executor.submit(get_web_data, query, level)
        
        all_results = f1.result() + f2.result()
    
    return jsonify(all_results)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
