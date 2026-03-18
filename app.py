import time
import requests
from flask import Flask, render_template, request, jsonify
from duckduckgo_search import DDGS  # Fixed Import

app = Flask(__name__)

def search_logic(query):
    results = []
    
    # 1. PRIMARY SEARCH: DuckDuckGo (Free & Unlimited)
    try:
        # Added a small delay to mimic human behavior on the server
        time.sleep(1) 
        with DDGS() as ddgs:
            # We specifically look for PDF, Excel, and Word files
            search_query = f"{query} (filetype:pdf OR filetype:xlsx OR filetype:docx)"
            
            # Use 'lite' backend - it is much more stable for server-side scraping
            response = ddgs.text(search_query, backend="lite", max_results=15)
            
            for r in response:
                link = r['href'].lower()
                ftype = 'web'
                if '.pdf' in link: ftype = 'pdf'
                elif '.xls' in link: ftype = 'excel'
                elif '.doc' in link: ftype = 'doc'
                elif '.ppt' in link: ftype = 'powerpoint'

                results.append({
                    "title": r['title'],
                    "url": r['href'],
                    "snippet": r['body'],
                    "file_type": ftype,
                    "source": "Global Edu Index"
                })
    except Exception as e:
        print(f"Primary search failed: {e}")

    # 2. BACKUP SEARCH: Wikipedia (If primary fails, always show something)
    if not results:
        try:
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=5&format=json"
            wiki_data = requests.get(wiki_url, timeout=5).json()
            for i in range(len(wiki_data[1])):
                results.append({
                    "title": wiki_data[1][i],
                    "url": wiki_data[3][i],
                    "snippet": "Academic article found in global archives.",
                    "file_type": "web",
                    "source": "Wikipedia"
                })
        except:
            pass

    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    data = search_logic(query)
    return jsonify(data)

if __name__ == '__main__':
    # Render uses Gunicorn, but this allows for local testing too
    app.run(debug=True)
