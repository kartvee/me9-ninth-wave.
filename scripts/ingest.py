import json, re, hashlib, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape

FEEDS = [
("BBC News","https://feeds.bbci.co.uk/news/world/europe/rss.xml"),
("The Guardian","https://www.theguardian.com/world/europe-news/rss"),
("France 24","https://www.france24.com/en/europe/rss"),
("RFE/RL","https://www.rferl.org/api/z-pqpiev-qpp"),
("Eurasianet","https://eurasianet.org/feed"),
("Agenda.ge","https://agenda.ge/en/rss"),
("Civil Georgia","https://civil.ge/feed"),
("OC Media","https://oc-media.org/feed/"),
("Asia-Plus","https://asiaplustj.info/en/feed"),
("The Economist","https://www.economist.com/the-world-this-week/rss.xml"),
("CNN World","http://rss.cnn.com/rss/edition_world.rss"),
("POLITICO Europe","https://www.politico.eu/feed/"),
]
COUNTRIES = {
"Georgia":["georgia","tbilisi","abkhazia","south ossetia"],
"Armenia":["armenia","yerevan","nagorno-karabakh"],
"Azerbaijan":["azerbaijan","baku","karabakh"],
"Kazakhstan":["kazakhstan","astana","almaty"],
"Kyrgyzstan":["kyrgyzstan","bishkek"],
"Tajikistan":["tajikistan","dushanbe"],
"Turkmenistan":["turkmenistan","ashgabat"],
"Uzbekistan":["uzbekistan","tashkent"],
"Russia":["russia","moscow","kremlin","siberia"],
"Ukraine":["ukraine","kyiv","kiev"],
"World":["united states","china","european union","united nations"]
}
TOPICS={"Security":["security","military","war","defence","defense","border","attack"],"Diplomacy":["diplomacy","minister","summit","agreement","ambassador","talks"],"Economy":["economy","trade","inflation","gdp","business","market"],"Energy":["energy","oil","gas","pipeline","electricity","nuclear"],"Sports":["football","sport","championship","olympic"],"Technology":["technology","cyber","artificial intelligence","digital"],"Society":["protest","rights","education","society","election"],"Politics":["politic","parliament","president","government","election","vote"]}
def clean(s):
    s=unescape(re.sub(r"<[^>]+>"," ",s or ""))
    return re.sub(r"\s+"," ",s).strip()
def parse_date(s):
    try:
        d=parsedate_to_datetime(s)
        return d.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()
def classify(text):
    low=text.lower()
    country=next((c for c,terms in COUNTRIES.items() if any(t in low for t in terms)), "Regional")
    topic=next((c for c,terms in TOPICS.items() if any(t in low for t in terms)), "Politics")
    return country,topic
items=[]; seen=set()
for source,url in FEEDS:
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ME9-NewsMonitor/1.0 (public RSS aggregator)"})
        with urllib.request.urlopen(req,timeout=15) as response:
            root=ET.fromstring(response.read())
        nodes=root.findall(".//item")
        if not nodes:
            nodes=root.findall(".//{http://www.w3.org/2005/Atom}entry")
        for node in nodes[:30]:
            def get(*names):
                for name in names:
                    found=node.find(name)
                    if found is not None and found.text: return found.text
                return ""
            title=clean(get("title","{http://www.w3.org/2005/Atom}title"))
            link=get("link")
            if not link:
                l=node.find("{http://www.w3.org/2005/Atom}link")
                link=l.attrib.get("href","") if l is not None else ""
            summary=clean(get("description","summary","{http://www.w3.org/2005/Atom}summary","{http://www.w3.org/2005/Atom}content"))[:420]
            pub=get("pubDate","published","updated","{http://www.w3.org/2005/Atom}published","{http://www.w3.org/2005/Atom}updated")
            if not title or not link: continue
            key=hashlib.sha256(re.sub(r"[^a-z0-9]","",title.lower()).encode()).hexdigest()
            if key in seen: continue
            seen.add(key)
            country,topic=classify(title+" "+summary)
            items.append({"id":key[:16],"title":title,"summary":summary,"source":source,"url":link,"published_at":parse_date(pub),"country":country,"topic":topic,"summary_type":"publisher_excerpt","automated":True})
    except Exception as e:
        print("Feed failed:",source,str(e)[:200])
items.sort(key=lambda x:x["published_at"],reverse=True)
out={"status":"live" if items else "demo","updated_at":datetime.now(timezone.utc).isoformat(),"source_count":len(FEEDS),"articles":items[:180]}
with open("data/news.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)
print("Collected",len(out["articles"]),"articles from",len(FEEDS),"configured feeds")
