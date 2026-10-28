"""English Atlas v2: explicit reading hierarchy and structured lexical cards."""
from pathlib import Path
import copy,html,json,re
from reportlab.platypus import (BaseDocTemplate,PageTemplate,Frame,Flowable,
    Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from grammar_terms import english_terms

W,H=595.276,841.89
M=36;CW=W-2*M
INK='#18263D';BODY='#334155';MUTED='#64748B';LINE='#DDE4EF'
BLUE='#244BC1';PALE='#EEF3FF';TEAL='#146B58';AMBER='#8B5700';RED='#A42D38'

def esc(s):return html.escape(str(s),quote=False)
def color(s):return HexColor(s)
def style(size=10,leading=None,font='CN',ink=BODY):
    return ParagraphStyle('atlas',fontName=font,fontSize=size,leading=leading or size*1.42,
        textColor=color(ink),wordWrap='CJK' if font.startswith('CN') else None,
        spaceAfter=0,allowWidows=0,allowOrphans=0)
def para(text,size=10,font='CN',ink=BODY,markup=False):
    if font in ('CN','CNB') and re.search(r'[A-Za-z]',str(text)) and not re.search(r'[\u3400-\u9fff]',str(text)):
        font='ENB' if font=='CNB' else 'EN'
    return Paragraph(str(text) if markup else esc(text),style(size,font=font,ink=ink))
def pad(table,n=10):
    table.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),n),('RIGHTPADDING',(0,0),(-1,-1),n),
        ('TOPPADDING',(0,0),(-1,-1),n),('BOTTOMPADDING',(0,0),(-1,-1),n),('VALIGN',(0,0),(-1,-1),'TOP')]))
    return table
def box(title,items,width=CW,accent=BLUE,bg=PALE,numbered=False):
    rows=[[para(title,9.5,'CNB',accent)]]
    for i,item in enumerate(items):
        text=(f'<font color="{accent}"><b>{i+1:02d}</b></font>  ' if numbered else '')+esc(item)
        rows.append([para(text,10,markup=True)])
    t=pad(Table(rows,colWidths=[width],repeatRows=1),7)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),color(bg)),
        ('BOX',(0,0),(-1,-1),.6,color(LINE)),('LINEBEFORE',(0,0),(0,-1),2.5,color(accent)),
        ('BOTTOMPADDING',(0,0),(-1,0),5),('TOPPADDING',(0,1),(-1,-1),3)]))
    return t

def lexical_card(v,index,width=CW):
    if isinstance(v,str):return box(f'{index:02d}  Vocabulary',[v],width,BLUE,'#F7F9FE')
    rows=[[para(f'W{index:02d}  {v["term"]}',14,'CNB',INK)],
          [para(v['explanation'],10)]]
    synonyms=v['near_synonyms']
    if synonyms:
        data=[[para('NEAR SYNONYMS',8.1,'ENB',BLUE),para('差別 / 替換限制',8.4,'CNB',MUTED)]]
        for s in synonyms:
            data.append([para(s['text'],10.5,'CNB',BLUE),para(s['distinction'],9.7)])
        syn=pad(Table(data,colWidths=[(width-20)*.34,(width-20)*.66],repeatRows=1),4)
        syn.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),color(PALE)),
            ('LINEBELOW',(0,0),(-1,0),.5,color(LINE)),
            ('LINEBELOW',(0,1),(-1,-1),.35,color(LINE)),
            ('LEFTPADDING',(0,0),(0,-1),6)]))
        rows.append([syn])
    else:
        rows.append([para('NEAR SYNONYMS  /  '+v.get('no_synonym_reason',''),9.4,'CN',MUTED)])
    if synonyms and v.get('no_synonym_reason'):rows.append([para(v['no_synonym_reason'],9.4,'CN',MUTED)])
    card=pad(Table(rows,colWidths=[width],repeatRows=1),7)
    card.setStyle(TableStyle([('BOX',(0,0),(-1,-1),.7,color(LINE)),
        ('BACKGROUND',(0,0),(-1,0),color('#E8EEF9')),
        ('LINEBEFORE',(0,0),(0,0),3,color(BLUE)),
        ('TOPPADDING',(0,1),(-1,-1),4),('BOTTOMPADDING',(0,1),(-1,1),4),
        ('LEFTPADDING',(0,2),(-1,2),7),('RIGHTPADDING',(0,2),(-1,2),7)]))
    return KeepTogether([card,Spacer(1,7)])

class Marker(Flowable):
    def __init__(self,key,title,level=0,entry=None):
        Flowable.__init__(self);self.key=key;self.title=title;self.level=level;self.entry=entry;self.height=0;self.width=0
    def draw(self):
        c=self.canv;c._atlas_entry=self.entry;c._atlas_section=self.title
        c.bookmarkPage(self.key);c.addOutlineEntry(self.title,self.key,self.level,False)
        if self.entry:self.canv._atlas_note_pages[str(self.entry['id'])]=c.getPageNumber()
        elif self.key.startswith('g') and self.key[1:].isdigit():self.canv._atlas_group_pages[self.key[1:]]=c.getPageNumber()

class Scene(Flowable):
    def __init__(self,primitives,width=CW):
        Flowable.__init__(self);self.items=primitives;self.width=width;self.height=180*width/480
    def draw(self):
        c=self.canv;s=self.width/480;c.saveState();c.translate(0,self.height)
        for typ,a in self.items:
            if typ=='line':
                x,y,xx,yy,col,lw=a;c.setStrokeColor(color(col));c.setLineWidth(lw*s);c.line(x*s,-y*s,xx*s,-yy*s)
            elif typ=='rect':
                x,y,w,h,fill,stroke,r=a;c.setFillColor(color(fill));c.setStrokeColor(color(stroke));c.setLineWidth(s)
                c.roundRect(x*s,-(y+h)*s,w*s,h*s,r*s,stroke=1,fill=1)
            elif typ=='circle':
                x,y,r,fill,stroke=a;c.setFillColor(color(fill));c.setStrokeColor(color(stroke));c.setLineWidth(s);c.circle(x*s,-y*s,r*s,stroke=1,fill=1)
            else:
                x,y,text,col,sz=a;c.setFillColor(color(col));c.setFont('CN',sz*s);c.drawCentredString(x*s,-(y+sz*.9)*s,str(text))
        c.restoreState()

def diagram(entry,ctx,width=CW):
    nodes=entry['diagram'];n=len(nodes);gap=12;colw=(width-gap*(n-1))/n
    cells=[]
    for node in nodes:
        col=ctx['color_for'](node['role'])
        cell=pad(Table([[para(node['role'],8.2,'CNB',col)],[para(node['text'],9.5,'EN',INK)]],colWidths=[colw]),7)
        cell.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),color('#F7F9FD')),
            ('BOX',(0,0),(-1,-1),.5,color(LINE)),('LINEABOVE',(0,0),(-1,0),2,color(col)),
            ('TOPPADDING',(0,1),(-1,1),2)]))
        cells.append(cell)
    row=[];widths=[]
    for i,cell in enumerate(cells):
        row.append(cell);widths.append(colw)
        if i<n-1:row.append(para('→',10,'CNB',MUTED));widths.append(gap)
    t=Table([row],colWidths=widths);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    return t

def clean_entry(e,ctx):
    e=copy.deepcopy(e)
    for k in ['structure','exam_points','pitfalls']:e[k]=[english_terms(x) for x in e[k]]
    for k in ['memory_tip','source_note']:e[k]=english_terms(e.get(k,''))
    for node in e['diagram']:node['role']=ctx['role'](node['role'])
    for v in e['vocabulary']:
        if isinstance(v,dict):
            v['explanation']=english_terms(v['explanation'])
            for s in v['near_synonyms']:s['distinction']=english_terms(s['distinction'])
            if v.get('no_synonym_reason'):v['no_synonym_reason']=english_terms(v['no_synonym_reason'])
    return e

def render_atlas(book,args,ctx):
    out=ctx['OUT'];qa=ctx['QA'];base=ctx['BASENAME'];meta=book['meta']
    entries=[clean_entry(e,ctx) for e in book['entries']];groups=book['groups'];gloss=book['glossary']
    pdf=out/(base+'.pdf');html_file=out/(base+'.html')
    qa.joinpath('rendered_content.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    note_pages={};group_pages={};page_count=[0]
    def page_end(c,doc):
        page_count[0]=c.getPageNumber();c.saveState()
        e=getattr(c,'_atlas_entry',None)
        left=meta.get('chapter','English Atlas')
        right=(f'{e["id"]:03d}  {e["keyword"]}' if e else 'English Atlas / 精讀圖譜')
        c.setFont('CN',7.2);c.setFillColor(color(MUTED));c.drawString(M,H-16,left)
        c.drawRightString(W-M,H-16,right)
        if e and c.getPageNumber()>note_pages.get(str(e['id']),c.getPageNumber()):
            c.setFillColor(color(PALE));c.rect(M,H-39,CW,18,stroke=0,fill=1)
            c.setFillColor(color(BLUE));c.setFont('CNB',10)
            label=f'Q{e["id"]:03d}  {e["keyword"]}  /  精讀續頁'
            while c.stringWidth(label,'CNB',10)>CW-14 and len(label)>28:label=label[:-15]+'… / 精讀續頁'
            c.drawString(M+7,H-34,label)
        c.setStrokeColor(color(LINE));c.setLineWidth(.5);c.line(M,28,W-M,28)
        c.setFont('CN',7);c.drawString(M,16,'READ  /  DECODE  /  COMPARE  /  RECALL')
        c.drawRightString(W-M,16,str(c.getPageNumber()));c.restoreState()
    doc=BaseDocTemplate(str(pdf),pagesize=(W,H),leftMargin=M,rightMargin=M,topMargin=42,bottomMargin=39,
        title=meta['title'],author='English Atlas')
    frame=Frame(M,39,CW,H-81,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='body')
    doc.addPageTemplates(PageTemplate(id='atlas',frames=frame,onPageEnd=page_end))
    story=[]
    def add(*items):story.extend(items)
    # The same mapping is available to marker flowables on every page.
    class AtlasCanvas(ctx['canvas'].Canvas):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw);self._atlas_note_pages=note_pages;self._atlas_group_pages=group_pages
    add(Marker('cover','English Atlas'),Spacer(1,40),para('ENGLISH ATLAS',13,'ENB',BLUE),Spacer(1,14),
        para('英語精讀圖譜',31,'CNB',INK),Spacer(1,10),para(meta['chapter'],14,'CNB',MUTED),Spacer(1,22),
        box('READ FIRST  /  一眼找到需要的信息',[
            '原句與譯文在最上方；Sentence structure 與 Exam focus 分區閱讀。',
            'Vocabulary 每個詞條獨立成卡：先看本句義項，再對照近義表達與替換限制。',
            'Pitfalls 使用警示區；Grammar 角色顏色只用於原句與拆句圖。'],accent=BLUE),
        Spacer(1,15),Scene(ctx['scene'](book.get('cover_illustration','reading')),CW),Spacer(1,15),
        box('本冊內容',[f'{len(entries)} 題完整精讀  /  {len(groups)} 組詞義圖譜  /  {len(gloss)} 項 Grammar 對照',
            f'來源：{meta["source_name"]}，原文件 {meta["source_pages"]} 頁。原文用法疑點另列 Source note。'],accent=TEAL,bg='#EDF7F3'),PageBreak())
    add(Marker('contents','閱讀導航'),para('閱讀導航',23,'CNB',INK),Spacer(1,12))
    nav_rows=[]
    for i,g in enumerate(groups,1):
        nav_rows.append([para(f'{i:02d}',15,'ENB',BLUE),para(g['title'],12,'CNB',INK),para(f'{g["range"][0]:03d} – {g["range"][1]:03d}',10,'EN',MUTED)])
    nt=pad(Table(nav_rows,colWidths=[38,CW-125,87]),10)
    nt.setStyle(TableStyle([('LINEBELOW',(0,0),(-1,-1),.6,color(LINE))]));add(nt,Spacer(1,18),
        box('COLOR KEY  /  語法角色',[ 'Subject 藍  ·  Predicate 紅  ·  Object / Complement 紫  ·  Modifier / Adverbial 綠。',
             '核心詞條使用統一深色標題；近義表達用藍色列，解釋用中性色。顏色不是唯一的信息線索。']),PageBreak())
    for gi,g in enumerate(groups,1):
        add(Marker(f'g{gi}',g['title']),para(f'WORD MAP  {gi:02d}',9,'ENB',BLUE),Spacer(1,8),
            para(g['title'],23,'CNB',INK),Spacer(1,8),para(g['subtitle'],11,'CN',MUTED),Spacer(1,8),
            Scene(ctx['scene'](g.get('illustration',g.get('icon','reading'))),CW),Spacer(1,10))
        data=[]
        for title,words,explanation in g['nodes']:
            data.append(box(title,[words,explanation],(CW-16)/3,BLUE,PALE))
        row=Table([[data[0],'',data[1],'',data[2]]],colWidths=[(CW-16)/3,8,(CW-16)/3,8,(CW-16)/3]);pad(row,0)
        add(row,Spacer(1,14))
        rows=[[para('WORDS / PHRASES',8.5,'ENB',BLUE),para('區別與用法',9,'CNB',MUTED)]]
        for word,meaning,usage in g['rows']:
            rows.append([para(word,10,'CNB',BLUE),para(esc(english_terms(meaning))+'<br/>'+esc(english_terms(usage)),10,markup=True)])
        t=pad(Table(rows,colWidths=[CW*.38,CW*.62],repeatRows=1),8)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),color(PALE)),('LINEBELOW',(0,0),(-1,-1),.5,color(LINE))]))
        add(t,Spacer(1,10),box('GRAMMAR CUE',[english_terms(g['focus'])],accent=TEAL,bg='#EDF7F3'),Spacer(1,8),
            box('COMPARE CAREFULLY',[english_terms(g['warning'])],accent=AMBER,bg='#FFF7E6'),PageBreak())
        for e in (e for e in entries if g['range'][0]<=e['id']<=g['range'][1]):
            add(Marker(f's{e["id"]}',f'{e["id"]:03d} {e["keyword"]}',1,e))
            head=Table([[para(f'{e["id"]:03d}',24,'ENB',BLUE),para(e['keyword'],18,'CNB',INK),para(f'原文 p.{e["page"]}',8.5,'CN',MUTED)]],colWidths=[55,CW-121,66])
            pad(head,0);add(head,Spacer(1,12),para(ctx['highlighted'](e),14.5,'EN',INK,markup=True),Spacer(1,10),
                box('TRANSLATION',[e['translation']],accent=BLUE,bg='#F2F5FA'),Spacer(1,10),diagram(e,ctx),Spacer(1,11))
            lw=(CW-12)*.58;rw=(CW-12)*.42
            left=[box('SENTENCE STRUCTURE',e['structure'],lw,BLUE,'#F4F7FD',True),Spacer(1,7),
                  box('MEMORY KEY',[e['memory_tip']],lw,TEAL,'#EDF7F3')]
            right=[box('EXAM FOCUS',e['exam_points'],rw,AMBER,'#FFF7E6',True),Spacer(1,7),
                   box('PITFALLS',e['pitfalls'],rw,RED,'#FFF0F1')]
            grid=Table([[left,'',right]],colWidths=[lw,12,rw]);pad(grid,0)
            add(grid,Spacer(1,13),para('VOCABULARY  /  本句詞義與近義辨析',12,'CNB',INK),Spacer(1,8))
            for vi,v in enumerate(e['vocabulary'],1):add(lexical_card(v,vi))
            if e['source_note']:add(box('SOURCE NOTE  /  原文說明',[e['source_note']],accent=MUTED,bg='#F4F5F7'),Spacer(1,8))
            add(PageBreak())
    add(Marker('glossary','Grammar Glossary'),para('Grammar Glossary',25,'ENB',INK),Spacer(1,8),
        para('集中中英對照 · 例句編號可回查正文',11,'CN',MUTED),Spacer(1,14))
    rows=[[para(s,9,'CNB','#FFFFFF') for s in ['English','中文名稱','理解與例句']]]
    for t in gloss:
        ids=' / '.join(str(x) for x in t['examples'])
        rows.append([para(t['term'],10,'CNB',BLUE),para(t['translation'],10,'CNB',INK),
                     para(t['explanation']+f'  [例句 {ids}]',10)])
    gt=pad(Table(rows,colWidths=[CW*.28,CW*.22,CW*.50],repeatRows=1),9)
    gt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),color(INK)),('ROWBACKGROUNDS',(0,1),(-1,-1),[color('#FFFFFF'),color('#F3F6FC')]),
        ('LINEBELOW',(0,1),(-1,-1),.45,color(LINE))]));add(gt,PageBreak(),Marker('review','複習路線'),para('把理解變成可回憶的知識',22,'CNB',INK),Spacer(1,15))
    review=book.get('review',[
        ['01 先讀原句','先看英文，找Subject與Predicate；再恢復其他成分。'],
        ['02 對照近義','先確定本句義項，再說明近義表達的搭配或結構差別。'],
        ['03 隔天自測','離線版可按題號搜尋、遮住譯文並逐句揭曉。']])
    for title,body in review:add(box(title,[body],accent=BLUE),Spacer(1,11))
    doc.build(story,canvasmaker=AtlasCanvas)
    layout={'pages':page_count[0],'sentences':len(entries),'glossary_terms':len(gloss),
        'note_pages':note_pages,'group_pages':group_pages,'layout':[],'design_version':2}
    qa.joinpath('layout_report.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
    make_html(book,entries,groups,review,ctx,html_file)
    qa.joinpath('artifacts.json').write_text(json.dumps({'pdf':str(pdf),'html':str(html_file),'input':str(args.input.resolve()),'design_version':2},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pdf':str(pdf),'html':str(html_file),'pages':page_count[0],'sentences':len(entries),'terms':len(gloss),'design_version':2},ensure_ascii=False))

CSS='''*{box-sizing:border-box}html{scroll-behavior:auto}body{margin:0;background:#eef2f8;color:#18263d;font:15px/1.7 "Microsoft YaHei","PingFang SC",Arial,sans-serif}button,input{font:inherit}button{cursor:pointer}.toolbar{position:sticky;top:0;z-index:20;background:#17263d;color:white;padding:12px 24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}.toolbar input{width:min(380px,36vw);border:0;border-radius:7px;padding:8px 12px}.toolbar button,.toolbar a{background:transparent;color:white;border:1px solid #8191af;border-radius:6px;padding:6px 10px;text-decoration:none;font-size:13px}.layout{max-width:1420px;margin:auto;display:grid;grid-template-columns:225px minmax(0,1fr);gap:24px;padding:26px}nav{position:sticky;top:100px;max-height:calc(100vh - 130px);overflow:auto}nav a{display:block;padding:8px 10px;color:#334155;text-decoration:none;font-size:13px;border-radius:6px}nav a:hover{background:#dde7fc}.cover,.map,.note,.glossary,.review{background:white;border:1px solid #dce4ef;border-radius:14px;padding:30px;margin-bottom:26px;scroll-margin-top:110px}.eyebrow{font-size:11px;letter-spacing:.12em;font-weight:700;color:#244bc1}h1{font-size:37px;line-height:1.3;margin:16px 0}h2{font-size:25px;line-height:1.4}h3{margin:0 0 10px;font-size:12px;letter-spacing:.05em}.muted{color:#64748b}.stats{display:flex;flex-wrap:wrap;gap:32px;margin:20px 0}.stats b{font-size:29px;color:#244bc1}.notehead{display:flex;gap:18px;align-items:center;border-bottom:1px solid #dce4ef;padding-bottom:15px}.notehead h2{margin:0}.num{font-size:36px;line-height:1;font-weight:bold;color:#244bc1}.source{font-size:12px;color:#64748b;margin-left:auto}.original{font:22px/1.65 Arial,sans-serif;margin:22px 0 16px}.translation{background:#f1f5fb;border-left:4px solid #244bc1;padding:14px 18px;border-radius:0 8px 8px 0;font-size:17px}.translation:before{content:"TRANSLATION";display:block;font-size:10px;color:#64748b;font-weight:bold;letter-spacing:.1em;margin-bottom:5px}.diagram{display:flex;gap:17px;margin:24px 0;align-items:stretch}.node{flex:1;min-width:0;position:relative;background:#f7f9fd;border:1px solid #dce4ef;border-top:3px solid var(--c);border-radius:7px;padding:11px}.node small{display:block;color:var(--c);font-weight:bold;font-size:11px;line-height:1.45;margin-bottom:9px}.node p{font:14px/1.55 Arial,sans-serif;margin:0;overflow-wrap:anywhere}.node:not(:last-child):after{content:"→";position:absolute;right:-17px;top:45%;color:#64748b}.decode-grid{display:grid;grid-template-columns:1.2fr 1fr;gap:14px;margin:20px 0}.panel{border:1px solid #dce4ef;border-left:4px solid var(--accent);background:var(--bg);border-radius:0 9px 9px 0;padding:15px 17px;margin-bottom:12px}.panel h3{color:var(--accent)}.panel p{font-size:14px;line-height:1.8;margin:8px 0}.panel ol{margin:0;padding-left:22px;font-size:14px}.panel li{padding:4px 0}.vocab-heading{font-size:15px;margin:26px 0 12px}.lex-card{border:1px solid #dce4ef;border-radius:10px;overflow:hidden;margin-bottom:15px;background:white}.lex-head{display:flex;gap:14px;align-items:baseline;padding:12px 17px;background:#e8eef9;border-left:4px solid #244bc1}.lex-head span{font-size:12px;color:#64748b}.lex-head h4{font-size:21px;line-height:1.4;margin:0}.lex-meaning{font-size:15px;padding:13px 20px;margin:0}.synonyms{margin:0 16px 16px;border:1px solid #e0e7f2;border-radius:6px;overflow:hidden}.syn-head,.syn-row{display:grid;grid-template-columns:minmax(150px,.8fr) minmax(0,1.7fr);gap:16px;padding:10px 13px}.syn-head{background:#eef3ff;font-size:10px;font-weight:bold;color:#64748b;letter-spacing:.04em}.syn-row+.syn-row{border-top:1px solid #e1e7f0}.syn-row strong{color:#244bc1;font-size:16px;line-height:1.5}.syn-row p{margin:0;font-size:14px;line-height:1.8}.no-synonym{padding:0 20px 16px;font-size:13px;color:#64748b}.scene{display:block;max-width:560px;width:100%;margin:20px auto}.mapnodes{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}.mapnodes div{padding:15px;background:#eef3ff;border-radius:8px}.mapnodes strong,.mapnodes span{display:block}.mapnodes small{color:#64748b}.map table,.glossary table{border-collapse:collapse;width:100%;font-size:14px;margin:20px 0}.map td,.glossary td,.glossary th{border-bottom:1px solid #dce4ef;text-align:left;vertical-align:top;padding:12px}.glossary th{background:#17263d;color:white}.glossary tr:nth-child(even){background:#f3f6fc}.glossary a{color:#244bc1}.showone{display:none;color:#244bc1;background:transparent;border:0;margin:7px 0}.selftest .showone{display:inline-block}.selftest .translation{filter:blur(6px);cursor:pointer;user-select:none}.selftest .translation.revealed{filter:none;user-select:text}.empty{display:none;padding:22px;background:white}.note[hidden],.map[hidden]{display:none}.toplink{display:block;text-align:right;color:#64748b;font-size:12px}.legend{display:flex;gap:8px;flex-wrap:wrap}.legend span{padding:4px 9px;border:1px solid currentColor;border-radius:6px;font-size:12px}#result{font-size:12px;color:#cbd5e1}@media(max-width:1000px){.layout{grid-template-columns:1fr;padding:14px}nav{display:none}.cover,.map,.note,.glossary,.review{padding:22px}.decode-grid{grid-template-columns:1fr}.toolbar input{width:100%;order:3}.notehead{flex-wrap:wrap}.source{width:100%;margin-left:0}.notehead h2{font-size:24px}.glossary{overflow:auto}.note,.map,.glossary{scroll-margin-top:165px}}@media(max-width:600px){.diagram{flex-direction:column;gap:22px}.node p{font-size:16px;overflow-wrap:normal;word-break:normal}.node small{font-size:12px}.node:not(:last-child):after{content:"↓";right:auto;left:50%;top:auto;bottom:-24px}.syn-head{display:none}.syn-row{display:block}.syn-row p{margin-top:7px}.lex-head h4{font-size:20px}.lex-meaning{font-size:15px}.mapnodes{grid-template-columns:1fr}.original{font-size:21px}.cover,.map,.note,.glossary,.review{padding:18px}}@media print{.toolbar,nav,.showone,.toplink{display:none}.layout{display:block;padding:0}.cover,.map,.note,.glossary,.review{border:0;box-shadow:none;break-before:page;margin:0}.selftest .translation{filter:none}.note[hidden],.map[hidden]{display:block}.lex-card,.panel,.diagram{break-inside:avoid}.decode-grid{grid-template-columns:1.2fr 1fr}}'''

def make_html(book,entries,groups,review,ctx,path):
    E=esc;meta=book['meta'];parts=[f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(meta["title"])}</title><style>{CSS}</style><body id="top"><div class="toolbar"><strong>English Atlas</strong><input id="search" type="search" placeholder="搜尋題號、詞彙或考點" aria-label="搜尋筆記"><button id="test" aria-pressed="false">開啟譯文自測</button><button id="reset">重置</button><a href="#glossary">Grammar Glossary</a><span id="result">{len(entries)} 句</span></div><div class="layout"><nav><a href="#top">閱讀指南</a>']
    for gi,g in enumerate(groups,1):parts.append(f'<a href="#g{gi}">{gi:02d} {E(g["title"])}<br>{g["range"][0]} – {g["range"][1]}</a>')
    parts.append(f'<a href="#glossary">Grammar Glossary</a></nav><main><section class="cover"><div class="eyebrow">{E(meta["chapter"])}</div><h1>English Atlas<br>英語精讀圖譜</h1><p class="muted">完整譯文 · 清晰拆句 · 近義辨析 · 考點定位</p><div class="stats"><span><b>{len(entries)}</b><br>逐題精讀</span><span><b>{len(groups)}</b><br>詞義圖譜</span><span><b>{len(book["glossary"])}</b><br>Grammar 對照</span></div><div class="legend">')
    for col,label in [('#2457BD','Subject'),('#B84132','Predicate'),('#7446A7','Object / Complement'),('#167361','Modifier / Adverbial')]:parts.append(f'<span style="color:{col}">{label}</span>')
    parts.append(f'</div><p>每個詞條獨立成卡。先讀本句義項，再看藍色近義表達及右側替換限制。Exam focus與Pitfalls獨立成區，便於快速找到重點。</p><p class="muted">來源：{E(meta["source_name"])}，原文{meta["source_pages"]}頁。原文與建議改寫分列；文件可完全離線使用。</p></section><p class="empty" id="empty">沒有匹配結果，請換一個詞或題號。</p>')
    def panel(title,items,accent,bg,ordered=False):
        body=('<ol>'+''.join('<li>'+E(x)+'</li>' for x in items)+'</ol>' if ordered else ''.join('<p>'+E(x)+'</p>' for x in items))
        return f'<section class="panel" style="--accent:{accent};--bg:{bg}"><h3>{title}</h3>{body}</section>'
    for gi,g in enumerate(groups,1):
        parts.append(f'<section class="map" id="g{gi}"><div class="eyebrow">WORD MAP {gi:02d} / {g["range"][0]}–{g["range"][1]}</div><h2>{E(g["title"])}</h2><p class="muted">{E(g["subtitle"])}</p>{ctx["scene_svg"](g.get("illustration",g.get("icon","reading")))}<div class="mapnodes">')
        for title,words,meaning in g['nodes']:parts.append(f'<div><strong>{E(title)}</strong><span>{E(words)}</span><small>{E(meaning)}</small></div>')
        parts.append('</div><table><tbody>')
        for w,m,u in g['rows']:parts.append(f'<tr><td><b>{E(w)}</b></td><td>{E(english_terms(m))}<br>{E(english_terms(u))}</td></tr>')
        parts.append('</tbody></table>'+panel('GRAMMAR CUE',[english_terms(g['focus'])],TEAL,'#EDF7F3')+panel('COMPARE CAREFULLY',[english_terms(g['warning'])],AMBER,'#FFF7E6')+'</section>')
        for e in (e for e in entries if g['range'][0]<=e['id']<=g['range'][1]):
            parts.append(f'<article class="note" id="s{e["id"]}" data-id="{e["id"]}"><div class="notehead"><span class="num">{e["id"]:03d}</span><h2>{E(e["keyword"])}</h2><span class="source">原文 p.{e["page"]}</span></div><div class="original" lang="en">{ctx["highlighted"](e)}</div><button class="showone">顯示或隱藏本句譯文</button><div class="translation">{E(e["translation"])}</div><div class="diagram">')
            for n in e['diagram']:parts.append(f'<div class="node" style="--c:{ctx["color_for"](n["role"])}"><small>{E(n["role"])}</small><p lang="en">{E(n["text"])}</p></div>')
            parts.append('</div><div class="decode-grid"><div>'+panel('SENTENCE STRUCTURE',e['structure'],BLUE,'#F4F7FD',True)+panel('MEMORY KEY',[e['memory_tip']],TEAL,'#EDF7F3')+'</div><div>'+panel('EXAM FOCUS',e['exam_points'],AMBER,'#FFF7E6',True)+panel('PITFALLS',e['pitfalls'],RED,'#FFF0F1')+'</div></div><h3 class="vocab-heading">VOCABULARY / 本句詞義與近義辨析</h3>')
            for vi,v in enumerate(e['vocabulary'],1):
                if isinstance(v,str):parts.append(panel('Vocabulary',[v],BLUE,PALE));continue
                parts.append(f'<section class="lex-card"><div class="lex-head"><span>W{vi:02d}</span><h4 lang="en">{E(v["term"])}</h4></div><p class="lex-meaning">{E(v["explanation"])}</p>')
                if v['near_synonyms']:
                    parts.append('<div class="synonyms"><div class="syn-head"><span>NEAR SYNONYMS</span><span>差別 / 替換限制</span></div>')
                    for s in v['near_synonyms']:parts.append(f'<div class="syn-row"><strong lang="en">{E(s["text"])}</strong><p>{E(s["distinction"])}</p></div>')
                    parts.append('</div>')
                if v.get('no_synonym_reason'):parts.append(f'<p class="no-synonym">NEAR SYNONYMS / {E(v["no_synonym_reason"])}</p>')
                parts.append('</section>')
            if e['source_note']:parts.append(panel('SOURCE NOTE / 原文說明',[e['source_note']],MUTED,'#F4F5F7'))
            parts.append('<a class="toplink" href="#top">回到頂部 ↑</a></article>')
    parts.append('<section class="glossary" id="glossary"><h2>Grammar Glossary</h2><p class="muted">集中中英對照；點擊例句編號返回正文。</p><table><thead><tr><th>English</th><th>中文名稱</th><th>理解與例句</th></tr></thead><tbody>')
    for t in book['glossary']:
        links=' / '.join(f'<a href="#s{i}">{i}</a>' for i in t['examples'])
        parts.append(f'<tr><td><b>{E(t["term"])}</b></td><td>{E(t["translation"])}</td><td>{E(t["explanation"])}<br>{links}</td></tr>')
    parts.append('</tbody></table></section><section class="review"><h2>複習路線</h2>')
    for title,body in review:parts.append(panel(E(title),[body],BLUE,PALE))
    parts.append('''</section></main></div><script>
const notes=[...document.querySelectorAll('.note')],maps=[...document.querySelectorAll('.map')],search=document.querySelector('#search'),test=document.querySelector('#test');
function filter(){let q=search.value.trim().toLowerCase(),n=0;for(const a of notes){let ok=!q||(/^\\d+$/.test(q)?Number(a.dataset.id)===Number(q):a.textContent.toLowerCase().includes(q));a.hidden=!ok;if(ok)n++}maps.forEach(m=>m.hidden=!!q);document.querySelector('#result').textContent=q?n+' / '+notes.length+' 句':notes.length+' 句';document.querySelector('#empty').style.display=n?'none':'block'}
search.addEventListener('input',filter);test.addEventListener('click',()=>{let b=document.body.classList.toggle('selftest');test.setAttribute('aria-pressed',b);test.textContent=b?'退出譯文自測':'開啟譯文自測';document.querySelectorAll('.translation').forEach(x=>x.classList.remove('revealed'))});
document.querySelector('#reset').addEventListener('click',()=>{search.value='';filter();document.body.classList.remove('selftest');test.textContent='開啟譯文自測';test.setAttribute('aria-pressed','false')});
notes.forEach(n=>{const t=n.querySelector('.translation');n.querySelector('.showone').addEventListener('click',()=>t.classList.toggle('revealed'));t.addEventListener('click',()=>{if(document.body.classList.contains('selftest'))t.classList.toggle('revealed')})});
document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>{if(search.value){search.value='';filter()}}));
</script></body></html>''')
    path.write_text(''.join(parts),encoding='utf-8')
