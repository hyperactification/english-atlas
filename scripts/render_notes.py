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

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description="Render reviewed English sentence notes as a color PDF and an offline interactive HTML file.")
parser.add_argument('--input',required=True,type=Path)
parser.add_argument('--output-dir',required=True,type=Path)
parser.add_argument('--qa-dir',type=Path)
parser.add_argument('--basename')
parser.add_argument('--font-cn',type=Path)
parser.add_argument('--font-cn-bold',type=Path)
args=parser.parse_args()
book=json.loads(args.input.read_text(encoding='utf-8-sig'))
meta=book['meta'];entries=copy.deepcopy(book['entries']);groups=copy.deepcopy(book['groups'])
TOTAL=len(entries);CHAPTER=meta.get('chapter','English Study Notes');TITLE=meta['title']
GLOSSARY=[(g['term'],g['translation'],g['explanation'],'  '.join(str(i) for i in g['examples'])) for g in book['glossary']]
OUT=args.output_dir.resolve();OUT.mkdir(parents=True,exist_ok=True)
QA=(args.qa_dir or args.input.resolve().parent/'qa').resolve();QA.mkdir(parents=True,exist_ok=True)
BASENAME=re.sub(r'[<>:"/\\|?*]','_',args.basename or TITLE).strip(' .')
if not BASENAME:raise ValueError('A non-empty output basename is required')
fontroot=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
cn=args.font_cn or fontroot/'msyh.ttc';cnb=args.font_cn_bold or fontroot/'msyhbd.ttc'
if not cn.is_file():raise SystemExit('CJK TrueType font missing; pass --font-cn and --font-cn-bold. On Windows use Microsoft YaHei.')
if not cnb.is_file():cnb=cn
pdfmetrics.registerFont(TTFont('CN',str(cn),subfontIndex=0))
pdfmetrics.registerFont(TTFont('CNB',str(cnb),subfontIndex=0))
pdfmetrics.registerFontFamily('CN',normal='CN',bold='CNB',italic='CN',boldItalic='CNB')
en=fontroot/'arial.ttf';enb=fontroot/'arialbd.ttf'
if not en.is_file():en=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf');enb=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
if not en.is_file():en=cn;enb=cnb
pdfmetrics.registerFont(TTFont('EN',str(en),subfontIndex=0))
pdfmetrics.registerFont(TTFont('ENB',str(enb),subfontIndex=0))
pdfmetrics.registerFontFamily('EN',normal='EN',bold='ENB',italic='EN',boldItalic='ENB')
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
    if any(x in s for x in ['predicate','verb','inversion','action','imperative','structure']):return RED
    return TEAL
for e in entries:
    for n in e['diagram']:n['role']=role(n['role'])
assert entries and len({e['id'] for e in entries})==TOTAL
for e in entries:
    assert all(e.get(k) for k in ['translation','structure','vocabulary','exam_points','pitfalls','diagram','memory_tip'])
    for k in ['structure','vocabulary','exam_points','pitfalls']:
        e[k]=[english_terms(s) for s in e[k]]
    e['source_note']=english_terms(e['source_note']);e['memory_tip']=english_terms(e['memory_tip'])
    assert not any(re.search('[\u4e00-\u9fff]',n['role']) for n in e['diagram']),e['id']
(QA/'rendered_content.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')

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

PDF=OUT/(BASENAME+'.pdf')
c=canvas.Canvas(str(PDF),pagesize=(W,H),pageCompression=1)
c.setTitle(TITLE);c.setAuthor('Study Notes')
page_no=0;note_pages={};group_pages={};layout=[]
def newpage(section,bookmark=None):
    global page_no
    if page_no:c.showPage()
    page_no+=1;rect(c,0,0,W,H,PAPER)
    if bookmark:c.bookmarkPage(bookmark)
    label(c,CHAPTER+' / SENTENCE NOTEBOOK',M,18,8,MUTED,'CNB')
    para(c,E(section),W-270,18,230,8,MUTED,align=2)
    line(c,M,H-35,W-M,H-35)
    label(c,'学习顺序  看图 → 拆句 → 翻译 → 自测',M,H-25,7.5,MUTED)
    para(c,str(page_no),W-M-38,H-27,38,9,MUTED,'EN',align=2)

def blocks(c,blocks,x,top,width,size=10.5):
    y=top
    for title,lines,col in blocks:
        if not lines:continue
        if c:label(c,title,x,y,11,col,'ENB' if re.fullmatch('[A-Za-z ]+',title) else 'CNB')
        y+=19
        for s in lines:
            a,b=(s.split('：',1)+[''])[:2] if '：' in s else ('','')
            content=(f'<b>{E(a)}</b>：{E(b)}' if a and len(a)<55 else E(s))
            ph=para(c,content,x,y,width,size,leading=14)
            y+=ph+4
        y+=6
    return y-top

newpage('使用指南','cover')
label(c,CHAPTER,M,65,15,BLUE)
para(c,f'{TOTAL}句彩色图解<br/>学霸笔记',M,102,CW,31,INK,'CNB',leading=43)
para(c,'完整译文  ·  English grammar  ·  中文详解<br/>箭头拆句  ·  易混词地图  ·  中英术语表',M,210,CW,13,MUTED,leading=24)
draw_scene(c,book.get('cover_illustration','reading'),M,286,CW)
rect(c,M,507,CW,99,'#EDF3FC',r=12)
for x,n,t in [(M+21,str(TOTAL),'原句逐一精读'),(M+191,str(len(groups)),'词义记忆地图'),(M+355,str(len(GLOSSARY)),'术语集中对照')]:
    label(c,n,x,521,26,BLUE,'ENB');label(c,t,x,560,10,INK)
para(c,'先抓结构，再看词义。每句保留完整英文，附中文译文、Sentence structure、Vocabulary、Exam focus 和 Pitfalls；容易混淆的表达另给记忆提示。',M,632,CW,11.5)
para(c,E(SOURCE_LINE+'原括注释义整合进词汇讲解；原句用法问题在对应页说明。图示中的类比用于记忆，示意数字不代表现实数据。'),M,715,CW,9,MUTED)

newpage('阅读导航','contents');c.addOutlineEntry('阅读导航','contents',0,False)
label(c,'一眼看懂  怎么用这本笔记',M,50,21,INK)
para(c,'正文的 grammar 术语统一用 English；末尾 Grammar Glossary 集中提供中英对照与例句索引。中文说明保留，方便理解与复习。',M,93,CW,11)
y=151
for col,en,cn in [(BLUE,'Subject','谁或什么'),(RED,'Predicate','做什么或处于何种状态'),(PURPLE,'Object / Complement','动作涉及谁  或补充什么'),(TEAL,'Modifier / Adverbial','何时  为何  在什么条件下')]:
    rect(c,M,y+1,9,13,col,r=3);label(c,en,M+20,y,10,col,'ENB');label(c,cn,M+208,y,10,INK);y+=29
para(c,'颜色与箭头帮助定位结构；图解会节选或压缩较长成分，完整形式以原句和 Sentence structure 为准。先理解每格标签，再沿箭头阅读。',M,y+4,CW,9.5,MUTED)
y+=65
for g in groups:
    if y>700:
        newpage('阅读导航  续页');y=60
    a,b=g['range'];line(c,M,y-7,W-M,y-7)
    label(c,f'{g["no"]:02d}',M,y,11,BLUE,'ENB');label(c,g['title'],M+38,y,11,INK)
    para(c,f'{a:03d} - {b:03d}',W-M-84,y,84,10,MUTED,'EN',align=2)
    c.linkRect('',f'group{g["no"]}',(M,H-y-22,W-M,H-y+5),relative=0,thickness=0)
    y+=31
para(c,'建议复习：先遮住译文独立翻译 → 对照箭头恢复句子结构 → 记搭配与易错点 → 第二天只看英文再译一次。离线网页版提供译文自测开关和全文检索。',M,746,CW,9.5,TEAL)

for g in groups:
    a,b=g['range'];newpage(f'词义地图 {g["no"]:02d}',f'group{g["no"]}');group_pages[g['no']]=page_no
    c.addOutlineEntry(f'{g["no"]:02d} {g["title"]}  {a}-{b}',f'group{g["no"]}',0,False)
    label(c,f'WORD MAP {g["no"]:02d}   /   {a:03d} - {b:03d}',M,52,10,BLUE,'ENB')
    label(c,g['title'],M,78,23,INK)
    para(c,E(g['subtitle']),M,116,CW,11,MUTED)
    draw_scene(c,g.get('illustration',g.get('icon','reading')),M+10,155,CW-20)
    y=352;nw=(CW-20)/3
    for j,(title,words,explain) in enumerate(g['nodes']):
        x=M+j*(nw+10);col=[BLUE,RED,TEAL][j]
        rect(c,x,y,nw,80,['#EDF3FC','#FBEEEB','#EAF5F0'][j],r=9)
        para(c,E(title),x+10,y+8,nw-20,11,col,'CNB');para(c,E(words),x+10,y+28,nw-20,10.5,col,'ENB');para(c,E(explain),x+10,y+54,nw-20,9,INK)
    y=459
    for words,meaning,usage in g['rows']:
        ph1=para(c,f'<b>{E(words)}</b>',M,y,185,10.5,BLUE)
        ph2=para(c,f'<b>{E(english_terms(meaning))}</b><br/>{E(english_terms(usage))}',M+198,y,CW-198,10.2)
        y+=max(ph1,ph2)+13;line(c,M,y-6,W-M,y-6)
    y+=7
    y+=para(c,'<b>Grammar cue</b>  '+txt(g['focus']),M,y,CW,10.4,TEAL)+12
    ph=para(c,'<b>辨析提醒</b>  '+txt(g['warning']),M,y,CW,10,AMBER)
    if y+ph>H-48:raise ValueError(('map overflow',g['no'],y+ph))
    for e in [v for v in entries if a<=v['id']<=b]:
        newpage(f'原练习第{e["page"]}页  /  句 {e["id"]:03d}',f's{e["id"]}');note_pages[e['id']]=page_no
        c.addOutlineEntry(f'{e["id"]:03d} {keyword(e)}',f's{e["id"]}',1,False)
        label(c,f'{e["id"]:03d}',M,45,25,BLUE,'ENB')
        para(c,E(keyword(e)),M+62,51,CW-62,17,INK,'ENB')
        y=89;label(c,'ORIGINAL',M,y,8,MUTED,'ENB');y+=16
        y+=para(c,highlighted(e),M,y,CW,14,INK,'EN',leading=19)+13
        label(c,'参考译文',M,y,9,TEAL);y+=17
        y+=para(c,E(e['translation']),M,y,CW,11.5,INK,leading=17)+18
        # Each block carries its own accurate grammar/semantic role.
        nodes=e['diagram'];gap=16;nw=(CW-gap*(len(nodes)-1))/len(nodes)
        heights=[]
        for n in nodes:
            roleh=para(None,E(n['role']),0,0,nw-15,8.3,MUTED,'ENB',leading=10.5)
            texth=para(None,E(n['text']),0,0,nw-15,10.3,INK,'EN',leading=13.3)
            heights.append(11+roleh+7+texth+10)
        dh=max(72,max(heights))
        for j,n in enumerate(nodes):
            x=M+j*(nw+gap);col=color_for(n['role']);rect(c,x,y,nw,dh,'#FFFFFF',BORDER,7);rect(c,x,y,nw,3,col)
            rh=para(c,E(n['role']),x+8,y+10,nw-16,8.3,col,'ENB',leading=10.5)
            para(c,E(n['text']),x+8,y+17+rh,nw-16,10.3,INK,'EN',leading=13.3)
            if j<len(nodes)-1:arrow(c,x+nw+3,y+dh/2,x+nw+gap-3,y+dh/2,MUTED,1.2)
        y+=dh+23
        left=[('Sentence structure',e['structure'],BLUE),('Vocabulary',e['vocabulary'],TEAL)]
        right=[('Exam focus',e['exam_points'],PURPLE),('Pitfalls',e['pitfalls'],RED),('原句表达提示',[e['source_note']] if e['source_note'] else [],AMBER)]
        colw=(CW-25)/2
        lh=blocks(None,left,M,y,colw);rh=blocks(None,right,M+colw+25,y,colw)
        available=H-105-y
        if max(lh,rh)>available:
            # A dense entry uses a continuation page, never a smaller font.
            para(c,'详细解析续见下一页。',M,y,CW,11,TEAL)
            newpage(f"句 {e['id']:03d}  详解续页")
            label(c,f"{e['id']:03d}  "+keyword(e),M,54,18,BLUE)
            yy=103
            for title,lines,col in left+right:
                if not lines:continue
                if yy+68>H-105:
                    newpage(f"句 {e['id']:03d}  详解续页");yy=70
                label(c,title,M,yy,12,col);yy+=24
                for s in lines:
                    paragraph=Paragraph(E(s),style(11,16))
                    pending=[paragraph]
                    while pending:
                        p=pending.pop(0);_,ph=p.wrap(CW,H-105-yy)
                        if ph>H-105-yy:
                            split=p.split(CW,H-105-yy)
                            if not split:
                                newpage(f"句 {e['id']:03d}  详解续页");yy=70;pending.insert(0,p);continue
                            p=split[0];pending=split[1:]+pending;_,ph=p.wrap(CW,H-105-yy)
                        p.drawOn(c,M,H-yy-ph);yy+=ph+12
                        if pending:newpage(f"句 {e['id']:03d}  详解续页");yy=70
                yy+=7
        else:
            blocks(c,left,M,y,colw);blocks(c,right,M+colw+25,y,colw)
        my=H-85;rect(c,M,my,CW,43,'#EEF5F2',r=6)
        mh=para(c,'<b>记忆钩子</b>  '+E(e['memory_tip']),M+10,my+7,CW-20,9.6,TEAL,leading=13)
        if mh>32:raise ValueError(('tip overflow',e['id'],mh))
        layout.append({'id':e['id'],'page':note_pages[e['id']],'body_start':round(y,1),'left_height':round(lh,1),'right_height':round(rh,1),'available':round(available,1)})

for k in range(0,len(GLOSSARY),8):
    newpage('Grammar Glossary  语法术语中英对照',f'glossary{k//8+1}')
    if k==0:c.addOutlineEntry('Grammar Glossary  语法术语中英对照','glossary1',0,False)
    label(c,'Grammar Glossary',M,53,24,INK,'ENB');label(c,'语法术语中英对照',M,91,14,BLUE)
    para(c,'英文术语 → 中文名称 → 简单解释 → 对应例句。例句编号与正文左上角编号一致。',M,122,CW,10,MUTED)
    y=163;xs=[M,M+124,M+214,M+462];widths=[124,90,248,CW-462]
    rect(c,M,y,CW,30,INK)
    for x,w,s in zip(xs,widths,['English','中文名称','怎么理解','例句']):para(c,E(s),x+7,y+8,w-14,9,'#FFFFFF','CNB')
    y+=30
    for i,(en,cn,meaning,ids) in enumerate(GLOSSARY[k:k+8]):
        vals=[en,cn,meaning,ids.replace('  ','\n')]
        sizes=[10,10,10,9];fonts=['ENB','CNB','CN','EN']
        rh=max(para(None,E(v).replace('\n','<br/>'),0,0,w-14,sz,INK,fo) for v,w,sz,fo in zip(vals,widths,sizes,fonts))+22
        rect(c,M,y,CW,rh,'#FFFFFF' if i%2==0 else '#F0F4F8',BORDER)
        for x,w,v,sz,fo in zip(xs,widths,vals,sizes,fonts):
            line(c,x,y,x,y+rh);para(c,E(v).replace('\n','<br/>'),x+7,y+11,w-14,sz,INK,fo)
        for id in re.findall(r'\d+',ids)[:1]:c.linkRect('',f's{int(id)}',(xs[-1],H-y-rh,W-M,H-y),relative=0,thickness=0)
        y+=rh
    if y>H-48:raise ValueError(('glossary overflow',k,y))

newpage('复习路线','review');c.addOutlineEntry('复习路线','review',0,False)
label(c,'把看懂  变成自己会用',M,54,24,INK)
review=book.get('review',[
('第1轮  找 sentence core','先找 Subject 与 Predicate，再恢复 Object、Complement、Modifier 和 Adverbial。确认每一部分与谁关联。'),
('第2轮  检查词义与搭配','结合本句选择词义，再检查动词后面接什么结构。不要把近义词当成可以在所有语境里任意替换。'),
('第3轮  守住意思的边界','检查条件、否定、范围和语气。区分可能与必然、目的与结果、时间先后与因果关系。'),
('第4轮  对照词义地图','把容易混淆的词放在同一张图里比较，记住搭配对象和适用语境。'),
('第5轮  遮译文自测','只看英文先写译文，核对结构和关键词；将错因记下，隔天再翻译一次。')])
y=125
for i,(title,body) in enumerate(review):
    rect(c,M,y,30,30,[BLUE,TEAL,PURPLE,RED,AMBER][i],r=8);para(c,str(i+1),M,y+5,30,15,'#FFFFFF','ENB',align=TA_CENTER)
    label(c,title,M+45,y,13,INK);ph=para(c,E(body),M+45,y+29,CW-45,11);y+=max(92,ph+57)
para(c,'这套材料是句子翻译与词汇用法练习。复习时要同时检查词义、结构和语气限定；真实世界的事实判断还需要相应领域的证据。',M,739,CW,10,MUTED)
c.save()
(QA/'layout_report.json').write_text(json.dumps({'pages':page_no,'sentences':TOTAL,'glossary_terms':len(GLOSSARY),'note_pages':note_pages,'group_pages':group_pages,'layout':layout},ensure_ascii=False,indent=2),encoding='utf-8')

# A self-contained companion: no remote fonts, images, scripts or network requests.
CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f2f4f5;color:#17263c;font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.75}button,input{font:inherit}button{cursor:pointer}.toolbar{position:sticky;top:0;z-index:10;background:#17263cf2;color:white;padding:14px 24px;display:flex;gap:14px;align-items:center;box-shadow:0 4px 16px #10203022}.toolbar strong{white-space:nowrap}.toolbar input{width:min(36vw,420px);padding:8px 12px;border:0;border-radius:7px}.toolbar button,.toolbar a{padding:7px 12px;border:1px solid #718096;border-radius:7px;background:transparent;color:white;text-decoration:none;font-size:13px}.layout{max-width:1400px;margin:auto;display:grid;grid-template-columns:250px 1fr;gap:28px;padding:28px}nav{position:sticky;top:102px;height:calc(100vh - 125px);overflow:auto}nav a{display:block;color:#334155;text-decoration:none;padding:8px 10px;border-radius:6px;font-size:13px}nav a:hover{background:#e1eaf8;color:#2457bd}main{min-width:0}.cover,.map,.note,.glossary,.review{background:#fcfcf9;border:1px solid #dfe5e8;border-radius:14px;padding:34px;margin:0 0 28px;scroll-margin-top:95px;box-shadow:0 6px 24px #16263706}.eyebrow{font-size:12px;letter-spacing:.12em;color:#2457bd;font-weight:700}h1{font-size:38px;line-height:1.35;letter-spacing:.03em}h2{font-size:25px;line-height:1.4}h3{font-size:15px}.muted{color:#64748b}.stats{display:flex;gap:40px;padding:16px 0}.stats b{font-size:30px;color:#2457bd}.legend{display:flex;flex-wrap:wrap;gap:10px}.legend span{font-size:12px;padding:3px 8px;border-radius:5px;background:white;border:1px solid currentColor}.scene{display:block;width:min(100%,560px);margin:25px auto;font-family:"Microsoft YaHei",Arial,sans-serif}.mapnodes{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}.mapnodes div{background:#edf3fc;border-radius:10px;padding:15px}.mapnodes div:nth-child(2){background:#fbeeea}.mapnodes div:nth-child(3){background:#eaf5f0}.mapnodes strong,.mapnodes span{display:block}.map table,.glossary table{width:100%;border-collapse:collapse;font-size:14px;margin:24px 0}.map td,.glossary td,.glossary th{padding:12px;vertical-align:top;border:1px solid #d9dfe5}.glossary th{background:#17263c;color:white;text-align:left}.glossary tr:nth-child(even){background:#f0f4f8}.glossary a{color:#2457bd}.cue{padding:12px 0;color:#167361}.warning{color:#945b09}.notehead{display:flex;align-items:baseline;gap:18px}.num{font-size:32px;color:#2457bd;font-weight:bold}.source{margin-left:auto;font-size:12px;color:#64748b;white-space:nowrap}.original{font-family:Arial,sans-serif;font-size:21px;line-height:1.6;margin:15px 0}.original font{font-weight:500}.translation{font-size:17px;border-left:3px solid #167361;padding-left:13px;margin:16px 0 26px}.diagram{display:flex;gap:18px;align-items:stretch;margin:28px 0}.node{position:relative;flex:1;min-width:0;background:white;border:1px solid #dde4ea;border-top:4px solid var(--c);border-radius:6px;padding:10px;font-family:Arial,sans-serif}.node small{display:block;font-size:12px;color:var(--c);font-weight:700;line-height:1.4;margin-bottom:8px}.node p{font-size:15px;line-height:1.45;margin:0;overflow-wrap:anywhere}.node:not(:last-child):after{content:'→';position:absolute;right:-18px;top:40%;color:#64748b}.columns{display:grid;grid-template-columns:1fr 1fr;gap:26px}.block h3{margin:18px 0 9px;color:var(--c)}.block p{font-size:14px;line-height:1.85;margin:8px 0 12px}.tip{background:#eaf4ee;color:#167361;padding:12px 16px;border-radius:7px;font-size:14px;margin-top:20px}.selftest .translation{filter:blur(6px);cursor:pointer;user-select:none}.selftest .translation.revealed{filter:none;user-select:text}.empty{display:none;padding:30px;background:white;border-radius:10px}.note[hidden],.map[hidden]{display:none}#result{font-size:12px;color:#c4d4eb}.showone{font-size:12px;color:#167361;border:0;background:transparent;display:none}.selftest .showone{display:inline-block}.toplink{float:right;font-size:12px;color:#64748b}@media(max-width:900px){.layout{grid-template-columns:1fr;padding:14px}.layout nav{display:none}.toolbar{flex-wrap:wrap;padding:10px 14px;gap:8px}.toolbar input{width:100%;order:3}.cover,.map,.note,.glossary,.review{padding:20px}h1{font-size:29px}.source{white-space:normal}.columns{grid-template-columns:1fr;gap:0}.diagram{gap:13px}.node{padding:7px}.node p{font-size:13px}.node small{font-size:10px}.node:not(:last-child):after{right:-13px}.mapnodes{grid-template-columns:1fr}.glossary{overflow:auto}.original{font-size:19px}}@media print{.toolbar,nav,.toplink,.showone{display:none}.layout{display:block;padding:0}.cover,.map,.note,.glossary,.review{box-shadow:none;border:0;border-radius:0;break-before:page;margin:0}.selftest .translation{filter:none}.note[hidden],.map[hidden]{display:block}.columns{grid-template-columns:1fr 1fr}.diagram{break-inside:avoid}}'''
CSS=CSS.replace('scroll-behavior:smooth','scroll-behavior:auto').replace('background:#17263cf2','background:#17263c')+'@media(max-width:900px){.note,.map,.glossary,.cover,.review{scroll-margin-top:178px}}'
CSS+='@media(max-width:600px){.diagram{flex-direction:column;gap:22px}.node{padding:12px}.node p{font-size:15px;overflow-wrap:normal;word-break:normal}.node small{font-size:12px}.node:not(:last-child):after{content:"↓";right:auto;left:50%;top:auto;bottom:-24px}.notehead{flex-wrap:wrap;gap:8px 14px}.notehead h2{overflow-wrap:anywhere}.source{margin-left:0;width:100%}}'
parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>@@TITLE@@</title><style>'+CSS+'</style><body id="top"><div class="toolbar"><strong>@@CHAPTER@@</strong><input id="search" type="search" placeholder="搜索原句编号、词汇或考点" aria-label="搜索笔记"><button id="test" aria-pressed="false">开启译文自测</button><button id="reset">重置</button><a href="#glossary">中英术语表</a><span id="result">@@TOTAL@@ 句</span></div><div class="layout"><nav aria-label="章节导航"><a href="#top">阅读指南</a>']
for g in groups:parts.append(f'<a href="#g{g["no"]}">{g["no"]:02d} {E(g["title"])}<br><small>{g["range"][0]} - {g["range"][1]}</small></a>')
parts.append('<a href="#glossary">Grammar Glossary</a></nav><main><section class="cover"><div class="eyebrow">@@CHAPTER@@</div><h1>@@TOTAL@@句彩色图解<br>学霸笔记</h1><p class="muted">完整译文 · English grammar · 中文详解 · 箭头拆句 · 易混词地图</p><div class="stats"><span><b>@@TOTAL@@</b><br>逐句精读</span><span><b>@@GROUPS@@</b><br>词义地图</span><span><b>'+str(len(GLOSSARY))+'</b><br>术语对照</span></div><div class="legend">')
for col,en in [(BLUE,'Subject'),(RED,'Predicate'),(PURPLE,'Object / Complement'),(TEAL,'Modifier / Adverbial')]:parts.append(f'<span style="color:{col}">{en}</span>')
parts.append('</div><p>先看原句和彩色箭头，再读翻译、结构和词汇。正文 grammar 术语统一用 English，末尾术语表提供中英对照、解释和例句链接。点击“开启译文自测”即可遮住译文；点击单句译文可单独揭晓。</p><p class="muted">@@SOURCE@@原括注释义已整合到词汇讲解，表达建议单列。图解会节选较长结构，完整形式请对照原句。文件可离线使用。</p></section><p class="empty" id="empty">没有匹配的笔记，请换一个词或句号。</p>')
for g in groups:
    parts.append(f'<section class="map" id="g{g["no"]}"><div class="eyebrow">WORD MAP {g["no"]:02d} / {g["range"][0]} - {g["range"][1]}</div><h2>{E(g["title"])}</h2><p class="muted">{E(g["subtitle"])}</p>{scene_svg(g.get('illustration',g.get('icon','reading')))}<div class="mapnodes">')
    for title,words,ex in g['nodes']:parts.append(f'<div><strong>{E(title)}</strong><span>{E(words)}</span><small>{E(ex)}</small></div>')
    parts.append('</div><table><tbody>')
    for w,m,u in g['rows']:parts.append(f'<tr><td><b>{E(w)}</b></td><td>{txt(m)}</td><td>{txt(u)}</td></tr>')
    parts.append('</tbody></table><p class="cue"><b>Grammar cue</b> '+txt(g['focus'])+'</p><p class="warning"><b>辨析提醒</b> '+txt(g['warning'])+'</p></section>')
    for e in [v for v in entries if g['range'][0]<=v['id']<=g['range'][1]]:
        parts.append(f'<article class="note" id="s{e["id"]}" data-id="{e["id"]}"><div class="notehead"><span class="num">{e["id"]:03d}</span><h2>{E(keyword(e))}</h2><span class="source">原练习第{e["page"]}页</span></div><div class="original" lang="en">{highlighted(e)}</div><button class="showone">显示或隐藏本句译文</button><div class="translation">{E(e["translation"])}</div><div class="diagram">')
        for n in e['diagram']:parts.append(f'<div class="node" style="--c:{color_for(n["role"])}"><small>{E(n["role"])}</small><p lang="en">{E(n["text"])}</p></div>')
        parts.append('</div><div class="columns">')
        for column in [[('Sentence structure',e['structure'],BLUE),('Vocabulary',e['vocabulary'],TEAL)],[('Exam focus',e['exam_points'],PURPLE),('Pitfalls',e['pitfalls'],RED),('原句表达提示',[e['source_note']] if e['source_note'] else [],AMBER)]]:
            parts.append('<div>')
            for title,ls,col in column:
                if not ls:continue
                parts.append(f'<section class="block" style="--c:{col}"><h3>{E(title)}</h3>')
                parts.extend('<p>'+E(s)+'</p>' for s in ls);parts.append('</section>')
            parts.append('</div>')
        parts.append(f'</div><div class="tip"><b>记忆钩子</b> {E(e["memory_tip"])}</div><a class="toplink" href="#top">回到顶部 ↑</a></article>')
parts.append('<section class="glossary" id="glossary"><div class="eyebrow">ENGLISH / 中文</div><h2>Grammar Glossary</h2><p>术语集中中英对照。点击例句编号直接跳回相应笔记。</p><table><thead><tr><th>English</th><th>中文名称</th><th>怎么理解</th><th>例句</th></tr></thead><tbody>')
for en,cn,m,ids in GLOSSARY:
    links=' '.join(f'<a href="#s{int(i)}">{i}</a>' for i in re.findall(r'\d+',ids))
    parts.append(f'<tr><td><b>{E(en)}</b></td><td>{E(cn)}</td><td>{E(m)}</td><td>{links}</td></tr>')
parts.append('</tbody></table></section><section class="review"><h2>复习路线</h2>')
for title,body in review:parts.append(f'<h3>{E(title)}</h3><p>{E(body)}</p>')
parts.append(r'''</section></main></div><script>
const notes=[...document.querySelectorAll('.note')],maps=[...document.querySelectorAll('.map')],search=document.querySelector('#search'),test=document.querySelector('#test');
function filter(){let q=search.value.trim().toLowerCase(),n=0;for(const a of notes){let ok=!q||(/^\d+$/.test(q)?Number(a.dataset.id)===Number(q):a.textContent.toLowerCase().includes(q));a.hidden=!ok;if(ok)n++}maps.forEach(m=>m.hidden=!!q);document.querySelector('#result').textContent=q?n+' / '+notes.length+' 句':notes.length+' 句';document.querySelector('#empty').style.display=n?'none':'block'}
search.addEventListener('input',filter);test.addEventListener('click',()=>{let b=document.body.classList.toggle('selftest');test.setAttribute('aria-pressed',b);test.textContent=b?'退出译文自测':'开启译文自测';document.querySelectorAll('.translation').forEach(x=>x.classList.remove('revealed'))});
document.querySelector('#reset').addEventListener('click',()=>{search.value='';filter();document.body.classList.remove('selftest');test.textContent='开启译文自测';test.setAttribute('aria-pressed','false')});
notes.forEach(n=>{const t=n.querySelector('.translation');n.querySelector('.showone').addEventListener('click',()=>t.classList.toggle('revealed'));t.addEventListener('click',()=>{if(document.body.classList.contains('selftest'))t.classList.toggle('revealed')})});
document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>{if(search.value){search.value='';filter()}}));
</script></body></html>''')
HTML=OUT/(BASENAME+'.html')
markup=''.join(parts)
for token,value in {'@@TITLE@@':TITLE,'@@CHAPTER@@':CHAPTER,'@@TOTAL@@':str(TOTAL),'@@GROUPS@@':str(len(groups)),'@@SOURCE@@':SOURCE_LINE}.items():markup=markup.replace(token,E(value))
HTML.write_text(markup,encoding='utf-8')
(QA/'artifacts.json').write_text(json.dumps({'pdf':str(PDF),'html':str(HTML),'input':str(args.input.resolve())},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pdf':str(PDF),'html':str(HTML),'pages':page_no,'sentences':len(entries),'terms':len(GLOSSARY)},ensure_ascii=False))
