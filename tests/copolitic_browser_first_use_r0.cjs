#!/usr/bin/env node
'use strict';
/* Browser acceptance of the EXACT public CoPolitic source draft.
   A Chromium test is not human acceptance, live-domain proof, voting,
   machine receiver acknowledgment, or authorization to publish.
   Only a loopback HTTP server is used; any outside request is denied.
*/
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require('playwright-core');

const ROOT = path.resolve(__dirname, '..');
const OUTPUT = path.join(ROOT, 'out', 'copolitic-first-use-r0');
const html = fs.readFileSync(path.join(ROOT, 'index.html'));
const machine = fs.readFileSync(path.join(ROOT, 'ai', 'index.json'));
const llms = fs.readFileSync(path.join(ROOT, 'llms.txt'));
const manifest = JSON.parse(machine);
const sha256 = data => crypto.createHash('sha256').update(data).digest('hex');
const gitBlob = data => crypto.createHash('sha1')
  .update(Buffer.concat([Buffer.from('blob ' + data.length + '\0'),data])).digest('hex');
const pinnedSelf = manifest.discovered_sources.find(x =>
  x.repo === 'CoCivium/CoPolitic-site' && x.path === 'index.html');

assert(pinnedSelf && pinnedSelf.blob_sha1 === gitBlob(html),
       'HOLD_BROWSER_SOURCE_DIFFERS_FROM_PINNED_HUMAN_MANIFEST');
assert.equal(manifest.state,
 'GITHUB_REVIEW_BRANCH__PUBLIC_SAFE_SOURCE__NOT_DEPLOYED__NO_EXTERNAL_RECEIVER_ACK');
const pages = new Map([
  ['/', ['text/html; charset=utf-8', html]],
  ['/index.html', ['text/html; charset=utf-8', html]],
  ['/ai/index.json', ['application/json', machine]],
  ['/llms.txt', ['text/plain; charset=utf-8', llms]],
]);
const negative = Buffer.from(html.toString('utf8').replace('</body>',
  '<form action="https://example.org/collect"><button>Cast vote</button></form></body>'));
pages.set('/negative-control.html', ['text/html; charset=utf-8', negative]);
const server = http.createServer((req,res)=>{
  if (req.url === '/favicon.ico') {res.writeHead(204); return res.end();}
  const hit = pages.get(req.url);
  if (!hit) {res.writeHead(404, {'Content-Type':'text/plain'});return res.end('HOLD_NOT_FOUND');}
  res.writeHead(200, {'Content-Type':hit[0], 'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
  res.end(hit[1]);
});

async function noEffectfulControls(page) {
  const count = await page.locator('form,button,input,textarea,select,iframe,script,[contenteditable]').count();
  assert.equal(count,0,'HOLD_ACTIVE_CIVIC_CONTROL_IN_SOURCE');
}

(async ()=>{
  await new Promise((resolve,reject)=>{
    server.once('error',reject);
    server.listen(0,'127.0.0.1',resolve);
  });
  let browser;
  try {
    browser = await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox']});
    const origin = 'http://127.0.0.1:' + server.address().port;
    const context = await browser.newContext({reducedMotion:'reduce'});
    let externalRequests = 0, blockedRoutes = 0;
    await context.route('**/*', async route=>{
      const u = new URL(route.request().url());
      if (u.origin !== origin || !pages.has(u.pathname)) {
        if (u.origin !== origin) externalRequests++;
        blockedRoutes++;
        await route.abort('blockedbyclient');
        return;
      }
      await route.continue();
    });
    const viewportChecks=[];
    const screenshots=[];
    for(const width of [320,390,768,1280]) {
      const page=await context.newPage();
      await page.setViewportSize({width,height:840});
      const response=await page.goto(origin+'/',{waitUntil:'load',timeout:15000});
      assert.equal(response.status(),200,'HOLD_LOOPBACK_SOURCE_SERVE');
      assert.equal(await page.locator('main').count(),1,'HOLD_MAIN_COUNT');
      assert.equal(await page.locator('h1').count(),1,'HOLD_H1_COUNT');
      assert.equal(await page.locator('html').getAttribute('lang'),'en','HOLD_LANG');
      assert.equal(await page.locator('.status').count(),1,'HOLD_STATUS');
      const overflow = await page.evaluate(() =>
        Math.max(0,document.documentElement.scrollWidth-window.innerWidth));
      assert.equal(overflow,0,'HOLD_HORIZONTAL_OVERFLOW_'+width);
      await noEffectfulControls(page);
      await page.keyboard.press('Tab');
      const firstFocus=await page.evaluate(()=>({
        href:document.activeElement.getAttribute('href'),
        text:(document.activeElement.textContent||'').trim(),
        outline:getComputedStyle(document.activeElement).outlineStyle,
        visible:!!(document.activeElement.getBoundingClientRect().height)
      }));
      assert.equal(firstFocus.href,'#main','HOLD_FIRST_FOCUS_NOT_SKIP_LINK');
      assert.notEqual(firstFocus.outline,'none','HOLD_FIRST_FOCUS_NOT_VISIBLE');
      assert(firstFocus.visible,'HOLD_FIRST_FOCUS_HIDDEN');
      assert(await page.getByText('Prototype, not a deployed civic service.').isVisible(),
             'HOLD_NO_CANDIDATE_WARNING');
      assert(await page.getByRole('heading',{name:'Choose one useful starting point'}).isVisible(),
             'HOLD_NO_FIRST_USE_CHOICE');
      await page.locator('nav a[href="#begin"]').click();
      assert(page.url().endsWith('#begin'),'HOLD_NAVIGATION_DEAD_END');
      if(width===390||width===1280){
        const out=path.join(OUTPUT,'copolitic-pr1-'+width+'.png');
        fs.mkdirSync(OUTPUT,{recursive:true});
        await page.screenshot({path:out,fullPage:true,animations:'disabled'});
        screenshots.push({file:path.basename(out),sha256:sha256(fs.readFileSync(out))});
      }
      viewportChecks.push({width,overflow_px:overflow,first_focus:firstFocus.href,
        forms:0,buttons:0,site_url_proven:false});
      await page.close();
    }
    const bad=await context.newPage();
    await bad.goto(origin+'/negative-control.html',{waitUntil:'load'});
    await assert.rejects(()=>noEffectfulControls(bad),/HOLD_ACTIVE_CIVIC_CONTROL_IN_SOURCE/,
                         'negative control must reject a fake voting form');
    await bad.close();
    assert.equal(externalRequests,0,'HOLD_EXTERNAL_BROWSER_NETWORK_ATTEMPT');
    assert.equal(blockedRoutes,0,'HOLD_OUT_OF_SCOPE_BROWSER_ROUTE');
    const receipt={
      schema:'CoPolitic.PublicPRBrowserFirstUse.R0',
      state:'PR_SOURCE_CHROMIUM_PASS_ONLY',
      source_git_blob_sha1:gitBlob(html),
      source_sha256:sha256(html),
      machine_index_sha256:sha256(machine),
      viewport_checks:viewportChecks,
      screenshots,
      external_request_attempts:externalRequests,
      forbidden_route_attempts:blockedRoutes,
      fake_vote_form_negative_control:'REJECTED',
      effects:0,
      real_vote: false, user_consent:false, human_acceptance:false,
      github_source_only:true, deployed_domain_verified:false,
      external_receiver_ack:false, independent_failure_domains:0,
      master_committed:false, authorized_publication:false,
      next:'HOLD_OWNER_AND_HOSTING_THEN_INDEPENDENT_HUMAN_FIRST_USE'
    };
    fs.mkdirSync(OUTPUT,{recursive:true});
    fs.writeFileSync(path.join(OUTPUT,'readback.json'),JSON.stringify(receipt,null,2)+'\n',
                     {flag:'wx'});
    console.log('PASS_COPOLITIC_PR_SOURCE_CHROMIUM_FOUR_VIEWPORTS__NO_LIVE_DOMAIN_ACK');
    console.log(JSON.stringify(receipt));
    await context.close();
  } finally {
    if(browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(e=>{console.error('HOLD_COPOLITIC_BROWSER_FIRST_USE',e);process.exitCode=3;});
