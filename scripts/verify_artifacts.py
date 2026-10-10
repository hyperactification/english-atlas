"""Check complete content and render PDF pages for visual review."""
from pathlib import Path
import argparse,json,re,sys,shutil,subprocess
from pypdf import PdfReader
from PIL import Image,ImageDraw

def normalize(s):return re.sub(r'\s+','',str(s)).replace('’',"'")
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--qa-dir',required=True,type=Path)
    ap.add_argument('--render',action='store_true')
    a=ap.parse_args();q=a.qa_dir.resolve()
    artifacts=json.loads((q/'artifacts.json').read_text(encoding='utf-8'))
    layout=json.loads((q/'layout_report.json').read_text(encoding='utf-8'))
    entries=json.loads((q/'rendered_content.json').read_text(encoding='utf-8'))
    pdf=Path(artifacts['pdf']);html=Path(artifacts['html'])
    reader=PdfReader(pdf);texts=[normalize(p.extract_text() or '') for p in reader.pages]
    fail=[];checks=0
    for j,e in enumerate(entries):
        start=layout['note_pages'][str(e['id'])]-1
        end=layout['note_pages'][str(entries[j+1]['id'])]-1 if j+1<len(entries) else len(texts)
        content=''.join(texts[start:end])
        for key in ['english','translation','memory_tip','source_note','structure','vocabulary','exam_points','pitfalls']:
            values=e.get(key,'');values=values if isinstance(values,list) else [values]
            for i,s in enumerate(values):
                if not s:continue
                checks+=1
                if normalize(s) not in content:fail.append({'id':e['id'],'field':key,'item':i})
    markup=html.read_text(encoding='utf-8')
    html_count=len(re.findall(r'<article class="note"',markup))
    if html_count!=len(entries):fail.append({'html_count':html_count,'expected':len(entries)})
    if len(reader.pages)!=layout['pages']:fail.append({'pdf_pages':len(reader.pages),'expected':layout['pages']})
    result={'pass':not fail,'sentences':len(entries),'pdf_pages':len(reader.pages),'checked_text_blocks':checks,'failures':fail,'rendered':False}
    if a.render:
        candidates=[Path(sys.executable).resolve().parent.parent/'native/poppler/Library/bin/pdftoppm.exe']
        candidates+=[Path(v) for v in [shutil.which('pdftoppm')] if v]
        exe=next((v for v in candidates if v.is_file()),None)
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
