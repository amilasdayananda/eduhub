import requests
from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

def search_archive(query, level, filter_type):
    """Searches for PDF, Excel, Word, and PPT."""
    results = []
    # If user selected a specific file type, we add it to the search
    q = f"{query} {level}"
    if filter_type and filter_type != 'all':
        q += f" format:{filter_type}"
    
    url = f"https://archive.org/advancedsearch.php?q={q}&fl[]=title,identifier,format&output=json&rows=20"
    try:
        data = requests.get(url, timeout=5).json()
        for item in data.get('response', {}).get('docs', []):
            formats = str(item.get('format', '')).lower()
            ftype = 'document'
            if 'pdf' in formats: ftype = 'pdf'
            elif 'excel' in formats or 'xls' in formats: ftype = 'excel'
            elif 'word' in formats or 'doc' in formats: ftype = 'document'
            elif 'powerpoint' in formats or 'ppt' in formats: ftype = 'ppt'
            
            results.append({
                "title": item.get('title', 'Resource'),
                "url": f"https://archive.org/details/{item['identifier']}",
                "type": ftype,
                "level": level
            })
    except: pass
    return results

def search_web(query, level):
    """Searches for Articles and Web Pages."""
    results = []
    url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query} {level}&limit=10&format=json"
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
    filter_type = request.args.get('type', 'all')
    
    if not query: return jsonify([])

    with ThreadPoolExecutor() as executor:
        f1 = executor.submit(search_archive, query, level, filter_type)
        f2 = executor.submit(search_web, query, level)
        
        combined = f1.result() + f2.result()
    
    # Final filter to ensure only requested type is shown
    if filter_type != 'all':
        combined = [r for r in combined if r['type'] == filter_type]
        
    return jsonify(combined)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
