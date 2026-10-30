"""SA Embroidery conversational catalog assistant. Start: uvicorn main:app --reload --port 8000"""

import html

import json

import logging

import os

import re

import threading

import time

import urllib.error

import urllib.request

from difflib import SequenceMatcher

from pathlib import Path

from urllib.parse import quote

from groq import Groq, GroqError

from fastapi import FastAPI, HTTPException, Request, Response, status

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse

from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field



from .prompts import (
    SYSTEM_PROMPT,
    OFF_TOPIC_REFUSAL_EN,
    OFF_TOPIC_REFUSAL_UR,
    is_off_topic_query,
)

from dotenv import load_dotenv



load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)



PRODUCTS_API = os.getenv('PRODUCTS_API', 'https://sa-embroidery-backend.onrender.com/api/read/Products')

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b').strip() or 'openai/gpt-oss-20b'

if GROQ_MODEL in ('llama-3.1-8b-instant', 'llama-3.3-70b-versatile'):

    logging.warning('Deprecated/unavailable GROQ_MODEL=%s; using openai/gpt-oss-20b instead', GROQ_MODEL)

    GROQ_MODEL = 'openai/gpt-oss-20b'

REFRESH_SECONDS = max(60, int(os.getenv('REFRESH_SECONDS', '600')))

RATE_LIMIT_PER_MINUTE = max(1, int(os.getenv('RATE_LIMIT_PER_MINUTE', '20')))

RATE_LIMIT_BURST = max(1, int(os.getenv('RATE_LIMIT_BURST', '5')))


class InMemoryRateLimiter:
    """Thread-safe sliding window and burst rate limiter."""
    def __init__(self, requests_per_minute: int = 20, burst_limit: int = 5, burst_window: int = 10):
        self.rpm = requests_per_minute
        self.burst_limit = burst_limit
        self.burst_window = burst_window
        self.lock = threading.Lock()
        self.history: dict[str, list[float]] = {}
        self._last_cleanup = time.time()

    def _cleanup(self, now: float):
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        stale = [k for k, ts in self.history.items() if not ts or (now - ts[-1] > 120)]
        for k in stale:
            self.history.pop(k, None)

    def check(self, key: str) -> tuple[bool, int]:
        now = time.time()
        with self.lock:
            self._cleanup(now)
            timestamps = self.history.setdefault(key, [])
            recent_minute = [t for t in timestamps if now - t <= 60]
            self.history[key] = recent_minute

            recent_burst = [t for t in recent_minute if now - t <= self.burst_window]
            if len(recent_burst) >= self.burst_limit:
                retry_after = max(1, int(self.burst_window - (now - recent_burst[0])))
                return False, retry_after

            if len(recent_minute) >= self.rpm:
                retry_after = max(1, int(60 - (now - recent_minute[0])))
                return False, retry_after

            recent_minute.append(now)
            return True, 0


rate_limiter = InMemoryRateLimiter(
    requests_per_minute=RATE_LIMIT_PER_MINUTE,
    burst_limit=RATE_LIMIT_BURST,
    burst_window=10
)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


SITE = 'https://saembroidery.com'

WA_NUMBER = '923167937030'

ROOT = Path(__file__).resolve().parent.parent

BUNDLED_CACHE_FILE = ROOT / 'data' / 'knowledge_base.json'
CACHE_DIR = Path('/tmp') if os.getenv('VERCEL') else (ROOT / 'data')
CACHE_FILE = CACHE_DIR / 'knowledge_base.json'

FEATURED_FILE = ROOT / 'data' / 'featured_products.json'

FRONTEND = ROOT / 'frontend'

logging.basicConfig(level=logging.INFO)

log = logging.getLogger('sa-chatbot')



app = FastAPI(title='SA Embroidery Professional AI Assistant', version='4.0.0')

origins = [x.strip() for x in os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,https://saembroidery.com,https://www.saembroidery.com').split(',') if x.strip()]

app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET','POST'], allow_headers=['Content-Type'])

if FRONTEND.exists():

    app.mount('/frontend', StaticFiles(directory=str(FRONTEND), html=True), name='frontend')



@app.get('/')

def index():

    return FileResponse(FRONTEND / 'Sa-Chat-PRO.html')



@app.get('/widget.js')

def widget():

    return FileResponse(FRONTEND / 'widget.js', media_type='application/javascript')



LOCK = threading.RLock()

PRODUCTS = []

LAST_SYNC = None

STOP_WORDS = set('i me my you your our of for to a an the is are do does it in on with please need want show tell give can could how what where have about and or ka ki ke ko hai hain mujhe mujy mujay bhai ji ap aap chahiye chaiye kya kitna kitni rate price qeemat cost'.split())

SYNONYMS = {'sui':'needle','suyan':'needle','firki':'bobbin','ribbon':'cable','shuttle':'hook','daam':'price','qeemat':'price','tensioner':'tension','dhaga':'thread'}



def parse_json(value, default):

    if isinstance(value, (list,dict)): return value

    if isinstance(value,str):

        try: return json.loads(value)

        except (ValueError, TypeError): pass

    return default



def strip_html(value):

    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', str(value or '')))).strip()



def website_price(record):

    """Prefer published USD schema offer over inconsistent legacy API number.

    The website itself cannot be verified here; confirm schema mirrors website.

    """

    def positive(v):

        try:

            value=float(v)

            return value if 0 < value < 1_000_000_000 else None

        except (TypeError,ValueError): return None

    schema=parse_json(record.get('schema_markup'), {})

    offer=None

    if isinstance(schema,dict):

        candidates=[schema]

        graph=schema.get('@graph')

        if isinstance(graph,list):candidates+= [node for node in graph if isinstance(node,dict)]

        for node in candidates:

            offers=node.get('offers')

            for o in (offers if isinstance(offers,list) else [offers]):

                if isinstance(o,dict) and str(o.get('priceCurrency','')).upper()=='USD':

                    offer=positive(o.get('price')) or (positive(o.get('lowPrice')) if o.get('highPrice') is None else None)

                    if offer:break

            if offer:break

    raw=positive(record.get('price'))

    sale=positive(record.get('sale_price'))

    discounted=raw is not None and sale is not None and sale<raw and str(record.get('sale')).lower() in ('true','1')

    listed=(sale if discounted else raw)

    amount=offer if offer is not None else listed

    source='schema_usd_offer' if offer is not None else 'api_usd_price'

    conflict=offer is not None and listed is not None and abs(offer-listed)>0.005

    return amount,source,conflict



def normalize(record):

    if not isinstance(record,dict) or record.get('active') is False or record.get('archive') is True: return None

    name = strip_html(record.get('product_name'))

    if not name: return None

    imgs=[]

    for im in parse_json(record.get('product_images'), []):

        url = (im.get('edited_url') or im.get('url')) if isinstance(im,dict) else (im if isinstance(im,str) else '')

        if isinstance(url,str) and url.startswith('https://') and url not in imgs: imgs.append(url)

    schema=parse_json(record.get('schema_markup'), {})

    sku=(record.get('sku') or (schema.get('sku') if isinstance(schema,dict) else None))

    def number(v):

        try: return float(v)

        except (ValueError, TypeError): return None

    stock = number(record.get('available_stock'))

    final_price,price_source,price_conflict=website_price(record)

    currency='USD'

    price_text=f'${final_price:,.2f}' if final_price is not None else None

    slug=record.get('url_slug') or ''

    url=SITE+'/'+quote(str(slug).strip('/'),safe='-/') if slug else None

    faqs=parse_json(record.get('faqs'), [])

    return {'id':record.get('id'),'sku':str(sku) if sku else None,'name':name,'category':strip_html(record.get('category_name') or record.get('category1')) or None,

            'price':price_text,'price_amount':final_price if final_price is not None and final_price>0 else None,'price_currency':currency,'price_source':price_source,'price_conflict':price_conflict,'stock':int(stock) if stock is not None and stock>0 else None,

            'stock_status':'Listed quantity' if stock is not None and stock>0 else 'Confirm current availability',

            'image_url':imgs[0] if imgs else None,'images':imgs,'url':url,

            'description':strip_html(record.get('description'))[:1300], 'short_description':strip_html(record.get('short_description'))[:500],

            'specifications':parse_json(record.get('specifications'), {}), 'features':parse_json(record.get('features'), []),

            'faqs':faqs[:5] if isinstance(faqs,list) else [],'keywords':strip_html(record.get('meta_keywords'))[:400]}



def refresh():

    global LAST_SYNC

    req=urllib.request.Request(PRODUCTS_API, headers={'Accept':'application/json','User-Agent':'SAEmbroideryChat/4.0'})

    key=os.getenv('PRODUCTS_API_KEY')

    if key: req.add_header('Authorization',f'Bearer {key}')

    with urllib.request.urlopen(req,timeout=25) as response: payload=json.loads(response.read().decode('utf8'))

    rows=payload if isinstance(payload,list) else payload.get('data',[])

    if isinstance(rows,dict): rows=rows.get('products', rows.get('rows', []))

    if not isinstance(rows,list): raise ValueError('Unsupported product API response')

    normalized=[p for r in rows if (p:=normalize(r))]

    if not normalized: raise ValueError('Product API returned no active products')

    with LOCK:

        PRODUCTS[:]=normalized

        LAST_SYNC=time.time()

        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(json.dumps(normalized, ensure_ascii=False), encoding='utf8')
        except OSError as exc:
            log.warning('Could not write cache to disk: %s', exc)

    log.info('Catalog refreshed: %s products', len(normalized))



def load_initial_cache():
    for f in (CACHE_FILE, BUNDLED_CACHE_FILE):
        if f.exists():
            try:
                cache = json.loads(f.read_text(encoding='utf8'))
                if isinstance(cache, list) and cache:
                    with LOCK:
                        PRODUCTS[:] = cache
                    log.info('Catalog loaded from cache: %s products from %s', len(PRODUCTS), f)
                    return
            except Exception as exc:
                log.warning('Invalid cache at %s: %s', f, exc)

load_initial_cache()



def refresh_loop():

    while True:

        try: refresh()

        except Exception as exc: log.warning('Catalog refresh failed: %s', exc)

        time.sleep(REFRESH_SECONDS)



@app.on_event('startup')

def startup():

    if not PRODUCTS:
        load_initial_cache()

    threading.Thread(target=refresh_loop, daemon=True).start()



def load_featured_ids() -> list[int]:
    """Load manually curated top-selling product IDs from config file."""
    try:
        if FEATURED_FILE.exists():
            data = json.loads(FEATURED_FILE.read_text(encoding='utf8'))
            return [int(i) for i in data.get('top_selling', [])]
    except Exception as exc:
        log.warning('Could not load featured_products.json: %s', exc)
    return []


def get_top_products(limit: int = 6) -> list[dict]:
    """Return featured/top-selling products in the configured order."""
    featured_ids = load_featured_ids()
    if not featured_ids:
        return []
    with LOCK:
        by_id = {p['id']: p for p in PRODUCTS if p.get('id') is not None}
    result = []
    for fid in featured_ids:
        p = by_id.get(fid)
        if p:
            result.append(p)
        if len(result) >= limit:
            break
    return result


# Patterns that indicate a "top/best/popular products" query
TOP_PRODUCTS_PATTERNS = [
    r'\b(?:top|best|most popular|bestseller|best seller|bestselling|best selling|featured|popular|trending|most sold|highly rated|sabse zyada bikne wale|sabse popular|mashhoor|top selling|top products|top list)\b',
]


def is_top_products_query(message: str) -> bool:
    """Return True if the user is asking for top/best/popular products."""
    text = (message or '').strip().lower()
    for pat in TOP_PRODUCTS_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def tokens(s):

    words=re.findall(r'[a-z0-9]+',str(s).lower())

    return [SYNONYMS.get(w,w) for w in words if w not in STOP_WORDS and len(w)>1]



def search_products(query,limit=4):

    query=query.lower().strip()

    ts=tokens(query)

    if not ts: return []

    ranked=[]

    with LOCK: rows=list(PRODUCTS)

    for p in rows:

        name=p['name'].lower(); cat=(p['category'] or '').lower()

        desc=(p['short_description'] or '').lower(); sku=(p['sku'] or '').lower(); pid=str(p['id'] or '')

        score=0

        if re.fullmatch(r'(sku\s*[:#]?\s*)?\d{2,8}',query) and (query.split()[-1]==sku or query.split()[-1]==pid): score+=35

        if len(query)>3 and query in name: score+=15

        name_tokens=set(tokens(name))

        for t in ts:

            if t in name_tokens: score+=6

            elif len(t)>3 and t in name: score+=4

            elif t in tokens(cat): score+=1.2

            elif len(t)>4 and t in desc: score+=0.3

            elif len(t)>3 and any(SequenceMatcher(None,t,w).ratio()>=.88 for w in name_tokens): score+=2

        if score>=4: ranked.append((score,p))

    ranked.sort(key=lambda x:x[0],reverse=True)

    if not ranked: return []

    # Prevent weak, generic matches from being presented as exact products.

    return [p for score,p in ranked[:limit] if score>=max(5,ranked[0][0]*0.45)]



# A synonym layer is useful for initial retrieval; Groq judges candidates, never invents listings.

RELATED_TERMS = {

    'firki':['bobbin','bobbin case'], 'dhaga':['thread','polyester thread'],

    'sui':['needle','organ needle'], 'kanta':['needle'],

    'shuttle':['rotary hook','hook'], 'hook':['rotary hook','shuttle'],

    'tensioner':['tension post','tension assembly'],

    'color change':['colour change','color plate'],

    'packing':['gasket','rubber','packing'],

    'head packing':['head rubber','crystal packing'],

    'belt':['drive belt','timing belt'], 'motor':['servo motor'],

    'wire':['ribbon cable','cable'], 'cable':['ribbon cable'],

}



# Initialize lazily so missing configuration reports a useful error instead of crashing startup.
groq_client = None


def groq_call(messages, max_tokens=500, temperature=0.2):
    global groq_client
    if not GROQ_API_KEY:
        log.error("Groq key missing. Check the project-root .env file.")
        return None

    try:
        if groq_client is None:
            groq_client = Groq(api_key=GROQ_API_KEY, timeout=45.0, max_retries=1)
        # Reasoning models can spend completion tokens on internal reasoning.
        # A small limit (100/140) can therefore produce empty visible content.
        budget = max(1600, int(max_tokens))
        kwargs = dict(
            model=GROQ_MODEL,
            messages=messages,
            max_completion_tokens=budget,
            temperature=temperature,
        )
        # Use SDK defaults; some accounts reject reasoning_effort overrides.
        response = groq_client.chat.completions.create(**kwargs)
        if not response.choices:
            log.error("Groq returned no choices")
            return None
        choice = response.choices[0]
        content = choice.message.content
        if isinstance(content, str) and content.strip():
            return content.strip()
        log.warning("Groq empty visible output (finish_reason=%s, usage=%s)",
                    choice.finish_reason, response.usage)
        return None
    except GroqError as exc:
        status = getattr(exc, 'status_code', None)
        # Avoid logging API credentials or request headers.
        log.error("Groq SDK failure: status=%s, model=%s, type=%s, message=%s",
                  status, GROQ_MODEL, type(exc).__name__, str(exc)[:700])
        return None
    except Exception:
        log.exception("Unexpected Groq failure")
        return None


def related_search(message):

    # Expand colloquial terms while keeping the actual product selection server-side.

    query=message.lower()

    expanded=[message]

    for term, synonyms in RELATED_TERMS.items():

        if re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',query):

            expanded += synonyms[:2]

    seen={};

    for text in expanded:

        for idx,p in enumerate(search_products(text,limit=12)):

            seen[str(p['id'])]=p

    # Groq may generate search words for indirect descriptions.

    result=groq_call([

        {'role':'system','content':'Extract up to 4 short English industrial embroidery/sewing spare-part search phrases from the user message. Include synonyms where useful. Output ONLY JSON: {"terms":["..."]}. Never answer user, invent inventory, or include generic words like product/price.'},

        {'role':'user','content':message[:500]}

    ],max_tokens=140)

    if result:

        try:

            parsed=json.loads(re.search(r'\{.*\}',result,re.S).group())

            for term in parsed.get('terms',[])[:4]:

                if not isinstance(term,str) or len(term)>80: continue

                for p in search_products(term,limit=12): seen[str(p['id'])]=p

        except (ValueError,AttributeError,TypeError): pass

    candidates=list(seen.values())[:22]

    if not candidates: return []

    # Catalog is source of truth. Groq chooses only IDs from server-side shortlist.

    choices=[{'id':str(p['id']),'name':p['name'],'sku':p.get('sku'),

       'category':p.get('category'),'description':p.get('short_description','')[:230]} for p in candidates]

    verdict=groq_call([

        {'role':'system','content':'You match customer descriptions to real catalog products. Return ONLY JSON {"ids":["id"]}. Pick up to 3 IDs from the supplied candidates only when the product is clearly the requested type/function. Reject vague accidental token similarities. Related names are allowed, but never claim machine compatibility from a generic match. If not confident, return {"ids":[]}. No other text.'},

        {'role':'user','content':json.dumps({'request':message,'candidates':choices},ensure_ascii=False)}

    ],max_tokens=140)

    if verdict:

        try:

            ids=json.loads(re.search(r'\{.*\}',verdict,re.S).group()).get('ids',[])

            by_id={str(p['id']):p for p in candidates}

            return [by_id[str(i)] for i in ids[:3] if str(i) in by_id]

        except (ValueError,AttributeError,TypeError): pass

    # If the AI is offline, only use high-confidence direct name matches.

    return [p for p in search_products(message,limit=3) if p['name'].lower() in query or (p.get('sku') and re.search(r'(?<!\w)'+re.escape(p['sku'].lower())+r'(?!\w)',query))]



class Message(BaseModel):

    role:str

    content:str



class ChatIn(BaseModel):

    message:str=Field(min_length=1,max_length=1500)

    history:list[Message]=Field(default_factory=list)

    language:str='auto'

    session_id:str|None=None

    products:list[dict]=Field(default_factory=list)  # ignored: never trust frontend products as authoritative



def lang_of(message, history, hint):

    if hint in ('en','ur'): return hint

    words=set(re.findall(r'[a-z]+',message.lower()))

    ur=set('kya kitna kitni hain hai mujhe mujy mujay chahiye chaiye ap aap batao btao bhai krna karna ho ga milay ga kahan kese kaisy kaisay kaise kesi kaisa kai hal haal ki ke ko hy han ji salam alaikum walaikum khairiyat shukriya theek thik hoon'.split())

    if words & ur: return 'ur'

    if len(words)<=2 and history:

        prior=[h.content for h in history[-6:] if h.role=='user']

        for x in reversed(prior):

            if set(re.findall(r'[a-z]+',x.lower())) & ur: return 'ur'

    return 'en'



# Handle social conversation before catalog retrieval. No generic product fallback for greetings.

HONORIFICS = r'(?:\s+(?:bhai|brother|bro|janab|sir|yaar|dear|friend|ji|sahab))?'

SMALL_TALK = [
 (r'(?:h+i+|h+y+|hey+|hello+|sala+m|salam alaikum|assalam(?:\s*[ou]\s*)?ala+i+kum|aoa|good morning|good afternoon|good evening)' + HONORIFICS, 'greeting'),
 (r'(?:how are (?:you|u)|how r (?:you|u)|how(?:[\x27\s]s| is) it going|how you doing|how are things|k(?:ai|ay|e|i)s(?:e|ay|a|y) (?:ho|hain)|(?:kya|kia|kai|kay) (?:hal|haal) (?:hai|hain)|(?:ap|aap) (?:ka|ke) (?:kya )?(?:hal|haal)|sab (?:theek|thik|khairiyat)|kheriyat)' + HONORIFICS, 'wellbeing'),
 (r'(?:i am|i\'m) (?:fine|good|great|okay)|(?:main|mai) (?:theek|thik|fine) (?:hun|hoon)|(?:theek|thik) (?:hun|hoon)|alhamdulillah', 'wellbeing_reply'),
 (r'(?:thanks|thank you|thankyou|shukriya|bohat shukriya|jazakallah)' + HONORIFICS, 'thanks'),
 (r'(?:bye|goodbye|see you|allah hafiz|khuda hafiz)' + HONORIFICS, 'farewell'),
 (r'(?:who are you|what is your name|tum kon ho|aap kon hain|ap kon ho)', 'identity'),
]



def small_talk_intent(message):

    clean = re.sub(r"[^a-z0-9\s\']", ' ', message.lower()).strip()

    clean = re.sub(r'\s+', ' ', clean)

    # Only pure social messages; a message containing a part number should never be intercepted.

    for pattern, intent in SMALL_TALK:

        if re.fullmatch(pattern, clean):

            return intent

    return None



def small_talk_fallback(intent, language, history):

    ur = language == 'ur'

    recent = ' '.join(h.content.lower() for h in history[-8:] if h.role == 'assistant')

    offered = any(x in recent for x in ('machine part', 'embroidery parts', 'spare part', 'threads', 'product', 'parts ya', 'part ya'))

    replies = {

      'greeting': ('Assalam-o-Alaikum! SA Embroidery mein khush aamdeed. Aap ki kis tarah madad kar sakta hoon?' if ur else 'Hello! Welcome to SA Embroidery. How may I assist you today?'),

      'wellbeing': ('Alhamdulillah, main theek hoon. Poochne ka shukriya! Aap sunayein, kaisay hain?' if ur else "I'm doing well, thank you for asking! How are you today?"),

      'wellbeing_reply': ('Bohat achha! Sun kar khushi hui.' if ur else "That's lovely to hear!"),

      'thanks': ('Aap ka shukriya! Khushi se madad karunga.' if ur else "You're very welcome! Happy to help."),

      'farewell': ('Allah Hafiz! Aap ka din achha guzray.' if ur else 'Thank you for visiting SA Embroidery. Have a wonderful day!'),

      'identity': ('Main SA Embroidery ka AI assistant hoon. Main products aur orders mein aap ki rehnumai karta hoon.' if ur else "I'm SA Embroidery's AI assistant. I can help you explore products and make enquiries."),

    }

    answer = replies.get(intent, '')

    if intent in ('thanks', 'farewell', 'wellbeing_reply') or offered:

        return answer

    if intent == 'wellbeing':

        return answer + (' Agar aap kisi sewing ya embroidery part ki talash mein hain to main guide kar sakta hoon.' if ur else ' If you are looking for any sewing or embroidery supplies, I would be glad to help.')

    return answer



def classify_intent(message, history):

    """Use AI to decide whether a catalog lookup is actually needed.



    Do not interpret every unknown message as an inventory inquiry.

    """

    recent = [{'role': h.role, 'content': h.content[:350]}

              for h in history[-6:] if h.role in ('user', 'assistant')]

    raw = groq_call([

        {'role': 'system', 'content': (

            'Classify the LATEST customer message for a general-purpose sales assistant. '

            'Output ONLY JSON: {"intent":"product|business|general"}. '

            'product = customer seeks a specific part, thread, accessory, product options, '

            'product identification, price, compatibility, or follows up about a previously discussed product. '

            'business = shipping, orders, contact/WhatsApp, store, wholesale policies, support. '

            'general = greetings, wellbeing, jokes, ordinary questions, general knowledge, insults, '

            'personal talk, unrelated topics. A single word such as "WhatsApp?" is business. '

            'Never interpret random terms as inventory requests unless the customer is discussing products. '

            'Use context for short follow-ups.'

        )},

        {'role': 'user', 'content': json.dumps({'history':recent, 'message':message}, ensure_ascii=False)}

    ], max_tokens=100, temperature=0)

    if raw:

        try:

            result=json.loads(re.search(r'\{.*?\}',raw,re.S).group())

            if result.get('intent') in ('product','business','general'):

                return result['intent']

        except (ValueError,AttributeError,TypeError): pass

    # If classification fails, don't assume an unknown sentence is a product request.

    product_words = r'\b(bobbin|needle|hook|shuttle|thread|tension|belt|motor|juki|tajima|barudan|part|parts|sku|spare|packing|machine|firki|sui|dhaga|price of|rate of)\b'

    business_words = r'\b(whatsapp|shipping|delivery|courier|fedex|dhl|contact|address|office|wholesale|quotation|quote)\b'

    if re.search(product_words,message,re.I): return 'product'

    if re.search(business_words,message,re.I): return 'business'

    return 'general'





def ai_response(message, history, language, products, intent):
    if not GROQ_API_KEY: return None

    with LOCK:
        catalog_count = len(PRODUCTS)

    context = {'catalog_loaded': bool(catalog_count), 'verified_catalog_matches': products}
    hist = [{'role': h.role, 'content': h.content[:1500]} for h in history[-12:] if h.role in ('assistant', 'user')]

    turn_guideline = ''
    if intent in ('greeting', 'wellbeing', 'wellbeing_reply', 'thanks', 'farewell', 'identity'):
        turn_guideline = (
            '- GREETING / WELLBEING: Respond warmly and politely like a real human sales consultant. '
            'Acknowledge how they are doing (e.g. "I am doing great, thank you for asking! How are you doing today?"), '
            'welcome them to SA Embroidery, and ask how you can help them with embroidery machine spare parts, needles, bobbins, threads, or store inquiries.\n'
        )
    elif intent == 'business':
        turn_guideline = '- BUSINESS: Respond helpfully and directly to shipping, wholesale, payment, or WhatsApp inquiries (https://wa.me/923167937030).\n'
    elif intent == 'product':
        turn_guideline = '- PRODUCT: Only assert facts for VERIFIED catalog matches. When no matches exist, clearly state that no verified listing was found and direct to https://saembroidery.com/products or request machine model/part details.\n'

    instructions = (
        SYSTEM_PROMPT + '\n\n' +
        'CURRENT INTENT: ' + intent + '\n' +
        'GUIDELINES FOR THIS TURN:\n' +
        turn_guideline +
        '- Tone: Warm, human, professional, polite, and helpful.\n' +
        '- Under NO circumstances should you answer questions unrelated to SA Embroidery (for example: "what is python", coding, math, general science, politics, recipes). If asked about unrelated topics, politely decline in a natural human way and ask what embroidery or sewing parts they need.\n' +
        '- Never invent stock, price, compatibility or SKU.\n' +
        'Reply in ' + ('natural, friendly Roman Urdu' if language == 'ur' else 'natural, polite English') + '.\n' +
        'VERIFIED DATA: ' + json.dumps(context, ensure_ascii=False)[:12000]
    )

    return groq_call([{'role': 'system', 'content': instructions}] + hist +
                     [{'role': 'user', 'content': message}], max_tokens=650, temperature=0.35)


@app.post('/chat')
@app.post('/api/chat')
def chat(body: ChatIn, request: Request):
    client_ip = get_client_ip(request)
    rate_key = client_ip
    allowed, retry_after = rate_limiter.check(rate_key)
    if not allowed:
        log.warning("Rate limit exceeded for %s", rate_key)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please wait {retry_after} seconds before sending another message.",
            headers={"Retry-After": str(retry_after)}
        )

    message = body.message.strip()
    language = lang_of(message, body.history, body.language)
    low = message.lower().strip()

    # 1. Warm Social Greetings & Small Talk (CHECK FIRST so greetings are NEVER blocked!)
    st_intent = small_talk_intent(message)
    if st_intent:
        ai_reply = ai_response(message, body.history, language, [], st_intent)
        reply_text = ai_reply if ai_reply else small_talk_fallback(st_intent, language, body.history)
        return {
            'answer': reply_text,
            'reply': reply_text,
            'language': language,
            'intent': st_intent,
            'type': 'answer',
            'products': [],
            'whatsapp_url': f'https://wa.me/{WA_NUMBER}?text={quote("Hello SA Embroidery, I need help")}',
            'ai_enabled': bool(GROQ_API_KEY),
            'catalog_url': None
        }

    # 2. TOP SELLING / POPULAR PRODUCTS query
    if is_top_products_query(message):
        top = get_top_products(limit=6)
        if top:
            names = ', '.join(p['name'] for p in top)
            if language == 'ur':
                answer_text = (
                    f'Hamare sabse zyada bikne wale products yeh hain: {names}. '
                    'Agar aap kisi bhi product ki qeemat ya availability ke baare mein puchna chahein, '
                    'to main hazir hoon.'
                )
            else:
                answer_text = (
                    f'Here are our top-selling products: {names}. '
                    'Feel free to ask about pricing, availability, or compatibility for any of them.'
                )
            top_out = [{k: p.get(k) for k in ('id', 'sku', 'name', 'category', 'price', 'price_amount',
                'price_currency', 'price_source', 'price_conflict', 'stock', 'stock_status',
                'image_url', 'images', 'url', 'short_description')} for p in top]
            return {
                'answer': answer_text,
                'reply': answer_text,
                'language': language,
                'intent': 'top_products',
                'type': 'product',
                'products': top_out,
                'whatsapp_url': f'https://wa.me/{WA_NUMBER}?text={quote("Hello SA Embroidery, I want to order top selling products")}',
                'ai_enabled': bool(GROQ_API_KEY),
                'catalog_url': SITE + '/products'
            }
        else:
            # Featured list not configured — fall through to normal product search
            log.info('Top-products query but no featured list configured.')

    # 3. IMMEDIATE GUARDRAILS: Check if query is explicitly off-topic (e.g. what is python, recipes, coding)
    if is_off_topic_query(message, body.history):
        refusal = OFF_TOPIC_REFUSAL_UR if language == 'ur' else OFF_TOPIC_REFUSAL_EN
        return {
            'answer': refusal,
            'reply': refusal,
            'language': language,
            'intent': 'off_topic',
            'type': 'refusal',
            'products': [],
            'whatsapp_url': f'https://wa.me/{WA_NUMBER}?text={quote("Hello SA Embroidery, I have an inquiry")}',
            'ai_enabled': bool(GROQ_API_KEY),
            'catalog_url': SITE + '/products'
        }


    # 3. Classify business vs product vs general
    if re.search(r'\b(whatsapp|contacts?|shippings?|deliver(?:y|ies)?|couriers?|fedex|dhl|address(?:es)?|offices?|wholesale|quotations?|quotes?)\b', low):
        intent = 'business'
    elif re.search(r'\b(bobbins?|needles?|hooks?|shuttles?|threads?|tensions?|belts?|motors?|juki|tajima|barudan|parts?|skus?|spares?|packings?|machines?|firkis?|suis?|dhagas?|loopers?|scissors?|cutters?|frames?|hoops?|presser\s*feet|presser\s*foot)\b', low):
        intent = 'product'
    elif re.search(r'\b(it|this|that|iska|iski|how much|qeemat|price|rate)\b', low) and any(
        h.role == 'assistant' and any(p['name'].lower() in h.content.lower() for p in PRODUCTS)
        for h in body.history[-6:]
    ):
        intent = 'product'
    else:
        intent = 'product' if search_products(message, limit=1) else 'general'

    # 3b. If intent classified as 'general', use AI to confirm it is NOT off-topic.
    #     'general' here means it did not match any known product/business pattern.
    #     If classify_intent also says 'general', the message is unrelated to SA Embroidery.
    if intent == 'general':
        ai_intent = classify_intent(message, body.history)
        if ai_intent == 'product':
            intent = 'product'
        elif ai_intent == 'business':
            intent = 'business'
        else:
            # Confirmed off-topic: politely refuse without calling the main LLM.
            refusal = OFF_TOPIC_REFUSAL_UR if language == 'ur' else OFF_TOPIC_REFUSAL_EN
            return {
                'answer': refusal,
                'reply': refusal,
                'language': language,
                'intent': 'off_topic',
                'type': 'refusal',
                'products': [],
                'whatsapp_url': f'https://wa.me/{WA_NUMBER}?text={quote("Hello SA Embroidery, I have an inquiry")}',
                'ai_enabled': bool(GROQ_API_KEY),
                'catalog_url': SITE + '/products'
            }

    matched = []
    if intent == 'product':
        matched = related_search(message)
        # Short follow-up: retain the previously discussed item when unambiguous.
        if not matched and re.search(r'\b(it|this|that|iska|iski|is ka|how much|price|rate|qeemat)\b', message, re.I):
            previous = [h.content for h in body.history[-8:] if h.role == 'assistant']
            with LOCK:
                rows = list(PRODUCTS)
            for prior in reversed(previous):
                found = next((p for p in rows if p['name'].lower() in prior.lower()), None)
                if found:
                    matched = [found]
                    break

    answer = ai_response(message, body.history, language, matched, intent)

    if not answer:
        log.error('No AI reply produced: intent=%s, groq_model=%s, key_configured=%s',
                  intent, GROQ_MODEL, bool(GROQ_API_KEY))
        raise HTTPException(status_code=503, detail='AI service temporarily unavailable. Please try again.')

    # Safety validator: ensure no code blocks or programming explanations slip through
    if re.search(r'```(?:python|javascript|java|c\+\+|html|css|bash|sh|sql)?\b', str(answer), re.I):
        refusal = OFF_TOPIC_REFUSAL_UR if language == 'ur' else OFF_TOPIC_REFUSAL_EN
        answer = refusal
        intent = 'off_topic'
        matched = []

    products = [{k: p.get(k) for k in ('id', 'sku', 'name', 'category', 'price', 'price_amount',
        'price_currency', 'price_source', 'price_conflict', 'stock', 'stock_status',
        'image_url', 'images', 'url', 'short_description')} for p in matched]

    wa_message = f'Hello SA Embroidery, I need help with: {message}'[:1200]

    return {
        'answer': answer,
        'reply': answer,
        'language': language,
        'intent': intent,
        'type': 'product' if products else 'answer',
        'products': products,
        'whatsapp_url': f'https://wa.me/{WA_NUMBER}?text={quote(wa_message)}',
        'ai_enabled': bool(GROQ_API_KEY),
        'catalog_url': SITE + '/products' if intent == 'product' and not products else None
    }



@app.get('/health')

def health():

    with LOCK: count=len(PRODUCTS); last=LAST_SYNC

    return {'ok':True,'products':count,'last_sync':last,'ai_configured':bool(GROQ_API_KEY),'catalog_loaded':bool(count)}
