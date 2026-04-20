from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from typing import List
import json
from pathlib import Path
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from parser.parsing import run_single_crawl_wiki, run_single_crawl_latimes, run_single_crawl_usagov, parse_html
from parser.parsing import token_level_eval

gold_path = Path(__file__).parent.parent / 'gs_data' / 'gs_wiki.json'

app = FastAPI()

class Parsed(BaseModel):
    url: str
    domain: str
    title: str
    parsed_text: str

@app.get("/parse")
async def parse_url(url: str) -> Parsed:
    domain = url[8:].split("/")[0]
    print(domain)
    
    with open('domain.json', 'r', encoding='utf-8') as f:
        doms = json.load(f)

    if (domain not in doms["domains"]):
        raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")
    
    try:
        match domain:
            case "en.wikipedia.org":
                res = await run_single_crawl_wiki(url)
            case "www.latimes.com":
                res = await run_single_crawl_latimes(url)
            case "www.usa.gov":
                res = await run_single_crawl_usagov(url)
            case _:
                raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato cioa.")
        
        return Parsed(
            url=res["url"],
            domain=res["domain"],
            title=res["title"],
            parsed_text=res["parsed_text"]
        )
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # ← mostra l'errore reale



class HtmlParse(BaseModel):
    url: str
    html_text: str

@app.post("/parse")
async def parse_url_html(request: HtmlParse):
    url = request.url
    html_text = request.html_text
    domain = url[8:].split("/")[0]

    with open('domain.json', 'r', encoding='utf-8') as f:
        doms = json.load(f)

    if (domain not in doms["domains"]):
        raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")
    
    return await parse_html(html_text, domain, url)


class Domain(BaseModel):
    domain: List[str]

@app.get("/supported-domains")
async def get_supported_domains() -> Domain:
    with open('domain.json', 'r', encoding='utf-8') as f:
        doms = json.load(f)
    print(doms["domains"])
    return Domain(domain=doms["domains"])


class GoldStandard(BaseModel):
    url: str
    domain: str
    title: str
    html_text: str
    gold_text: str

@app.get("/gold-standard")
async def gold_standard(url: str) -> GoldStandard:
    domain = url[8:].split("/")[0]

    with open('domain.json', 'r', encoding='utf-8') as f:
        doms = json.load(f)

    if (domain not in doms["domains"]):
        raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")

    with open(gold_path, 'r', encoding='utf-8') as f:
        gs = json.load(f)
    
    gs=gs[domain]
   # print(gs)


    try:
        match domain:
            case "en.wikipedia.org":
                res = await run_single_crawl_wiki(url)
            case "www.latimes.com":
                res = await run_single_crawl_latimes(url)
            case "www.usa.gov":
                res = await run_single_crawl_usagov(url)
            case _:
                raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")
        return GoldStandard(
            url=res["url"],
            domain=res["domain"],
            title=res["title"],
            html_text=res["html_text"],
            gold_text=gs[res["title"]]["gold_text"]
        )
    
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # ← mostra l'errore reale




class Full_Gold_standard(BaseModel):
    gold_standard: List[GoldStandard]


@app.get("/full-gold-standard")
async def full_gold_standard(domain: str) -> Full_Gold_standard:

    with open('domain.json', 'r', encoding='utf-8') as f:
        doms = json.load(f)

    if (domain not in doms["domains"]):
        raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")

    with open(gold_path, 'r', encoding='utf-8') as f:
        gs = json.load(f)
    
    gs=gs[domain]
    res_list = []

    for elem in gs.values():
        url = elem["url"]

        match domain:
            case "en.wikipedia.org":
                res = await run_single_crawl_wiki(url)
            case "www.latimes.com":
                res = await run_single_crawl_latimes(url)
            case "www.usa.gov":
                res = await run_single_crawl_usagov(url)
            case _:
                raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")
        res_list.append(GoldStandard(
            url=res["url"],
            domain=res["domain"],
            title=res["title"],
            html_text=res["html_text"],
            gold_text=elem["gold_text"]
        ))
        
    return Full_Gold_standard(gold_standard=res_list)



class Input(BaseModel):
    gold: str
    parsed: str

@app.post("/evaluate")
async def evaluate(request: Input):
    gold = request.gold
    parsed = request.parsed
    precision, recall, f1_score = token_level_eval(parsed, gold, "")
    return {"token_leval_eval": { "precision": precision, "recall": recall, "f1_score": f1_score}}

class Full_Evaluation(BaseModel):
    avarage_precision: float
    avarage_recall: float
    avarage_f1_score: float

@app.get("/full-gs-evaluation")
async def full_gs_evaluation(domain: str) -> Full_Evaluation:
    with open('domain.json', 'r', encoding='utf-8') as f:
        doms = json.load(f)

    if (domain not in doms["domains"]):
        raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")

    with open(gold_path, 'r', encoding='utf-8') as f:
        gs = json.load(f)
    
    gs=gs[domain]
    
    precision_list = []
    recall_list = []
    f1_score_list = []

    for elem in gs.values():
        url = elem["url"]
        match domain:
            case "en.wikipedia.org":
                res = await run_single_crawl_wiki(url)
            case "www.latimes.com":
                res = await run_single_crawl_latimes(url)
            case "www.usa.gov":
                res = await run_single_crawl_usagov(url)
            case _:
                raise HTTPException(status_code=400, detail=f"Dominio '{domain}' non supportato.")
        precision, recall, f1_score = token_level_eval(res["parsed_text"], elem["gold_text"], "")
        precision_list.append(precision)
        recall_list.append(recall)
        f1_score_list.append(f1_score)

    avarage_precision = sum(precision_list) / len(precision_list) if precision_list else 0.0
    avarage_recall = sum(recall_list) / len(recall_list) if recall_list else 0.0
    avarage_f1_score = sum(f1_score_list) / len(f1_score_list) if f1_score_list else 0.0

    return Full_Evaluation(
        avarage_precision=avarage_precision,
        avarage_recall=avarage_recall,
        avarage_f1_score=avarage_f1_score
    )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)