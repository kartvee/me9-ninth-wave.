import json, re, hashlib, urllib.request, urllib.error, xml.etree.ElementTree as ET, os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote
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
("Fortanga (Google News feed)","https://news.google.com/rss/search?q=site%3Afortanga.org&hl=en-US&gl=RU&ceid=RU:en")]
COUNTRIES={"Georgia":["georgia","tbilisi","abkhazia","south ossetia"],"Armenia":["armenia","yerevan","nagorno-karabakh"],"Azerbaijan":["azerbaijan","baku","karabakh"],"Kazakhstan":["kazakhstan","astana","almaty"],"Kyrgyzstan":["kyrgyzstan","bishkek"],"Tajikistan":["tajikistan","dushanbe"],"Turkmenistan":["turkmenistan","ashgabat"],"Uzbekistan":["uzbekistan","tashkent"],"Russia":["russia","moscow","kremlin","siberia","chechnya"],"Ukraine":["ukraine","kyiv","kiev"],"World":["united states","china","european union","united nations"]}
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
        "mediazona":"Russia","taiga.info":"Russia","fortanga":"Russia"
    }
    country=next((c for hint,c in source_country.items() if hint in source_low),None)
    if not country:
        country=next((c for c,terms in COUNTRIES.items() if any(t in low for t in terms)),"Regional")
    topic=next((c for c,terms in TOPICS.items() if any(t in low for t in terms)),"Politics")
    return country,topic
def first_text(node,names):
    for name in names:
        el=node.find(name)
        if el is not None and el.text:return el.text.strip()
    return ""
def image_url(node):
    for name in ["{http://search.yahoo.com/mrss/}content","{http://search.yahoo.com/mrss/}thumbnail","enclosure","{http://www.w3.org/2005/Atom}link"]:
        el=node.find(name)
        if el is None:continue
        url=el.attrib.get("url") or el.attrib.get("href","")
        typ=el.attrib.get("type","")
        if url and (name.endswith("link}") and el.attrib.get("rel")!="enclosure"):continue
        if url and (name!="enclosure" or typ.startswith("image/") or re.search(r"\\.(jpg|jpeg|png|webp)(?:\\?|$)",url,re.I)):return url
    raw=ET.tostring(node,encoding="unicode")
    m=re.search(r"<(?:media:content|media:thumbnail)[^>]+url=[\"']([^\"']+)",raw)
    if not m:m=re.search(r"<img[^>]+src=[\"']([^\"']+)",raw,re.I)
    return m.group(1) if m else ""
def translate_to_english(text):
    """Translate non-English feed text to English using Google's public translation endpoint."""
    if not text:return text, "en"
    url="https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q="+quote(text[:1200])
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 ME9-NewsMonitor/1.2"})
    try:
        with urllib.request.urlopen(req,timeout=5) as res:data=json.loads(res.read())
        translated="".join(part[0] for part in data[0] if part and part[0])
        detected=(data[2] or "en").lower() if len(data)>2 else "en"
        return clean(translated) or text, detected
    except Exception as e:
        print("Translation unavailable:",str(e)[:100])
        return text, "unknown"

def ai_enrich(title,excerpt):
    key=os.environ.get("ME9_OPENAI_API_KEY")
    if not key:return None
    payload={"model":"gpt-4.1-mini","input":[{"role":"system","content":"You are a careful news editor. Return JSON only with keys summary_en and translated_title. Write a factual English summary of at most 2 sentences based only on the supplied headline and excerpt. If headline is already English, translated_title must be an empty string. If it is another language, translate the headline to English. Never add facts."},{"role":"user","content":json.dumps({"headline":title,"publisher_excerpt":excerpt},ensure_ascii=False)}],"text":{"format":{"type":"json_object"}}}
    req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=25) as res:body=json.loads(res.read())
        txt="".join(part.get("text","") for item in body.get("output",[]) for part in item.get("content",[]) if part.get("type")=="output_text")
        obj=json.loads(txt)
        return {"summary_en":clean(obj.get("summary_en",""))[:650],"translated_title":clean(obj.get("translated_title",""))[:240],"summary_type":"ai_summary"} if obj.get("summary_en") else None
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
            # Keep Georgian headlines in Georgian and add their English translation.
            # For all other non-English headlines, publish the English translation only.
            translated_title=""
            title_en, detected=translate_to_english(title)
            summary_en=""
            if detected == "ka":
                translated_title=title_en if title_en.lower()!=title.lower() else ""
            elif detected not in ("en","unknown"):
                title=title_en
            if detected not in ("en","unknown"):
                summary_en, _=translate_to_english(excerpt)
            article={"id":key[:16],"title":title,"summary":excerpt if detected in ("en","ka","unknown") else summary_en,"summary_en":summary_en,"translated_title":translated_title,"source":source,"url":link,"image":image_url(node),"published_at":parse_date(pub),"country":country,"topic":topic,"summary_type":"publisher_excerpt","automated":True,"language":"ka" if detected=="ka" else "en"}
            enriched=ai_enrich(title,excerpt)
            if enriched:article.update(enriched)
            items.append(article)
    except Exception as e:print("Feed failed:",source,str(e)[:200])
items.sort(key=lambda x:x["published_at"],reverse=True)
out={"status":"live" if items else "demo","updated_at":datetime.now(timezone.utc).isoformat(),"source_count":len(FEEDS),"active_source_count":feed_ok,"ai_enabled":bool(os.environ.get("ME9_OPENAI_API_KEY")),"articles":items}
os.makedirs("data",exist_ok=True)
with open("data/news.json","w",encoding="utf-8") as f:json.dump(out,f,ensure_ascii=False,indent=2)
print("Collected",len(out["articles"]),"articles;",feed_ok,"feeds responded; AI enrichment",out["ai_enabled"])
