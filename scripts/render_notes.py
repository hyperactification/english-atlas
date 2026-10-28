from pathlib import Path
import json,re,html,math,io,argparse,os,copy
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor,Color,white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from grammar_terms import english_terms
from lexical_resources import format_vocabulary
from runtime_support import register_pdf_fonts

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description="Render reviewed English sentence notes as a color PDF and an offline interactive HTML file.")
parser.add_argument('--input',required=True,type=Path)
parser.add_argument('--output-dir',required=True,type=Path)
parser.add_argument('--qa-dir',type=Path)
parser.add_argument('--basename')
parser.add_argument('--font-cn',type=Path)
parser.add_argument('--font-cn-bold',type=Path)
parser.add_argument('--font-en',type=Path)
parser.add_argument('--font-en-bold',type=Path)
args=parser.parse_args()
book=json.loads(args.input.read_text(encoding='utf-8-sig'))
meta=book['meta'];entries=copy.deepcopy(book['entries']);groups=copy.deepcopy(book['groups'])
TOTAL=len(entries);CHAPTER=meta.get('chapter','English Atlas');TITLE=meta['title']
GLOSSARY=[(g['term'],g['translation'],g['explanation'],'  '.join(str(i) for i in g['examples'])) for g in book['glossary']]
OUT=args.output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True)
QA=(args.qa_dir or args.input.resolve().parent/'qa').resolve();QA.mkdir(parents=True,exist_ok=True)
BASENAME=re.sub(r'[<>:"/\\|?*]','_',args.basename or TITLE).strip(' .')
if not BASENAME:raise ValueError('A non-empty output basename is required')
FONT_SELECTION=register_pdf_fonts(args,book)
(QA/'fonts.json').write_text(json.dumps(FONT_SELECTION,ensure_ascii=False,indent=2),encoding='utf-8')
SOURCE_LINE=f"来源：{meta.get('source_author','')}《{meta['source_name']}》，原文{meta['source_pages']}页。"
INK='#17263C';MUTED='#64748B';BLUE='#2457BD';RED='#B84132';PURPLE='#7446A7';TEAL='#167361';AMBER='#945B09';PAPER='#FCFCF9';BORDER='#DDE4EA'
W,H=595.276,841.89;M=40;CW=W-2*M
def E(s):return html.escape(str(s),quote=False)
def txt(s):return E(english_terms(s))
def hc(s):return HexColor(s)

for i,g in enumerate(groups):g['no']=i+1

ROLE_MAP={
'主语':'Subject','主语中心':'Subject head','否定主语':'Negative subject','形式主语':'Formal subject','真实主语':'Real subject','真正主语':'Real subject','谓语':'Predicate','谓语结构':'Predicate','被动谓语':'Passive predicate','系动词':'Linking verb','系表':'Linking verb + complement','系表结构':'Linking verb + complement','否定系表':'Negated linking structure','宾语':'Object','宾语及限定':'Object + modifier','表语':'Subject complement','宾语补足语':'Object complement','后置定语':'Postmodifier','定语':'Modifier','所属定语':'Possessive modifier','来源定语':'Source modifier','风险来源定语':'Source modifier','条件前置':'Fronted adverbial','部分倒装':'Partial inversion','存在句谓语':'Existential predicate','存在结构':'Existential structure','存在事物':'Real subject','转折连接':'Contrast','否定祈使':'Negative imperative',
'谓语与宾语':'Predicate + object','谓语与时间':'Predicate + time','谓语与时长':'Predicate + duration','所属':'Possession','来源':'Source','原因':'Reason','目的':'Purpose','时间':'Time','地点':'Place','方式':'Manner','范围':'Scope','条件':'Condition','对象':'Target','补充说明':'Extra information','对照':'Comparison','评价':'Evaluation','补足内容':'Complement','情境':'Context','关联因素':'Related factor','用途':'Use','作用':'Effect','认识对象':'Target','适应对象':'Target','保护目标':'Target','受助对象':'Beneficiary','单一依据':'Criterion','依据':'Basis','场合':'Setting','时间范围':'Time span','时间关系':'Time order','先发生':'Earlier event','后发生':'Later event','先后次序':'Sequence','传播范围':'Scope','群体范围':'Group','发生领域':'Domain','发布平台':'Platform','所需条件':'Requirement','诱惑来源':'Source','引向结论':'Conclusion','原句搭配':'Original wording','意愿内容':'Intention','反对行为':'Opposed action','不赞成行为':'Disapproved action','禁止行为':'Prohibited action','克制行为':'Refrained action','被阻止行为':'Prevented action','受阻行为':'Hindered action','帮助内容':'Helped action','努力目标':'Intended goal','停顿目的':'Purpose','逐利目的':'Purpose','复习目标':'Study goal','忙碌事项':'Activity','到期时间':'Expiry time','提交期限':'Deadline','触发条件':'Condition','适用条件':'Condition','写作情境':'Context','同时发生':'Concurrent action','须停止的活动':'Stopped activity','决定内容':'Decision','同意内容':'Agreement','投票决定':'Decision','权利内容':'Scope of rights','消息内容':'News content','修饰法律':'Relative clause','因素的限定':'Relative clause','排除':'Exclusion','移除范围':'Removal source','动作一':'Action 1','动作二':'Action 2','对象一':'Object 1','对象二':'Object 2','关系一端':'Endpoint 1','关系另一端':'Endpoint 2','辩解对象':'Excused behavior','可以做到':'Possible action','无法做到':'Impossible action'}
def role(s):
    if s=='目标':return 'Goal'
    r=ROLE_MAP.get(s,s)
    if re.search('[\u4e00-\u9fff]',r):r=english_terms(r)
    return r
def color_for(r):
    s=r.lower()
    if 'object' in s or 'complement' in s or s in ['target','beneficiary']:return PURPLE
    if 'subject' in s:return BLUE
    if 'adverbial' in s or 'modifier' in s:return TEAL
    if any(x in s for x in ['predicate','verb','inversion','action','imperative','structure']):return RED
    return TEAL
for e in entries:
    for n in e['diagram']:n['role']=role(n['role'])
assert entries and len({e['id'] for e in entries})==TOTAL

def style(size=10.5,leading=None,font='CN',color=INK,align=TA_LEFT):
    return ParagraphStyle('x',fontName=font,fontSize=size,leading=leading or size*1.43,textColor=hc(color),spaceAfter=0,wordWrap='CJK' if font.startswith('CN') else None,alignment=align,allowWidows=0,allowOrphans=0)
def para(c,text,x,top,width,size=10.5,color=INK,font='CN',leading=None,align=TA_LEFT):
    p=Paragraph(text,style(size,leading,font,color,align));pw,ph=p.wrap(width,2000)
    if c:p.drawOn(c,x,H-top-ph)
    return ph
def rect(c,x,top,w,h,fill,stroke=None,r=0):
    c.setFillColor(hc(fill));c.setStrokeColor(hc(stroke or fill))
    if r:c.roundRect(x,H-top-h,w,h,r,fill=1,stroke=bool(stroke))
    else:c.rect(x,H-top-h,w,h,fill=1,stroke=bool(stroke))
def line(c,x1,y1,x2,y2,color=BORDER,lw=1):
    c.setStrokeColor(hc(color));c.setLineWidth(lw);c.line(x1,H-y1,x2,H-y2)
def arrow(c,x1,y1,x2,y2,col=TEAL,lw=1.5):
    line(c,x1,y1,x2,y2,col,lw);angle=math.atan2(y2-y1,x2-x1)
    for d in [-.6,.6]:line(c,x2,y2,x2-6*math.cos(angle+d),y2-6*math.sin(angle+d),col,lw)
def label(c,s,x,top,size=10,color=MUTED,font='CNB'):
    return para(c,E(s),x,top,CW,size,color,font)
def keyword(e):
    if e.get('keyword'):return e['keyword']
    s=re.split(r'[：:,，]',e['vocabulary'][0],maxsplit=1)[0].strip()
    s=re.split(r'[\u4e00-\u9fff]',s,maxsplit=1)[0].strip()
    return re.sub(r'\s+',' ',s)
def highlighted(e):
    s=e['english'];taken=[]
    for node in sorted(e['diagram'],key=lambda n:len(n['text']),reverse=True):
        phrase=node['text'];i=s.find(phrase)
        if i>=0 and not any(i<b and i+len(phrase)>a for a,b,_ in taken):taken.append((i,i+len(phrase),color_for(node['role'])))
    chunks=[];i=0
    for a,b,col in sorted(taken):chunks.extend([E(s[i:a]),f'<font color="{col}">{E(s[a:b])}</font>']);i=b
    chunks.append(E(s[i:]));return ''.join(chunks)

# Vector scene primitives are shared by PDF and offline HTML.
def scene(kind):
    if isinstance(kind,dict):return [(v['type'],tuple(v['args'])) for v in kind['primitives']]
    z=[]
    def L(x1,y1,x2,y2,col=BLUE,w=3):z.append(('line',(x1,y1,x2,y2,col,w)))
    def R(x,y,w,h,fill,stroke=INK,r=8):z.append(('rect',(x,y,w,h,fill,stroke,r)))
    def C(x,y,r,fill,stroke=INK):z.append(('circle',(x,y,r,fill,stroke)))
    def T(x,y,s,col=INK,size=14):z.append(('text',(x,y,s,col,size)))
    def A(x1,y1,x2,y2,col=TEAL):
        L(x1,y1,x2,y2,col,2);a=math.atan2(y2-y1,x2-x1)
        for d in [-.55,.55]:L(x2,y2,x2-8*math.cos(a+d),y2-8*math.sin(a+d),col,2)
    if kind=='reading':
        for x,s,col in [(79,'READ',BLUE),(240,'PARSE',RED),(402,'RECALL',TEAL)]:
            R(x-55,27,110,100,'#FFFFFF',col,9);L(x-36,58,x+32,58,col,2);L(x-36,75,x+32,75,col,2);T(x,97,s,col,12)
        A(140,75,178,75);A(300,75,340,75)
    elif kind=='boundary':
        R(30,22,145,105,'#EAF1FD',BLUE);C(65,52,10,BLUE,BLUE);C(106,92,10,BLUE,BLUE);C(138,61,10,BLUE,BLUE);T(102,151,'finite  有边界',BLUE);A(195,75,247,75)
        for t in range(61):
            a=t*2*math.pi/60;b=(t+1)*2*math.pi/60
            L(344+70*math.cos(a)/(1+math.sin(a)**2),75+70*math.sin(a)*math.cos(a)/(1+math.sin(a)**2),344+70*math.cos(b)/(1+math.sin(b)**2),75+70*math.sin(b)*math.cos(b)/(1+math.sin(b)**2),TEAL,4)
        T(344,151,'infinite  无尽',TEAL)
    elif kind=='hurdle':
        L(20,113,460,113,INK,2);C(67,45,11,BLUE,BLUE);L(67,57,67,87);L(67,64,48,80);L(67,65,88,67);L(67,86,51,112);L(67,86,85,108)
        R(175,53,19,60,'#FFF0CF',AMBER,3);R(284,23,19,90,'#FAE4E0',RED,3);A(104,79,153,79);A(208,79,261,79);T(175,148,'restrict',AMBER);T(295,148,'obstruct',RED);T(402,85,'前进',TEAL);A(329,78,459,78)
    elif kind=='choices':
        for x,title,sub,col in [(79,'观点','oppose',BLUE),(240,'事实','deny',RED),(402,'请求','refuse',PURPLE)]:
            R(x-57,26,114,65,'#FFFFFF',col);T(x,44,title,col,16);T(x,70,sub,col,14);L(x-12,112,x+12,135,col,4);L(x+12,112,x-12,135,col,4)
    elif kind=='growth':
        L(35,128,451,128,INK,2);L(35,128,35,15,INK,2)
        pts=[(70,108),(231,55),(413,30)]
        for a,b in zip(pts,pts[1:]):L(*a,*b,BLUE,4)
        for x,y in pts:C(x,y,5,BLUE,BLUE)
        for x,y,s in [(70,86,'100'),(231,30,'110'),(413,5,'115')]:T(x,y,s,BLUE,14)
        T(148,92,'+10',TEAL);T(321,103,'+5',AMBER);T(242,151,'总量向上  增长速度放慢',INK)
    elif kind=='family':
        C(241,43,18,BLUE,BLUE);T(241,0,'ancestor',BLUE,12);L(241,61,241,84,TEAL,2);L(95,84,385,84,TEAL,2)
        for x in [95,241,385]:L(x,84,x,100,TEAL,2);C(x,115,16,'#E8F3EF',TEAL)
        T(241,151,'descendants / offspring',TEAL);T(80,36,'ancestry',PURPLE,14)
    elif kind=='pressure':
        for cx,p,col in [(123,30,RED),(352,-35,TEAL)]:
            C(cx,72,53,'#FFFFFF',col);L(cx,72,cx+38*math.sin(p*math.pi/180),72-38*math.cos(p*math.pi/180),col,4);C(cx,72,5,col,col)
        A(192,72,283,72);T(123,148,'压力较大',RED);T(352,148,'有所缓解',TEAL)
    elif kind=='fade':
        for x,col in [(76,'#7446A7'),(231,'#BCA5D6'),(388,'#E5DDEE')]:C(x,70,44,col,col)
        A(131,70,173,70);A(287,70,330,70);T(240,148,'fade  逐渐褪色或减弱',PURPLE)
    elif kind=='hourglass':
        L(45,20,150,20,BLUE,5);L(45,135,150,135,BLUE,5);L(58,22,135,134,BLUE,2);L(135,22,58,134,BLUE,2);L(70,43,124,43,AMBER,9);L(70,118,125,118,AMBER,13)
        A(175,76,240,76);R(280,27,145,97,'#FFFFFF',RED,4);L(280,50,425,50,RED,2);T(352,68,'DEADLINE',RED,16);T(352,99,'截止时点',RED,14);T(98,157,'时间流逝',BLUE,12)
    elif kind=='traffic':
        for x,col,s in [(74,AMBER,'pause'),(239,BLUE,'suspend'),(406,RED,'terminate')]:
            C(x,63,36,col,col)
            if s in ['pause','suspend']:R(x-12,44,8,36,'#FFFFFF','#FFFFFF',1);R(x+4,44,8,36,'#FFFFFF','#FFFFFF',1)
            else:R(x-16,47,32,32,'#FFFFFF','#FFFFFF',2)
            T(x,122,s,col,15)
        T(239,154,'停一下  暂停安排  结束约定',INK,13)
    elif kind=='filter':
        for x,y in [(53,35),(95,35),(53,76),(95,76)]:R(x,y,22,22,'#EAF1FD',BLUE,2)
        L(159,23,310,23,TEAL,3);L(159,23,218,105,TEAL,3);L(310,23,250,105,TEAL,3);L(218,105,218,127,TEAL,3);L(250,105,250,127,TEAL,3);A(123, sixty:=65,169,65)
        A(320,65,370,65,RED);L(392,49,420,81,RED,4);L(420,49,392,81,RED,4);T(240,150,'exclude  不纳入范围',TEAL)
    elif kind=='magnifier':
        C(143,65,45,'#F0EDFA',PURPLE);L(175,99,208,134,PURPLE,10);C(143,65,3,INK,INK);T(353,43,'negligible',PURPLE,20);T(353,79,'小到可以忽略',INK,15);T(277,149,'≠ negligent  疏忽失职',RED,14)
    return z
def draw_scene(c,kind,x,top,w):
    scale=w/480
    for typ,args in scene(kind):
        if typ=='line':
            a,b,d,e,col,lw=args;line(c,x+a*scale,top+b*scale,x+d*scale,top+e*scale,col,lw*scale)
        elif typ=='rect':
            a,b,d,e,f,s,r=args;rect(c,x+a*scale,top+b*scale,d*scale,e*scale,f,s,r*scale)
        elif typ=='circle':
            a,b,r,f,s=args;c.setFillColor(hc(f));c.setStrokeColor(hc(s));c.setLineWidth(1.7*scale);c.circle(x+a*scale,H-top-b*scale,r*scale,fill=1,stroke=1)
        else:
            a,b,t,col,sz=args;para(c,E(t),x+(a-145)*scale,top+b*scale,290*scale,sz*scale,col,'CN',align=TA_CENTER)
def scene_svg(kind):
    a=['<svg class="scene" viewBox="0 0 480 180" role="img" aria-label="词义记忆图">']
    for typ,args in scene(kind):
        if typ=='line':
            x,y,x2,y2,col,w=args;a.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>')
        elif typ=='rect':
            x,y,w,h,f,s,r=args;a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{f}" stroke="{s}" stroke-width="1.7"/>')
        elif typ=='circle':
            x,y,r,f,s=args;a.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{f}" stroke="{s}" stroke-width="1.7"/>')
        else:
            x,y,t,col,sz=args;a.append(f'<text x="{x}" y="{y+sz}" text-anchor="middle" fill="{col}" font-size="{sz}">{E(t)}</text>')
    return ''.join(a)+'</svg>'


from atlas_layout import render_atlas
render_atlas(book,args,globals())
