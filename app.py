import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def stealth_search(query):
    """Direct Lite Search - Bypasses blocks and works on Render/Namecheap."""
    # Force search for specific educational filetypes
    search_q = f"{query} filetype:pdf OR filetype:xlsx OR filetype:docx"
    url = f"https://html.duckduckgo.com/html/?q={search_q}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }

    results = []
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200: return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extracting results from DDG Lite HTML structure
        for link in soup.find_all('a', class_='result__a', limit=15):
            title = link.text
            href = link['href']
            
            # Detect Type
            ftype = 'web'
            if '.pdf' in href.lower(): ftype = 'pdf'
            elif '.xls' in href.lower(): ftype = 'excel'
            elif '.doc' in href.lower(): ftype = 'doc'

            results.append({
                "title": title,
                "url": href,
                "file_type": ftype,
                "snippet": "Educational resource found in global archives."
            })
        
        # Fallback to Wikipedia if web search is dry
        if not results:
            wiki = requests.get(f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=3&format=json").json()
            for i in range(len(wiki[1])):
                results.append({"title": wiki[1][i], "url": wiki[3][i], "file_type": "web", "snippet": "Wiki Summary"})

        return results
    except:
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    return jsonify(stealth_search(q))

if __name__ == '__main__':
    app.run(debug=True)
