import requests
from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def search_videos(query, level):
    """Deep search for YouTube educational videos without an API key."""
    results = []
    search_url = f"https://www.youtube.com/results?search_query={query}+{level}+tutorial"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    try:
        response = requests.get(search_url, headers=headers, timeout=5)
        # Using Regex to find video IDs in the raw HTML (Faster than BeautifulSoup for YT)
        video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
        
        for v_id in list(set(video_ids))[:10]:
            results.append({
                "title": f"Video Tutorial: {query}",
                "url": f"https://www.youtube.com/watch?v={v_id}",
                "type": "video",
                "level": level,
                "source": "YouTube"
            })
    except: pass
    return results

def search_files(query, level, f_type):
    """Deep search for Excel, Docs, and PDFs using a direct indexer."""
    results = []
    # If type is 'all', we search for everything. If specific, we target it.
    target = f_type if f_type != 'all' else "(pdf OR xlsx OR docx OR pptx)"
    search_query = f"{query} {level} filetype:{target}"
    
    # We use DuckDuckGo's Lite HTML for reliable, unblocked file discovery
    url = f"https://html.duckduckgo.com/html/?q={search_query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.find_all('a', class_='result__a', limit=15):
            href = link['href'].lower()
            # Intelligent type detection
            detected_type = 'web'
            if '.pdf' in href: detected_type = 'pdf'
            elif '.xls' in href or '.csv' in href: detected_type = 'excel'
            elif '.doc' in href: detected_type = 'document'
            elif '.ppt' in href: detected_type = 'ppt'

            results.append({
                "title": link.text,
                "url": link['href'],
                "type": detected_type,
                "level": level,
                "source": "Global Index"
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
        # We search for videos and files in parallel
        f1 = executor.submit(search_videos, query, level)
        f2 = executor.submit(search_files, query, level, f_type)
        
        combined = f1.result() + f2.result()
    
    # Final filter for the UI
    if f_type != 'all':
        combined = [r for r in combined if r['type'] == f_type]
        
    return jsonify(combined)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
