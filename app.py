import requests
import sqlite3
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Database for Favorites
DB_PATH = 'favorites.db'
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS favs (id INTEGER PRIMARY KEY, title TEXT, url TEXT, type TEXT)')
init_db()

def get_edu_resources(query):
    results = []
    
    # SOURCE 1: Internet Archive (Direct PDF & Document Search)
    try:
        # Search for PDFs and Documents specifically
        archive_url = f"https://archive.org/advancedsearch.php?q={query}+AND+mediatype:(texts)&fl[]=title,identifier,format&output=json&rows=10"
        archive_data = requests.get(archive_url, timeout=5).json()
        
        for item in archive_data.get('response', {}).get('docs', []):
            identifier = item.get('identifier')
            # Create a direct link to the document
            results.append({
                "title": item.get('title', 'Educational Document'),
                "url": f"https://archive.org/details/{identifier}",
                "snippet": f"Full text archive resource from Internet Archive.",
                "file_type": "pdf", # Archive is mostly PDF/Text
                "source": "Archive.org"
            })
    except: pass

    # SOURCE 2: Wikipedia API (High Reliability fallback)
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=5&format=json"
        wiki_data = requests.get(wiki_url, timeout=5).json()
        for i in range(len(wiki_data[1])):
            results.append({
                "title": wiki_data[1][i],
                "url": wiki_data[3][i],
                "snippet": "Verified educational summary and references.",
                "file_type": "web",
                "source": "Wikipedia"
            })
    except: pass

    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q: return jsonify([])
    return jsonify(get_edu_resources(q))

@app.route('/api/save', methods=['POST'])
def save_fav():
    data = request.json
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO favs (title, url, type) VALUES (?, ?, ?)", (data['title'], data['url'], data['type']))
    return jsonify({"status": "saved"})

if __name__ == '__main__':
    app.run(debug=True)
