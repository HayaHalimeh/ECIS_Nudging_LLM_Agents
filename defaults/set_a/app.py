from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import time
import json

app = FastAPI()

# Mount static directories so the browser can request them
script_dir = os.path.dirname(os.path.abspath(__file__))

image_candidates = [
    os.path.normpath(os.path.join(script_dir, '..', '..', 'src', 'images')),
    os.path.normpath(os.path.join(script_dir, '..', '..', 'images')),
    os.path.join(script_dir, 'images'),
]
for _dir in image_candidates:
    if os.path.isdir(_dir):
        app.mount('/images', StaticFiles(directory=_dir), name='images')
        break

css_candidates = [
    os.path.normpath(os.path.join(script_dir, '..', '..', 'src', 'css')),
    os.path.normpath(os.path.join(script_dir, '..', '..', 'css')),
    os.path.join(script_dir, 'css'),
]
for _dir in css_candidates:
    if os.path.isdir(_dir):
        app.mount('/css', StaticFiles(directory=_dir), name='css')
        break

js_candidates = [
    os.path.normpath(os.path.join(script_dir, '..', '..', 'src', 'js')),
    os.path.normpath(os.path.join(script_dir, '..', '..', 'js')),
    os.path.join(script_dir, 'js'),
]
for _dir in js_candidates:
    if os.path.isdir(_dir):
        app.mount('/js', StaticFiles(directory=_dir), name='js')
        break


@app.get("/review.html", response_class=HTMLResponse)
async def serve_review():
    """Serve the review page which reads selections from localStorage in the browser.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, "../review.html")

    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse("<h1>Review page not found</h1>", status_code=404)


@app.post('/api/save_selection')
async def save_selection(request: Request):
    """Receive a JSON payload with the selections and save a JSON snapshot
    into a `selections/` folder inside this app directory.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid JSON payload')

    # Save into the most recently created subfolder under `conversations/` if it exists,
    # otherwise fall back to `selections/`. If no subfolders exist, create a new run folder.
    parent_conversations = os.path.join(script_dir, 'conversations')
    parent_selections = os.path.join(script_dir, 'selections')

    if os.path.isdir(parent_conversations):
        parent = parent_conversations
    else:
        parent = parent_selections

    # ensure parent exists
    os.makedirs(parent, exist_ok=True)

    # find latest subdirectory inside parent
    try:
        entries = [e for e in os.scandir(parent) if e.is_dir()]
        if entries:
            latest = max(entries, key=lambda e: e.stat().st_mtime)
            out_dir = latest.path
            print(f"Saving selection to existing folder: {out_dir}")
        else:
            # create a new run folder
            out_dir = os.path.join(parent, 'run_' + time.strftime('%Y%m%d_%H%M%S'))
            os.makedirs(out_dir, exist_ok=True)
    except FileNotFoundError:
        out_dir = os.path.join(parent, 'run_' + time.strftime('%Y%m%d_%H%M%S'))
        os.makedirs(out_dir, exist_ok=True)

    ts = time.strftime('%Y%m%d_%H%M%S')
    base = f'selection_{ts}'
    json_path = os.path.join(out_dir, base + '.json')

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to write JSON: {e}')


    
@app.get("/end.html", response_class=HTMLResponse)
async def serve_end():
    """Serve the end page which shows the end message.
    """

    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, "../end.html")

    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse("<h1>End page not found</h1>", status_code=404)
    

@app.get("/", response_class=HTMLResponse)
async def serve_experiment():
    """Serve the HTML file directly"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, "index_a.html")
    
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse("<h1>Experiment not found</h1>", status_code=404)