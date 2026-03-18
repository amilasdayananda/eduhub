import requests
from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def search_files(query, level, f_type):
    """Specifically hunts for direct file links (Excel, Word, PDF)."""
    results = []
    
    # Mapping for targeted 'Dorks'
    type_map = {
        'pdf': 'filetype:pdf',
        'excel': '(filetype:xlsx OR filetype:xls)',
        'document': '(filetype:docx OR filetype:doc)',
        'all': '(filetype:pdf OR filetype:xlsx OR filetype:docx)'
    }
    
    # We use DuckDuckGo HTML which is excellent for finding direct files
    target_ext = type_map.get(f_type, type_map['all'])
    search_query = f"{query} {level} {target_ext}"
    url = f"https://html.duckduckgo.com/html/?q={search_query}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=7)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for link in soup.find_all('a', class_='result__a', limit=20):
            href = link['href'].lower()
            
            # Strict File Type Detection
            detected = 'web'
            if '.pdf' in href: detected = 'pdf'
            elif any(x in href for x in ['.xls', '.xlsx', '.csv']): detected = 'excel'
            elif any(x in href for x in ['.doc', '.docx', '.rtf']): detected = 'document'
            
            # Only add if it's a file or we are in 'all' mode
            if f_type == 'all' or detected == f_type:
                results.append({
                    "title": link.text.strip(),
                    "url": link['href'],
                    "type": detected,
                    "level": level,
                    "source": "Global File Index"
                })
    except: pass
    return results

def search_videos(query, level):
    """Educational video search."""
    results = []
    url = f"https://www.youtube.com/results?search_query={query}+{level}+tutorial"
    try:
        resp = requests.get(url, timeout=5)
        v_ids = re.findall(r"watch\?v=(\S{11})", resp.text)
        for v_id in list(set(v_ids))[:8]:
            results.append({
                "title": f"Video: {query} ({level})",
                "url": f"https://www.youtube.com/watch?v={v_id}",
                "type": "video",
                "level": level,
                "source": "YouTube"
            })
    except: pass
    return results

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    level = request.args.get('level', 'Beginner')
    f_type = request.args.get('type', 'all')
    
    if not query: return jsonify([])

    with ThreadPoolExecutor() as executor:
        # If user asks for videos, we search videos. Otherwise, we focus on files.
        if f_type == 'video':
            data = search_videos(query, level)
        elif f_type == 'all':
            # In 'All' mode, we combine both
            f1 = executor.submit(search_files, query, level, 'all')
            f2 = executor.submit(search_videos, query, level)
            data = f1.result() + f2.result()
        else:
            # Targeted file search (Excel/Docs/PDF)
            data = search_files(query, level, f_type)
            
    return jsonify(data)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
