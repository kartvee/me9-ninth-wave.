import json, re, hashlib, urllib.request, urllib.error, xml.etree.ElementTree as ET, os
from langdetect import detect, DetectorFactory, LangDetectException
DetectorFactory.seed = 0
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urljoin, urlparse, urlencode
from concurrent.futures import ThreadPoolExecutor
from html import unescape
FEEDS=[
# Established international outlets
("BBC News","https://feeds.bbci.co.uk/news/world/europe/rss.xml"),
("The Guardian","https://www.theguardian.com/world/europe-news/rss"),
("France 24","https://www.france24.com/en/europe/rss"),
("RFE/RL","https://www.rferl.org/api/z-pqpiev-qpp"),
("Eurasianet","https://eurasianet.org/feed"),
("The Economist","https://www.economist.com/the-world-this-week/rss.xml"),
("CNN World","https://rss.cnn.com/rss/edition_world.rss"),
("POLITICO Europe","https://www.politico.eu/feed/"),
("The Telegraph","https://www.telegraph.co.uk/rss.xml"),
# Reuters stopped maintaining its former public RSS; Google News site-search RSS keeps attribution on original Reuters URLs.
("Reuters (Google News feed)","https://news.google.com/rss/search?q=site%3Areuters.com&hl=en-US&gl=US&ceid=US:en"),
("TASS (Google News feed)","https://news.google.com/rss/search?q=site%3Atass.com&hl=en-US&gl=US&ceid=US:en"),
("Sputnik (Google News feed)","https://news.google.com/rss/search?q=site%3Asputnikglobe.com+OR+site%3Asputniknews.com&hl=en-US&gl=US&ceid=US:en"),
("Current Time (Google News feed)","https://news.google.com/rss/search?q=site%3Acurrenttime.tv&hl=en-US&gl=US&ceid=US:en"),
# South Caucasus
("Agenda.ge","https://agenda.ge/en/rss"),
("Civil Georgia","https://civil.ge/feed"),
("OC Media","https://oc-media.org/feed/"),
("Interpressnews (Google News feed)","https://news.google.com/rss/search?q=site%3Aipn.ge&hl=en-US&gl=GE&ceid=GE:en"),
("Netgazeti","https://netgazeti.ge/feed/"),
("Radio Tavisupleba (Georgian RFE/RL)","https://www.radiotavisupleba.ge/api/z-pqpiev-qpp"),
("Armenia (Google News feed)","https://news.google.com/rss/search?q=Armenia+OR+Yerevan&hl=en-US&gl=US&ceid=US:en"),
("Azerbaijan (Google News feed)","https://news.google.com/rss/search?q=Azerbaijan+OR+Baku+OR+Karabakh&hl=en-US&gl=US&ceid=US:en"),
("Turan (Google News feed)","https://news.google.com/rss/search?q=site%3Aturan.az&hl=en-US&gl=AZ&ceid=AZ:en"),
# Country-level discovery feeds complement individual publishers and improve smaller-country coverage.
("Kazakhstan (Google News feed)","https://news.google.com/rss/search?q=Kazakhstan+OR+Astana+OR+Almaty&hl=en-US&gl=US&ceid=US:en"),
("Kyrgyzstan (Google News feed)","https://news.google.com/rss/search?q=Kyrgyzstan+OR+Bishkek&hl=en-US&gl=US&ceid=US:en"),
("Tajikistan (Google News feed)","https://news.google.com/rss/search?q=Tajikistan+OR+Dushanbe&hl=en-US&gl=US&ceid=US:en"),
("Turkmenistan (Google News feed)","https://news.google.com/rss/search?q=Turkmenistan+OR+Ashgabat&hl=en-US&gl=US&ceid=US:en"),
("Uzbekistan (Google News feed)","https://news.google.com/rss/search?q=Uzbekistan+OR+Tashkent&hl=en-US&gl=US&ceid=US:en"),
# Central Asia
("Asia-Plus","https://asiaplustj.info/en/feed"),
("Avesta","https://avesta.tj/feed/"),
("Faraj (Google News feed)","https://news.google.com/rss/search?q=site%3Afaraj.tj&hl=en-US&gl=TJ&ceid=TJ:en"),
("24.kg","https://24.kg/rss.xml"),
("Kaktus Media","https://kaktus.media/rss"),
("KyrTAG (Google News feed)","https://news.google.com/rss/search?q=site%3Akyrtag.kg&hl=en-US&gl=KG&ceid=KG:en"),
("Kun.uz","https://kun.uz/news/rss"),
("Xabar.uz (Google News feed)","https://news.google.com/rss/search?q=site%3Axabar.uz&hl=en-US&gl=UZ&ceid=UZ:en"),
("UzDaily (Google News feed)","https://news.google.com/rss/search?q=site%3Auzdaily.uz&hl=en-US&gl=UZ&ceid=UZ:en"),
("Turkmen.news","https://turkmen.news/feed/"),
# Russia / Eastern Europe
("Mediazona","https://zona.media/rss"),
("Taiga.info (Google News feed)","https://news.google.com/rss/search?q=site%3Ataiga.info&hl=en-US&gl=RU&ceid=RU:en"),
("Fortanga (Google News feed)","https://news.google.com/rss/search?q=site%3Afortanga.org&hl=en-US&gl=RU&ceid=RU:en"),
# Czechia: established press, public broadcaster, radio and national news agency.
("CTK / Czech News Agency","https://news.google.com/rss/search?q=site%3Aceskenoviny.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("iDNES / Mlada Fronta Dnes","https://news.google.com/rss/search?q=site%3Aidnes.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("Lidovky / Lidove Noviny","https://news.google.com/rss/search?q=site%3Alidovky.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("Novinky / Pravo","https://news.google.com/rss/search?q=site%3Anovinky.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("Blesk","https://news.google.com/rss/search?q=site%3Ablesk.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("Hospodarske noviny","https://news.google.com/rss/search?q=site%3Ahn.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("Respekt","https://news.google.com/rss/search?q=site%3Arespekt.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("Czech Television / CT24","https://news.google.com/rss/search?q=site%3Act24.ceskatelevize.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("TV Nova","https://news.google.com/rss/search?q=site%3Atn.nova.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("CNN Prima News","https://news.google.com/rss/search?q=site%3Acnn.iprima.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("Czech Radio / Radio Prague International","https://news.google.com/rss/search?q=site%3Aenglish.radio.cz+OR+site%3Airozhlas.cz&hl=en-US&gl=CZ&ceid=CZ:en"),
("Czechia (Google News discovery feed)","https://news.google.com/rss/search?q=Czechia+OR+Prague+OR+Czech+government&hl=en-US&gl=CZ&ceid=CZ:en")]
COUNTRIES={"Georgia":["georgia","tbilisi","abkhazia","south ossetia"],"Armenia":["armenia","yerevan","nagorno-karabakh"],"Azerbaijan":["azerbaijan","baku","karabakh"],"Kazakhstan":["kazakhstan","astana","almaty"],"Kyrgyzstan":["kyrgyzstan","bishkek"],"Tajikistan":["tajikistan","dushanbe"],"Turkmenistan":["turkmenistan","ashgabat"],"Uzbekistan":["uzbekistan","tashkent"],"Russia":["russia","moscow","kremlin","siberia","chechnya"],"Ukraine":["ukraine","kyiv","kiev"],"Czechia":["czechia","czech republic","prague","praha","brno","ostrava","česko","česká republika"],"World":["united states","china","european union","united nations"]}
TOPICS={"Security":["security","military","war","defence","defense","border","attack","army","conflict"],"Diplomacy":["diplomacy","minister","summit","agreement","ambassador","talks","foreign affairs"],"Economy":["economy","trade","inflation","gdp","business","market","finance"],"Energy":["energy","oil","gas","pipeline","electricity","nuclear"],"Sports":["football","sport","championship","olympic"],"Technology":["technology","cyber","artificial intelligence","digital"],"Society":["protest","rights","education","society","school"],"Politics":["politic","parliament","president","government","election","vote"]}
def clean(s):
    return re.sub(r"\\s+"," ",unescape(re.sub(r"<[^>]+>"," ",s or ""))).strip()
def parse_date(s):
    try:return parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
    except Exception:return datetime.now(timezone.utc).isoformat()
def classify(text, source=""):
    low=text.lower()
    source_low=source.lower()
    source_country={
        "agenda.ge":"Georgia","civil georgia":"Georgia","interpressnews":"Georgia",
        "netgazeti":"Georgia","radio tavisupleba":"Georgia",
        "asia-plus":"Tajikistan","avesta":"Tajikistan","faraj":"Tajikistan",
        "24.kg":"Kyrgyzstan","kaktus media":"Kyrgyzstan","kyrtag":"Kyrgyzstan",
        "kun.uz":"Uzbekistan","xabar.uz":"Uzbekistan","uzdaily":"Uzbekistan",
        "turkmen.news":"Turkmenistan","turan":"Azerbaijan",
        "mediazona":"Russia","taiga.info":"Russia","fortanga":"Russia","ctk / czech":"Czechia","idnes":"Czechia","lidovky":"Czechia","novinky":"Czechia","blesk":"Czechia","hospodarske noviny":"Czechia","respekt":"Czechia","czech television":"Czechia","ct24":"Czechia","tv nova":"Czechia","cnn prima":"Czechia","czech radio":"Czechia","czechia (google news":"Czechia",
        "ctk / czech":"Czechia","idnes":"Czechia","lidovky":"Czechia","novinky":"Czechia","blesk":"Czechia","hospodarske noviny":"Czechia","respekt":"Czechia","czech television":"Czechia","ct24":"Czechia","tv nova":"Czechia","cnn prima":"Czechia","czech radio":"Czechia","czechia (google news":"Czechia"
    }
    country=next((c for c,terms in COUNTRIES.items() if any(t in low for t in terms)),None)
    if not country:
        country=next((c for hint,c in source_country.items() if hint in source_low),"Regional")
    topic=next((c for c,terms in TOPICS.items() if any(t in low for t in terms)),"Politics")
    return country,topic
def first_text(node,names):
    for name in names:
        el=node.find(name)
        if el is not None and el.text:return el.text.strip()
    return ""
def image_url(node):
    """Prefer the largest explicitly supplied image, not a tiny RSS thumbnail."""
    candidates = []
    media = "{http://search.yahoo.com/mrss/}"
    atom = "{http://www.w3.org/2005/Atom}"
    for name in [media+"content", media+"thumbnail", "enclosure", atom+"link"]:
        for el in node.findall(name):
            url = el.attrib.get("url") or el.attrib.get("href", "")
            typ = el.attrib.get("type", "").lower()
            if not url or (name == atom+"link" and el.attrib.get("rel") != "enclosure"):
                continue
            if name == "enclosure" and not (typ.startswith("image/") or re.search(r"\.(jpg|jpeg|png|webp|avif)(?:\?|$)", url, re.I)):
                continue
            if typ and not typ.startswith("image/") and name != media+"thumbnail":
                continue
            try:
                width = int(el.attrib.get("width", 0) or 0)
                height = int(el.attrib.get("height", 0) or 0)
            except ValueError:
                width = height = 0
            # Prefer known high-resolution variants; retain unknown-size images as fallback.
            score = (width * height) if width and height else (width * 1000 if width else 1)
            candidates.append((score, url))
    raw = ET.tostring(node, encoding="unicode")
    # Feed descriptions sometimes contain the publisher's featured image.
    for match in re.finditer(r"<img\b[^>]*(?:src|data-src)=[\"']([^\"']+)[\"'][^>]*>", raw, re.I):
        url = unescape(match.group(1))
        if url.startswith(("https://", "http://")):
            candidates.append((500000, url))
    if not candidates:
        return ""
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]

def page_og_image(article):
    """Fetch a publisher's Open Graph image as a higher-quality alternative to RSS thumbnails."""
    url = article.get("url", "")
    if not url.startswith(("https://", "http://")):
        return None
    host = re.sub(r"^www\.", "", urlparse(url).netloc.lower())
    if host == "news.google.com":
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; ME9-NewsMonitor/1.3)", "Accept":"text/html"})
        with urllib.request.urlopen(req, timeout=4) as response:
            if "html" not in response.headers.get("Content-Type", "").lower():
                return None
            html = response.read(500000).decode("utf-8", errors="ignore")
            final_url = response.geturl()
        metas = re.findall(r"<meta\b[^>]*>", html, re.I)
        found = {}
        for tag in metas:
            key_match = re.search(r"\b(?:property|name)\s*=\s*[\"']([^\"']+)[\"']", tag, re.I)
            val_match = re.search(r"\bcontent\s*=\s*[\"']([^\"']+)[\"']", tag, re.I)
            if key_match and val_match:
                found[key_match.group(1).lower()] = unescape(val_match.group(1).strip())
        image = found.get("og:image") or found.get("og:image:url") or found.get("twitter:image") or found.get("twitter:image:src")
        if not image:
            return None
        image = urljoin(final_url, image)
        if not image.startswith(("https://", "http://")) or re.search(r"\.(svg|gif)(?:\?|$)", image, re.I):
            return None
        if re.search(r"(?:logo|favicon|avatar|sprite)", image, re.I):
            return None
        return image
    except Exception as e:
        return None

def detect_language(text):
    """Detect source language without translating it."""
    text = clean(text)
    if not text:
        return "unknown"
    if re.search("[ა-ჰ]", text):
        return "ka"
    letters = re.findall("[A-Za-zА-Яа-я]", text)
    if len(letters) < 12:
        return "unknown"
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

def ai_enrich(title,excerpt):
    key=os.environ.get("ME9_OPENAI_API_KEY")
    if not key:return None
    payload={"model":"gpt-4.1-mini","input":[{"role":"system","content":"You are a careful news editor. Return JSON only with key summary_en. Write a factual English summary of at most 2 sentences based only on the supplied English headline and excerpt. Do not translate the headline. Never add facts."},{"role":"user","content":json.dumps({"headline":title,"publisher_excerpt":excerpt},ensure_ascii=False)}],"text":{"format":{"type":"json_object"}}}
    req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=25) as res:body=json.loads(res.read())
        txt="".join(part.get("text","") for item in body.get("output",[]) for part in item.get("content",[]) if part.get("type")=="output_text")
        obj=json.loads(txt)
        return {"summary_en":clean(obj.get("summary_en",""))[:650],"summary_type":"ai_summary"} if obj.get("summary_en") else None
    except Exception as e:
        print("AI enrichment unavailable:",str(e)[:150]);return None
items=[];seen=set();feed_ok=0
for source,url in FEEDS:
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ME9-NewsMonitor/1.1 (+RSS reader; contact site owner)"})
        with urllib.request.urlopen(req,timeout=18) as response:root=ET.fromstring(response.read())
        nodes=root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
        feed_ok+=1
        for node in nodes:
            title=clean(first_text(node,["title","{http://www.w3.org/2005/Atom}title"]))
            link=first_text(node,["link"])
            if not link:
                l=node.find("{http://www.w3.org/2005/Atom}link");link=l.attrib.get("href","") if l is not None else ""
            excerpt=clean(first_text(node,["description","summary","{http://www.w3.org/2005/Atom}summary","{http://www.w3.org/2005/Atom}content"]))[:650]
            pub=first_text(node,["pubDate","published","updated","{http://www.w3.org/2005/Atom}published","{http://www.w3.org/2005/Atom}updated"])
            if not title or not link or not link.startswith(("https://","http://")):continue
            if source=="CNN World" and any(x in link.lower() for x in ["lendingtree.com","fool.com","credit-card","cashoutoptions"]):continue
            key=hashlib.sha256(re.sub(r"[^a-z0-9]","",title.lower()).encode()).hexdigest()
            if key in seen:continue
            seen.add(key);country,topic=classify(title+" "+excerpt,source)
            # Keep only stories whose headline and available excerpt are Georgian or English.
            # No translation is performed for other source languages.
            title_language=detect_language(title)
            excerpt_language=detect_language(excerpt) if excerpt else title_language
            if title_language not in ("ka","en") or excerpt_language not in ("ka","en"):
                continue
            language="ka" if title_language=="ka" else "en"
            if excerpt and excerpt_language != language:
                continue
            article={"id":key[:16],"title":title,"summary":excerpt,"summary_en":"","translated_title":"","source":source,"url":link,"image":image_url(node),"published_at":parse_date(pub),"country":country,"topic":topic,"summary_type":"publisher_excerpt","automated":True,"language":language}
            if language=="en":
                enriched=ai_enrich(title,excerpt)
                if enriched:article.update(enriched)
            items.append(article)
    except Exception as e:print("Feed failed:",source,str(e)[:200])
items.sort(key=lambda x:x["published_at"],reverse=True)
# Prefer publisher-provided photos. Only search open-license repositories when no publisher image exists.
image_candidates = [item for item in items[:60] if item.get("url")]
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = {pool.submit(page_og_image, item): item for item in image_candidates if not item.get("image")}
    for future, item in list(futures.items()):
        try:
            better_image = future.result(timeout=7)
            if better_image:
                item["image"] = better_image
        except Exception:
            pass

os.makedirs("data",exist_ok=True)
cache_path="data/image_cache.json"
try:
    with open(cache_path,"r",encoding="utf-8") as f:image_cache=json.load(f)
    if not isinstance(image_cache,dict):image_cache={}
except (OSError,ValueError):
    image_cache={}
def image_terms(article):
    text=" ".join([article.get("title",""),article.get("summary",""),article.get("country",""),article.get("topic","")])
    words=re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}",text.lower())
    stop={"with","from","that","this","after","before","over","under","into","about","says","said","will","have","has","their","they","them","its","for","and","the","are","was","were","has","had","but","not","new","latest","report","reports","news","official","officials"}
    return list(dict.fromkeys(w for w in words if w not in stop))[:10]
def openverse_photo(article):
    terms=image_terms(article)
    if not terms:return None
    query=" ".join(terms[:7])
    params={"q":query,"license":"cc0,pdm,by,by-sa","license_type":"commercial","category":"photograph","aspect_ratio":"wide","size":"medium","page_size":20,"filter_dead":"true"}
    endpoint="https://api.openverse.org/v1/images/?" + urlencode(params)
    req=urllib.request.Request(endpoint,headers={"User-Agent":"ME9-NewsMonitor/1.0 (open-license editorial image search)"})
    try:
        with urllib.request.urlopen(req,timeout=12) as response:data=json.loads(response.read())
    except Exception as e:
        print("Openverse search unavailable:",str(e)[:120]);return None
    article_words=set(terms)
    ranked=[]
    for result in data.get("results",[]):
        image_url=result.get("url","")
        if not image_url.startswith("https://"):continue
        license_code=(result.get("license") or "").lower()
        if license_code not in ("cc0","pdm","by","by-sa"):continue
        title_words=set(re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}",(result.get("title","")+" "+" ".join(t.get("name","") for t in result.get("tags",[]))).lower()))
        overlap=article_words & title_words
        if not overlap:continue
        score=len(overlap)*3 + (2 if result.get("category")=="photograph" else 0) + (1 if result.get("width",0)>=1000 else 0)
        ranked.append((score,result))
    if not ranked:return None
    ranked.sort(key=lambda pair:pair[0],reverse=True)
    result=ranked[0][1]
    return {"image":result["url"],"image_source":"Openverse","image_page":result.get("foreign_landing_url") or result.get("detail_url",""),"image_credit":result.get("creator") or "Unknown creator","image_creator_url":result.get("creator_url",""),"image_license":(result.get("license") or "").upper()+(" "+str(result.get("license_version")) if result.get("license_version") else ""),"image_license_url":result.get("license_url",""),"image_attribution":result.get("attribution","")}
# Search a bounded batch on each scheduled run and persist both hits and misses.
# Subsequent five-minute runs continue through the backlog without repeating searches.
new_searches=0
for article in items:
    if article.get("image"):continue
    cached=image_cache.get(article["id"])
    if cached:
        if cached.get("image"):
            article.update({k:v for k,v in cached.items() if k!="checked_at"})
        continue
    if new_searches>=24:continue
    photo=openverse_photo(article)
    image_cache[article["id"]]={"checked_at":datetime.now(timezone.utc).isoformat(),**(photo or {})}
    if photo:article.update(photo)
    new_searches+=1
    import time
    time.sleep(0.35)
with open(cache_path,"w",encoding="utf-8") as f:json.dump(image_cache,f,ensure_ascii=False,indent=2)
out={"status":"live" if items else "demo","updated_at":datetime.now(timezone.utc).isoformat(),"source_count":len(FEEDS),"active_source_count":feed_ok,"ai_enabled":bool(os.environ.get("ME9_OPENAI_API_KEY")),"openverse_searches_this_run":new_searches,"openverse_cached_images":sum(1 for v in image_cache.values() if v.get("image")),"articles":items}
with open("data/news.json","w",encoding="utf-8") as f:json.dump(out,f,ensure_ascii=False,indent=2)
print("Collected",len(out["articles"]),"articles;",feed_ok,"feeds responded;",new_searches,"Openverse searches;",out["openverse_cached_images"],"cached open-license photos; AI enrichment",out["ai_enabled"])