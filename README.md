# Progetto di laboratorio — estrazione e valutazione del testo da pagine web

Servizio che scarica una pagina web, ne estrae il testo principale e lo confronta con un *gold standard* scritto a mano, calcolando **precision, recall e F1 a livello di token**. Un'interfaccia web permette di provare il parser su un URL e vedere la valutazione.

Domini supportati (`domain.json`): `en.wikipedia.org`, `www.usa.gov`, `www.latimes.com`.

## Come funziona

- **Parser** (`parser/parsing.py`): scarica la pagina con [crawl4ai](https://github.com/unclecode/crawl4ai), la converte in testo pulito con BeautifulSoup e mistune e valuta il risultato rispetto al gold standard.
- **Backend** (FastAPI, porta 8003): espone il parser e la valutazione.
- **Frontend** (Flask + Jinja, porta 8004): pagina per provare il sistema dal browser.

### Endpoint principali del backend

| Metodo | Percorso | Descrizione |
|---|---|---|
| GET / POST | `/parse` | estrae il testo da un URL o da un HTML |
| GET | `/supported-domains` | domini supportati |
| GET | `/gold-standard` | gold standard di una pagina |
| GET | `/full-gold-standard` | tutti i gold standard di un dominio |
| POST | `/evaluate` | valutazione di un testo estratto |
| GET | `/full-gs-evaluation` | valutazione su tutto il dominio |

## Avvio con Docker

La versione completa, con Dockerfile e `docker-compose`, è in `Progetto_Lab_info/`:

```bash
cd Progetto_Lab_info
docker compose up --build
```

Backend su http://localhost:8003 (documentazione interattiva su `/docs`), frontend su http://localhost:8004.

## Struttura

```
Progetto_Lab_info/   versione con Docker (backend, frontend, parser, gold standard)
gl_texts/            testi di riferimento
gs_data/             gold standard
```

## Autori

Danilo Cimmino e compagni di corso. Università Sapienza di Roma.
