import asyncio
import json
import re
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
import mistune

# Funzione per valutare precision, recall e F1-score a livello di token
def token_level_eval(text, gold_text, titolo):
    text = re.sub(r'\[\d+\]', '', text)

    html = mistune.html(text)
    soup = BeautifulSoup(html, "html.parser")
    # rimuove i tag lasciando il testo esattamente in-place (nessun separatore aggiunto, mantiene punteggiatura)
    for tag in soup.find_all(True):
        tag.unwrap()
    text = re.sub(r'[ \t]+', ' ', str(soup)) # collassa spazi orizzontali (non \n)
    text = re.sub(r'\n+', '\n', text) # collassa nuove linee multiple in una sola

    text = re.sub(r'\[\d+\]', '', text)
    
    #print(text)
    


    text = re.split(r'[\s]+', text.lower())
    set_token_parsati = set(text)
    #print(set_token_parsati)
    gold_text = re.split(r'[\s]+', gold_text.lower())
    set_token_gs = set(gold_text)
    #print(set_token_gs)
    res = set_token_gs.intersection(set_token_parsati)
    print(set_token_parsati-res)
    #print(set_token_gs - res)
    precision = len(res) / len(set_token_parsati) if set_token_parsati else 0
    recall = len(res) / len(set_token_gs) if set_token_gs else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0
    #print(f"titolo {titolo}, precision: {precision:.4f}, recall: {recall:.4f}, F1-score: {f1:.4f}")
    return precision, recall, f1



def parse_markdown_to_clean_wiki(text):
    # 1. Rimuovi link wikipedia residui tipo "Testo (disambigua)")
    text = re.sub(r'"[^"]*\([^)]*\)"\)', '', text)
    # 2. Rimuovi grassetto **testo** mantenendo il testo
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    # 3. Rimuovi corsivo _testo_ mantenendo il testo
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # 4. Rimuovi [citation needed] e varianti
    text = re.sub(r'\[citation needed\]', '', text)
    # 5. Rimuovi sezioni ## e ### finali
    sections_to_remove = [
        'See also', 'References', 'External links', 'Further reading',
        'Notes', 'Sources', 'Footnotes', 'Bibliography', 'Related articles',
        'Citations', 'Works cited', 'General references', 'Inline notes',
        'Explanatory notes', 'Navigation menu', 'Contents',
    ]
    for section in sections_to_remove:
        pattern = rf'##\s+{re.escape(section)}.*?(?=##|\Z)'
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    # 6. Rimuovi righe che sono solo ## titolo
    text = re.sub(r'^#{1,3}\s+.*$', '', text, flags=re.MULTILINE)
    # 7. Rimuovi backslash
    text = re.sub(r'\\', '', text)
    # 8. Rimuovi virgolette iniziali e finali del testo intero
    text = text.strip('"')
    # 9. Rimuovi link vuoti [](url)
    text = re.sub(r'\[\]\([^\)]*\)', '', text)
    # 10. Rimuovi link markdown [testo](url) → testo
    text = re.sub(r'\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    # 11. Rimuovi riferimenti numerici [1], [23]
    text = re.sub(r'\[\d+\]', '', text)
    # 12. Rimuovi tag HTML residui
    text = re.sub(r'<[^>]+>', '', text)
    # 13. Rimuovi righe che sono solo simboli
    text = re.sub(r'^\s*[\|\*\#]+\s*$', '', text, flags=re.MULTILINE)
    # 14. Elimina link con singolo carattere [[a]](url)
    text = re.sub(r'\[\[[a-zA-Z]\]\]\([^\)]*\)', '', text)
    # 15. Mantieni testo da link doppia parentesi [[testo]](url) → testo
    text = re.sub(r'\[\[([^\]]+)\]\]\([^\)]*\)', r'\1', text)
    # 16. Pulisci spazi eccessivi
    text = re.sub(r'\n\n\n+', '\n\n', text)
    text = text.strip()
    text = re.sub(r'\n', '', text)
    # elimina possibilita di parola.parola ma senza considerare i numeri decimali, ad esempio "3.14" non deve essere modificato, ma "parola.parola" deve diventare "parola. parola"
    text = re.sub(r'(?<!\d)\.(?!\d)', '. ', text)
    text = re.sub(r'\[\]\(https?://[^\)]*\)', '', text)
    # [(https://en.wikipedia.org/wiki/Wikipedia:Citationneeded "Wikipedia:Citation needed")]
    text = re.sub(r'\[\(https?://[^\)]*\)\]', '', text)
    # "Mars , Jupiter , Juno " → "Mars, Jupiter, Juno"
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r' ,', ',', text)
    text = re.sub(r' \.', '.', text)
    return text


# Configurazione del crawler per Wikipedia (gestisce come il browser viene lanciato e come si comporta)
browser_config_wiki = BrowserConfig(verbose=True, headless=True)
run_config_wiki = CrawlerRunConfig(
        #css_selector="#mw-content-text .mw-parser-output p, #mw-content-text .mw-parser-output h2, #mw-content-text .mw-parser-output h3",     #PROBLEMa: modifica html
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=0,
        excluded_tags=["nav", "footer", "header", "aside", "script", "style", "table", "figure", "figcaption"],
        excluded_selector="#Bibliography, .side-box, .mw-indicator, .mw-jump-link, .noprint, .hatnote, .infobox, .metadata, .navbox, .reflist, .references, .citation, .mw-editsection, .mw-references-wrap",
)
#funzione chiamata dagli endopoint che parsa il testo associatoal sito web identificato dall'url che prendi in input
async def run_single_crawl_wiki(url):
        async with AsyncWebCrawler(config=browser_config_wiki) as crawler:
            result = await crawler.arun(url, config=run_config_wiki)
            if result.success:
                cleaned_text = parse_markdown_to_clean_wiki(result.markdown)
                return {
                    "url": result.url,
                    "domain": "en.wikipedia.org",
                    "title": result.metadata.get('title', 'N/A'),
                    "html_text": result.html,
                    "parsed_text": result.markdown  # ritorno il markdown sporco che poi polisco nella token level eval
                }
            else:
                raise ConnectionError(f"Failed to crawl {url}: {result.error}")






def parse_markdown_to_clean_latimes(text):
    # Rimuovi tag HTML
    text = re.sub(r'<[^>]+>', '', text)
    # Rimuovi spazi eccessivi
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\[\[[a-zA-Z]\]\]\([^\)]*\)', '', text)
    return text

browser_config_latimes = BrowserConfig(verbose=True, headless=True)
run_config_latimes = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=0,
        excluded_tags=["ul","i","button","img","nav", "footer", "header", "aside", "script", "style", "figure", "figcaption"],
        excluded_selector=".published-date-day, .byline-suffix, .relative, .page-below, .page-above, .page-content-footer, .bylines, .enhancement, .noprint, .hatnote, .metadata, .navbox, .reflist, .references, .citation, .mw-editsection, .mw-references-wrap",
        wait_until="networkidle"
)

async def run_single_crawl_latimes(url):
        async with AsyncWebCrawler(config=browser_config_latimes) as crawler:
            result = await crawler.arun(url, config=run_config_latimes)
            if result.success:
                print("ciaooooo")
                cleaned_text = parse_markdown_to_clean_latimes(result.markdown)
                
                return {
                    "url": result.url,
                    "domain": "latimes.com",
                    "title": result.metadata.get('title', 'N/A'),
                    "html_text": result.html,
                    "parsed_text": result.markdown  # ritorno il markdown sporco che poi polisco nella token level eval
                }
            else:
                raise ConnectionError(f"Failed to crawl {url}: {result.error}")





def parse_markdown_to_clean_usagov(text):
    # Rimuovi tag HTML
    text = re.sub(r'<[^>]+>', '', text)
    # Rimuovi spazi eccessivi
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\[\[[a-zA-Z]\]\]\([^\)]*\)', '', text)
    return text

browser_config_usagov = BrowserConfig(verbose=True, headless=True)
run_config_usagov = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=0,
        excluded_tags=["button","img","nav", "footer", "header", "aside", "script", "style", "figure", "figcaption"],
        excluded_selector="#question-box, .additional_body_info",
        wait_until="networkidle"
)
# funzione di aprsin per usa gov
async def run_single_crawl_usagov(url):
        async with AsyncWebCrawler(config=browser_config_usagov) as crawler:
            result = await crawler.arun(url, config=run_config_usagov)
            if result.success:
                print("ciaooooo")
                cleaned_text = parse_markdown_to_clean_usagov(result.markdown)
                
                return {
                    "url": result.url,
                    "domain": "latimes.com",
                    "title": result.metadata.get('title', 'N/A'),
                    "html_text": result.html,
                    "parsed_text": result.markdown  # ritorno il markdown sporco che poi polisco nella token level eval
                }
            else:
                raise ConnectionError(f"Failed to crawl {url}: {result.error}")


async def parse_html(html, dominio, url):
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=browser_config) as crawler:
    # prefisso "raw:" per indicare che voglio parsare direttamente una stringa HTML
        result = await crawler.arun(
                url=f"raw:{html}", 
                config=run_config,
        )
    return {
        "url": url,
        "domain": dominio,
        "title": result.metadata.get('title', 'N/A'),
        "html_text": result.html,
        "parsed_text": result.markdown
    }