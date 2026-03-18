import requests
from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

def get_archive_materials(query, level):
    """
    Searches Archive.org specifically for Office and PDF formats.
    """
    results = []
    # Refine query based on student level
    search_term = f"{query} {level}"
    
    # We ask for specific formats in the Archive.org query
    url = f"https://archive.org/advancedsearch.php?q={search_term}&fl[]=title,identifier,format&output=json&rows=15"
    
    try:
        response = requests.get(url, timeout=5).json()
        docs = response.get('response', {}).get('docs', [])
        
        for item in docs:
            # Archive stores multiple formats in a list or string
            formats = str(item.get('format', '')).lower()
            
            # Map formats to our dashboard icons
            ftype = 'web'
            if 'pdf' in formats: ftype = 'pdf'
            elif 'excel' in formats or 'xlsx' in formats: ftype = 'excel'
            elif 'word' in formats or 'docx' in formats: ftype = 'doc'
            elif 'powerpoint' in formats or 'pptx' in formats: ftype = 'ppt'

            results.append({
                "title": item.get('title', 'Educational Resource'),
                "url": f"https://archive.org/details/{item['identifier']}",
                "type": ftype,
                "level": level,
                "source": "Internet Archive"
            })
    except:
        pass
    return results

def get_web_articles(query, level):
    """
    Fetches high-quality web pages from Wikipedia.
    """
    results = []
    url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query} {level}&limit=5&format=json"
    try:
        data = requests.get(url, timeout=5).json()
        for i in range(len(data[1])):
            results.append({
                "title": data[1][i],
                "url": data[3][i],
                "type": "web",
                "level": level,
                "source": "Wikipedia"
            })
    except:
        pass
    return results

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    level = request.args.get('level', 'Beginner')
    if not query: return jsonify([])

    # Run searches in parallel for "Anti-Gravity" speed
    with ThreadPoolExecutor() as executor:
        f1 = executor.submit(get_archive_materials, query, level)
        f2 = executor.submit(get_web_articles, query, level)
        
        # Combine everything
        combined = f1.result() + f2.result()
    
    return jsonify(combined)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
