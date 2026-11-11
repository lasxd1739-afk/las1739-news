#!/usr/bin/env python3
"""Collect public article links once per day. Archive by collection date, not source publication date."""
import datetime as dt, email.utils, hashlib, json, os, re, urllib.parse
import feedparser
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/'news.json'
TZ=ZoneInfo('Asia/Ho_Chi_Minh')
TODAY=dt.datetime.now(TZ).date().isoformat()
NOW=dt.datetime.now(TZ).strftime('%d/%m/%Y %H:%M (GMT+7)')
KEYWORDS=('tcvn','astm','thí nghiệm','thử nghiệm','vật liệu xây dựng','bê tông','nhựa đường','cốt liệu','xi măng','địa kỹ thuật','kiểm định','tiêu chuẩn','construction materials','concrete','asphalt','geotechnical','aggregate','cement','standard')
SOURCES=[
  ('VSQI qua Google News','site:tieuchuan.vsqi.gov.vn (TCVN OR "tiêu chuẩn" OR "vật liệu")'),
  ('Bộ Xây dựng qua Google News','site:moc.gov.vn ("vật liệu xây dựng" OR "thí nghiệm" OR "tiêu chuẩn")'),
  ('ASTM qua Google News','site:astm.org (concrete OR asphalt OR aggregate OR geotechnical OR standards)'),
]

def make_rss(q):
 return 'https://news.google.com/rss/search?q='+urllib.parse.quote(q)+'&hl=vi&gl=VN&ceid=VN:vi'

def published(e):
 obj=e.get('published_parsed') or e.get('updated_parsed')
 if obj:
  try:return dt.datetime(*obj[:6],tzinfo=dt.timezone.utc).astimezone(TZ).strftime('%d/%m/%Y')
  except Exception:pass
 return ''

def discover():
 result=[];ok=0
 for source,query in SOURCES:
  feed=feedparser.parse(make_rss(query),request_headers={'User-Agent':'LAS1739-News-Archive/1.0'})
  if feed.get('bozo') and not feed.entries:
   print('Lỗi nguồn:',source,repr(feed.get('bozo_exception')))
   continue
  ok+=1
  for e in feed.entries[:24]:
   title=re.sub(r'\s+',' ',e.get('title','')).strip()
   url=e.get('link','')
   if not title or not url.startswith('https://'):continue
   if not any(x in title.casefold() for x in KEYWORDS):continue
   uid=hashlib.sha256(url.encode()).hexdigest()[:22]
   result.append({'id':uid,'title':title[:240],'source':source,'url':url,'published':published(e),'saved_on':TODAY})
 return result,ok

def main():
 data={'last_checked':'','latest':[],'archive':[],'seen_ids':[],'latest_day':''}
 if TARGET.exists():
  try:data.update(json.loads(TARGET.read_text(encoding='utf-8')))
  except (ValueError,OSError):pass
 items,ok=discover()
 if not ok:
  print('Không có nguồn phản hồi thành công. Giữ nguyên dữ liệu cũ.');return
 seen=set(data.get('seen_ids') or [])
 new=[]
 for x in items:
  if x['id'] not in seen:
   new.append(x);seen.add(x['id'])
 new=new[:35]
 # When next calendar day begins, move previous day's collected items into the archive.
 if data.get('latest_day') and data['latest_day']!=TODAY:
  arch=list(data.get('archive') or [])
  ids={x.get('id') for x in arch}
  for x in data.get('latest') or []:
   if x.get('id') not in ids:arch.append(x);ids.add(x.get('id'))
  data['archive']=sorted(arch,key=lambda x:(x.get('saved_on',''),x.get('published','')),reverse=True)[:1500]
  data['latest']=[]
 if data.get('latest_day')==TODAY:
  known={x.get('id') for x in data.get('latest') or []}
  data['latest']=(data.get('latest') or [])+[x for x in new if x['id'] not in known]
 else:
  data['latest']=new
 data['latest_day']=TODAY
 data['last_checked']=NOW
 data['seen_ids']=list(seen)[-10000:]
 TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Ngày',TODAY,'nguồn thành công',ok,'tin mới',len(new),'lưu trữ',len(data.get('archive') or []))

if __name__=='__main__':main()
