/* Browser behavior check for the generated, fully offline notebook. */
const fs=require('fs'),path=require('path'),os=require('os');
function arg(key){let i=process.argv.indexOf(key);return i>=0?process.argv[i+1]:null}
function playwright(){
  const roots=[process.env.NODE_PATH,path.join(path.dirname(process.execPath),'../node_modules'),path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')].filter(Boolean);
  for(const r of roots){try{return require(path.join(r,'playwright'))}catch{}}
  return require('playwright');
}
(async()=>{
  const file=arg('--html'),qa=arg('--qa-dir');if(!file||!qa)throw Error('Usage: node check_web.cjs --html FILE --qa-dir DIR');
  fs.mkdirSync(qa,{recursive:true});const {chromium}=playwright();let browser;
  try{browser=await chromium.launch({channel:'msedge',headless:true})}catch{browser=await chromium.launch({headless:true})}
  const page=await browser.newPage({viewport:{width:1365,height:1000}}),errors=[],externalRequests=[];
  await page.route(/^https?:/,route=>{externalRequests.push(route.request().url());return route.abort()});
  page.on('pageerror',e=>errors.push(e.message));
  const url=require('url').pathToFileURL(path.resolve(file)).href;await page.goto(url);
  const count=await page.locator('.note').count();if(!count)throw Error('No notes rendered');
  const brokenLinks=await page.locator('a[href^="#"]').evaluateAll(links=>links.map(a=>a.getAttribute('href')).filter(h=>!document.getElementById(h.slice(1))));
  if(brokenLinks.length)throw Error('Broken internal links: '+brokenLinks.join(', '));
  const id=await page.locator('.note').first().getAttribute('data-id');
  await page.locator('#search').fill(id);
  if(await page.locator('.note:visible').count()!==1)throw Error('Numeric search did not match exactly one note');
  const n=page.locator('#s'+id);await page.locator('#test').click();
  if(await n.locator('.translation').evaluate(e=>getComputedStyle(e).filter)==='none')throw Error('Self-test mask failed');
  await n.locator('.showone').click();
  if(await n.locator('.translation').evaluate(e=>getComputedStyle(e).filter)!=='none')throw Error('Single answer reveal failed');
  await page.locator('#reset').click();if(await page.locator('.note:visible').count()!==count)throw Error('Reset failed');
  const word=(await n.locator('h2').textContent()).trim();await page.locator('#search').fill(word);
  if(await page.locator('.note:visible').count()<1)throw Error('Text search failed');
  await page.locator('#search').fill('__NO_NOTE_MATCH_489172__');
  if(await page.locator('.note:visible').count()!==0||!await page.locator('#empty').isVisible())throw Error('No-result state failed');
  await page.locator('#reset').click();
  const target=await page.locator('.glossary a').first().getAttribute('href');await page.locator('.glossary a').first().click();
  if(!page.url().endsWith(target))throw Error('Glossary navigation failed');
  await page.locator('#search').fill(id);await page.locator('#test').click();await page.emulateMedia({media:'print'});
  if(await page.locator('.note:visible').count()!==count||await n.locator('.translation').evaluate(e=>getComputedStyle(e).filter)!=='none'||await page.locator('.toolbar').isVisible())throw Error('Print mode did not restore all content');
  await page.emulateMedia({media:'screen'});
  await page.goto(url);await page.screenshot({path:path.join(qa,'web-desktop.png')});
  await page.setViewportSize({width:390,height:844});await page.goto(url+'#s'+id);await n.evaluate(e=>e.scrollIntoView());
  await page.screenshot({path:path.join(qa,'web-mobile.png')});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2);if(overflow)throw Error('Mobile horizontal overflow');
  const splitWords=await page.locator('.node p').evaluateAll(nodes=>{
    const failures=[];
    for(const p of nodes){const text=p.firstChild;if(!text||text.nodeType!==3)continue;
      for(const match of text.textContent.matchAll(/[A-Za-z]{3,}/g)){
        const r=document.createRange();r.setStart(text,match.index);r.setEnd(text,match.index+match[0].length);
        if(r.getClientRects().length>1)failures.push(match[0]);
      }
    }return [...new Set(failures)];
  });if(splitWords.length)throw Error('Mobile diagram splits words: '+splitWords.join(', '));
  if(externalRequests.length)throw Error('Offline notebook attempted network requests: '+externalRequests.join(', '));
  const result={pass:!errors.length,notes:count,glossary:await page.locator('.glossary tbody tr').count(),numericSearch:true,textSearch:true,noResultState:true,selfTest:true,singleReveal:true,reset:true,glossaryNavigation:true,internalLinks:true,printRestoresContent:true,offline:true,mobileOverflow:overflow,mobileDiagramWordsIntact:true,errors};
  fs.writeFileSync(path.join(qa,'web-verification.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));await browser.close();if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
