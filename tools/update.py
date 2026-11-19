import datetime as dt,json,re,sys,urllib.request
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo
IDS=[294,297,304,321,325,371,383,397]
URL='https://lastwarrank.com/bracket/1543'
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None
 def handle_starttag(self,t,a):
  if t=='table':self.table=[]
  elif t=='tr' and self.table is not None:self.row=[]
  elif t in ('th','td') and self.row is not None:self.cell=[]
 def handle_data(self,s):
  if self.cell is not None:self.cell.append(s)
 def handle_endtag(self,t):
  if t in ('th','td') and self.cell is not None:self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
  elif t=='tr' and self.row is not None:self.table.append(self.row);self.row=None
  elif t=='table' and self.table is not None:self.tables.append(self.table);self.table=None

def num(s):
 m=re.search(r'(\d+(?:\.\d+)?)\s*([BMTK]?)',s.replace(',',''),re.I)
 return round(float(m[1])*{'':1,'K':1e3,'M':1e6,'B':1e9,'T':1e12}[m[2].upper()]) if m else None

def parse(html):
 p=Parser();p.feed(html)
 for t in p.tables:
  if not t:continue
  h=[re.sub('[^a-z]','',v.lower()) for v in t[0]]
  names=['server','heropower','power','kills','alliances','playerslisted','topalliance']
  if not all(x in h for x in names):continue
  ix={x:h.index(x) for x in names};found={}
  for r in t[1:]:
   if len(r)<=max(ix.values()):continue
   match=re.search(r'#\s*(\d+)',r[ix['server']])
   if not match:continue
   sid=int(match[1])
   if sid not in IDS:continue
   rec={'server':sid,'hero_power':num(r[ix['heropower']]),'power':num(r[ix['power']]),'kills':num(r[ix['kills']]),'alliances':num(r[ix['alliances']]),'players_listed':num(r[ix['playerslisted']]),'top_alliance':r[ix['topalliance']],'top200_thp':None,'top10_thp':None,'top50_thp':None,'kill_delta':None}
   if rec['hero_power'] is not None:found[sid]=rec
  if len(found)==8:return [found[i] for i in IDS]
 raise ValueError('8-server overview table not found; last saved data preserved')

if __name__=='__main__':
 now=dt.datetime.now(dt.timezone.utc);local=now.astimezone(ZoneInfo('Europe/Budapest'))
 if '--force' not in sys.argv and local.hour not in (2,14):print('Outside scheduled hour');sys.exit(0)
 req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 (compatible; Season7WarzoneIntel/1.0)','Accept':'text/html'})
 try:
  with urllib.request.urlopen(req,timeout=25) as resp:page=resp.read(3000000).decode('utf-8','replace')
  records=parse(page)
 except Exception as e:print('No update; retained previous snapshot:',e,file=sys.stderr);sys.exit(1)
 path=Path('data/overview.json');old=json.loads(path.read_text()) if path.exists() else {}
 prev={x['server']:x for x in old.get('servers',[])}
 for x in records:
  before=prev.get(x['server'],{}).get('kills');after=x['kills']
  if old.get('status')=='updated' and isinstance(before,int) and isinstance(after,int) and after>=before:x['kill_delta']=after-before
 path.parent.mkdir(exist_ok=True)
 path.write_text(json.dumps({'source':URL,'retrieved_at':now.isoformat(),'status':'updated','servers':records},ensure_ascii=False,indent=2)+'\n')
 print('Updated all 8 servers')
