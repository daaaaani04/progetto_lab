from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
import requests
from pathlib import Path
import json
import os



app = FastAPI()
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
gold_path = Path(__file__).parent.parent.parent / 'gs_data' / 'gs_wiki.json'

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8003")

@app.get("/")
def index(request: Request):
    with open(gold_path, 'r', encoding='utf-8') as f:
        gold_data = json.load(f)
    urls = []
    for val in gold_data.values():
        for item in val.values():
            print(item["url"])
            urls.append(item["url"])
        

    
    return templates.TemplateResponse(
                            request=request,
                            name="index.html",
                            context={"urls": urls}
    )   

@app.get("/elabora")
async def elabora(url: str):
    try:
        print(f"Richiesta di parsing per URL: {url}")
        response = requests.get(f"{API_BASE}/parse", params={"url": url})
        response.raise_for_status()
        data = response.json()

        with open(gold_path, 'r', encoding='utf-8') as f:
            gold_data = json.load(f)
    
        gt = ""
        for val in gold_data.values():
            for item in val.values():
                if item["url"] == url:
                    gt = item["gold_text"]
                    break
        response = requests.post(f"{API_BASE}/evaluate", json={"gold": gt, "parsed": data["parsed_text"]})
        dati = response.json()
        dati=dati["token_leval_eval"]

        return {"data": data, "precision":dati["precision"], "recall":dati["recall"], "f1":dati["f1_score"]}
    
    except requests.exceptions.RequestException as e:
        print(f"ERRORE: {e}")
        raise HTTPException(status_code=502, detail=str(e))


    

    



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("frontend:app", host="0.0.0.0", port=8004, reload=True)

