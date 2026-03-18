import time
import requests
import sqlite3
import os
from flask import Flask, render_template, request, jsonify
from duckduckgo_search import DDGS

app = Flask(__name__)

# Render-safe Database Path
DB_PATH = '/opt/render/project/src/favorites.db' if os.path.exists('/opt/render/project/src/') else 'favorites.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS favs (id INTEGER PRIMARY KEY, title TEXT, url TEXT, type TEXT)')
    conn.close()

init_db()

def search_logic(query):
    results = []
    # 1. PRIMARY: DuckDuckGo
    try:
        with DDGS() as ddgs:
            # We force it to find documents
            q = f"{query} (filetype:pdf OR filetype:xlsx OR filetype:docx)"
            ddgs_res = ddgs.text(q, backend="lite", max_results=15)
            for r in ddgs_res:
                link = r['href'].lower()
                ftype = 'pdf' if '.pdf' in link else ('excel' if '.xls' in link else 'doc')
                results.append({"title": r['title'], "url": r['href'], "snippet": r['body'], "file_type": ftype, "source": "Global"})
    except Exception as e:
        print(f"DDG Error: {e}")

    # 2. BACKUP: Wikipedia (Always works)
    if not results:
        try:
            wiki = requests.get(f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=5&format=json").json()
            for i in range(len(wiki[1])):
                results.append({"title": wiki[1][i], "url": wiki[3][i], "snippet": "Educational summary from archives.", "file_type": "web", "source": "Wiki"})
        except: pass
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    return jsonify(search_logic(q)) if q else jsonify([])

@app.route('/api/save', methods=['POST'])
def save_fav():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO favs (title, url, type) VALUES (?, ?, ?)", (data['title'], data['url'], data['type']))
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

@app.route('/api/get_favs')
def get_favs():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM favs").fetchall()
    conn.close()
    return jsonify([{"title": r[1], "url": r[2], "type": r[3]} for r in rows])

if __name__ == '__main__':
    app.run(debug=True)
