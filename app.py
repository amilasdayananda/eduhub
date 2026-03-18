import time
import requests
from flask import Flask, render_template, request, jsonify
from ddgs import DDGS # Updated version of duckduckgo_search

app = Flask(__name__)

def search_logic(query):
    results = []
    
    # 1. TRY DUCKDUCKGO (Primary)
    try:
        # Using a small delay is the secret for Namecheap
        time.sleep(0.75) 
        with DDGS() as ddgs:
            # We search for diverse file types
            q = f"{query} (filetype:pdf OR filetype:xlsx OR filetype:docx)"
            # 'lite' backend is less likely to be blocked than 'api'
            for r in ddgs.text(q, backend="lite", max_results=10):
                results.append({
                    "title": r['title'],
                    "url": r['href'],
                    "snippet": r['body'],
                    "file_type": "pdf" if ".pdf" in r['href'].lower() else "doc"
                })
    except Exception as e:
        print(f"Source 1 (DDG) Blocked: {e}")

    # 2. BACKUP: WIKIPEDIA (If DDG fails, always show something)
    if not results:
        try:
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=5&format=json"
            wiki_data = requests.get(wiki_url).json()
            for i in range(len(wiki_data[1])):
                results.append({
                    "title": wiki_data[1][i],
                    "url": wiki_data[3][i],
                    "snippet": "Educational article found in global archives.",
                    "file_type": "web"
                })
        except: pass

    return results

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    if not query: return jsonify([])
    
    data = search_logic(query)
    return jsonify(data)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
