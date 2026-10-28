"""Check complete content and render PDF pages for visual review."""
from pathlib import Path
import argparse,json,re,sys,shutil,subprocess
from pypdf import PdfReader
from PIL import Image,ImageDraw
from runtime_support import find_native_tool

def normalize(s):return re.sub(r'\s+','',str(s)).replace('’',"'")
def printed_fragments(item):
    if not isinstance(item,dict):return [item]
    result=[item['term'],item['explanation']]
    for synonym in item.get('near_synonyms',[]):result.extend([synonym['text'],synonym['distinction']])
    if item.get('no_synonym_reason'):result.append(item['no_synonym_reason'])
    return result
def body_text(page,seen_headings=None,card_headings=()):
    # Repeated page headers/footers are not part of a paragraph that continues
    # on the next page. Keep the body and memory tip in PDF drawing order.
    parts=[];header=[];height=float(page.mediabox.height)
    def visit(value,cm,tm,font,size):
        y=tm[4]*cm[1]+tm[5]*cm[3]+cm[5]
        if y>=height-42:header.append(value)
        elif 42<y and value.strip():parts.append((value,y,size))
    page.extract_text(visitor_text=visit)
    # Splittable tables repeat their heading above a continued paragraph.
    # Recognise only the renderer's captions (and this book's exact card IDs),
    # at their heading font sizes. Never delete matching prose globally.
    captions={normalize(s):9.5 for s in (
        'TRANSLATION','SENTENCE STRUCTURE','EXAM FOCUS','PITFALLS',
        'MEMORY KEY','SOURCE NOTE / 原文說明')}
    captions.update({normalize(s):14 for s in card_headings})
    captions[normalize('NEAR SYNONYMS差別 / 替換限制')]=8.1
    # pypdf can divide a mixed English/Chinese caption into several runs.
    lines=[]
    for text,y,size in parts:
        if lines and abs(lines[-1][1]-y)<.8 and abs(lines[-1][2]-size)<.8:
            lines[-1][0]+=text
        else:lines.append([text,y,size])
    known=seen_headings if seen_headings is not None else set()
    continuation='精讀續頁' in normalize(''.join(header))
    skip=set()
    if continuation:
        for i,(text,y,size) in enumerate(lines):
            key=normalize(text);expected=captions.get(key)
            if y>height-120 and expected is not None and abs(size-expected)<.15 and key in known:
                skip.add(i)
            else:break
    for text,y,size in lines:
        key=normalize(text);expected=captions.get(key)
        if expected is not None and abs(size-expected)<.15:known.add(key)
    return normalize(''.join(text for i,(text,_,_) in enumerate(lines) if i not in skip))
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--qa-dir',required=True,type=Path)
    ap.add_argument('--render',action='store_true')
    a=ap.parse_args();q=a.qa_dir.resolve()
    artifacts=json.loads((q/'artifacts.json').read_text(encoding='utf-8'))
    layout=json.loads((q/'layout_report.json').read_text(encoding='utf-8'))
    entries=json.loads((q/'rendered_content.json').read_text(encoding='utf-8'))
    pdf=Path(artifacts['pdf']);html=Path(artifacts['html'])
    reader=PdfReader(pdf);seen_headings=set()
    card_headings=[f'W{vi:02d} {v["term"]}' for e in entries for vi,v in enumerate(e['vocabulary'],1) if isinstance(v,dict)]
    texts=[body_text(p,seen_headings,card_headings) for p in reader.pages]
    fail=[];checks=0
    for j,e in enumerate(entries):
        start=layout['note_pages'][str(e['id'])]-1
        end=layout['note_pages'][str(entries[j+1]['id'])]-1 if j+1<len(entries) else len(texts)
        content=''.join(texts[start:end])
        for key in ['english','translation','memory_tip','source_note','structure','vocabulary','exam_points','pitfalls']:
            values=e.get(key,'');values=values if isinstance(values,list) else [values]
            for i,item in enumerate(values):
                for fi,s in enumerate(printed_fragments(item)):
                    if not s:continue
                    checks+=1
                    if normalize(s) not in content:fail.append({'id':e['id'],'field':key,'item':i,'fragment':fi})
    markup=html.read_text(encoding='utf-8')
    html_count=len(re.findall(r'<article class="note"',markup))
    if html_count!=len(entries):fail.append({'html_count':html_count,'expected':len(entries)})
    if len(reader.pages)!=layout['pages']:fail.append({'pdf_pages':len(reader.pages),'expected':layout['pages']})
    result={'pass':not fail,'sentences':len(entries),'pdf_pages':len(reader.pages),'checked_text_blocks':checks,'failures':fail,'rendered':False}
    if a.render:
        exe=find_native_tool('pdftoppm')
        if not exe:raise SystemExit('Poppler pdftoppm is unavailable. Locate/install it before claiming visual verification.')
        pages=q/'pages';pages.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(exe),'-scale-to','1100','-png',str(pdf),str(pages/'page')],check=True)
        images=[]
        for no in range(1,len(reader.pages)+1):
            matches=[p for p in pages.glob('page-*.png') if int(re.search(r'(\d+)\.png$',p.name)[1])==no]
            if len(matches)!=1:raise SystemExit(f'Missing or ambiguous rendered page {no}')
            images.append(matches[0])
        for off in range(0,len(images),16):
            sheet=Image.new('RGB',(1200,1792),'#e5e9ee');draw=ImageDraw.Draw(sheet)
            for i,path in enumerate(images[off:off+16]):
                im=Image.open(path).convert('RGB');im.thumbnail((288,412))
                x=(i%4)*300+6;y=(i//4)*448+25;sheet.paste(im,(x,y));draw.text((x,y-18),path.stem,fill='#17263c')
            sheet.save(q/f'contact-{off//16+1:02d}.jpg',quality=88)
        result['rendered']=True;result['rendered_pages']=len(images)
    (q/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
