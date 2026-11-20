"use strict";
// Static-source CoPolitic contrast and first-use canary. No remote requests.
// Redacted diagnostic: never emit text content, node HTML, raw CSS selectors,
// secrets, page bodies, image data, or user submissions.
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const {pathToFileURL} = require("node:url");
const {execFileSync} = require("node:child_process");
const {chromium} = require("playwright-core");
const EXPECTED_SOURCE_BLOB = "a6ef70f8bd8413175e0bf5af334ba2c725c6acbb";
const AUDIT_TAGS = ["wcag2a","wcag2aa","wcag21a","wcag21aa"];
const OUT = path.resolve("out/copolitic-contrast-candidate-r0");
const hex = buf => crypto.createHash("sha256").update(buf).digest("hex");
const gitBlob = b => crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");
function binary() {
  for(const c of ["google-chrome","google-chrome-stable","chromium"]){
    try {return execFileSync("which",[c],{encoding:"utf8"}).trim();}catch(_){}
  }
  throw Error("HOLD_NO_CHROMIUM");
}
async function main(){
  fs.mkdirSync(OUT,{recursive:true});
  const receipt={
    schema:"CoPolitic.SourceFirstUse.ContrastReadiness.R0",
    state:"HOLD_AWAITING_SCAN",
    observed_utc:new Date().toISOString(),
    ci_head:process.env.GITHUB_SHA||"UNATTESTED",
    source_blob_sha1:null,source_sha256:null,views:[],reasons:[],
    boundary:"PINNED_SOURCE_BROWSER_ONLY_NOT_HUMAN_ACCESSIBILITY_ACCEPTANCE",
    nonclaims:["NO_DOMAIN_DEPLOYMENT","NO_VISITOR_ACCEPTANCE","NO_REMOTE_BROWSER_REQUESTS",
      "NO_THREE_INDEPENDENT_ROOTS","NO_COEX","NO_X2_RUNTIME","NO_PHANTOM_ACK"]
  };
  let browser=null;
  try {
    const src=fs.readFileSync("index.html");
    const blob=gitBlob(src);receipt.source_blob_sha1=blob;receipt.source_sha256=hex(src);
    if(blob!==EXPECTED_SOURCE_BLOB)throw Error("HOLD_SOURCE_BYTES_DRIFT");
    const axe=fs.readFileSync(require.resolve("axe-core/axe.min.js"),"utf8");
    browser=await chromium.launch({executablePath:binary(),headless:true,args:["--no-sandbox","--disable-dev-shm-usage"]});
    for(const viewport of [{name:"mobile390",width:390,height:844},{name:"desktop1365",width:1365,height:900}]) {
      const ctx=await browser.newContext({viewport:{width:viewport.width,height:viewport.height},deviceScaleFactor:1,reducedMotion:"reduce"});
      const attempts=[];const errors=[];
      await ctx.route(/^https?:/i, async route=>{
        attempts.push("BLOCKED_EXTERNAL_REQUEST"); await route.abort("blockedbyclient");
      });
      const page=await ctx.newPage();
      page.on("pageerror",e=>errors.push(String(e.name).slice(0,32)));
      try {
        await page.goto(pathToFileURL(path.resolve("index.html")).href,{waitUntil:"load",timeout:15000});
        await page.addScriptTag({content:axe});
        const result=await page.evaluate(async tags=>window.axe.run(document,{
          runOnly:{type:"tag",values:tags},resultTypes:["violations","incomplete"]
        }),AUDIT_TAGS);
        const incomplete=result.incomplete.filter(x=>x.id==="color-contrast");
        const targets=incomplete.flatMap(x=>x.nodes.map(n=>(Array.isArray(n.target)?n.target[0]:null)));
        const hints=await page.evaluate(rawTargets=>rawTargets.map(sel=>{
          if(typeof sel!=="string")return {kind:"UNKNOWN_NODE"};
          let el=null;
          try{el=document.querySelector(sel);}catch(_){}
          if(!el)return {kind:"UNRESOLVED_SELECTOR"};
          const spans=[...document.querySelectorAll("span")];
          const css=getComputedStyle(el);
          const parent=el.parentElement;
          const pc=parent?getComputedStyle(parent):null;
          const gp=parent?.parentElement;
          const gpc=gp?getComputedStyle(gp):null;
          const knownPart=el.closest(".steps")?"steps":
            el.closest("header")?"header":el.closest(".card")?"card":
            el.closest(".hero")?"hero":el.closest("footer")?"footer":"other";
          return {
            tag:el.tagName.toLowerCase(),span_ordinal:spans.indexOf(el),
            region:knownPart,
            parent_tag:parent?.tagName.toLowerCase()||null,
            parent_classes:(parent?.className||"").toString().split(/\s+/)
              .filter(x=>/^[a-z0-9_-]{1,35}$/i.test(x)).slice(0,4),
            element_color:css.color,
            element_bg:css.backgroundColor,
            parent_bg:pc?.backgroundColor||null,
            grandparent_bg:gpc?.backgroundColor||null,
            parent_display:pc?.display||null,
            aria_hidden:el.getAttribute("aria-hidden")==="true"
          };
        }),targets);
        const overflow=await page.evaluate(()=>Math.max(0,document.documentElement.scrollWidth-window.innerWidth,document.body.scrollWidth-window.innerWidth));
        const png=await page.screenshot({fullPage:true});
        const filename=viewport.name+".png";
        fs.writeFileSync(path.join(OUT,filename),png);
        receipt.views.push({viewport:viewport.name,width:viewport.width,height:viewport.height,
          violations:result.violations.map(v=>v.id).sort(),
          inconclusive_color_contrast_elements:targets.length,
          inconclusive_other_ids:result.incomplete.filter(x=>x.id!=="color-contrast").map(x=>x.id).sort(),
          redacted_element_hints:hints,
          overflow_px:overflow,blocked_http_requests:attempts.length,script_errors:errors.length,
          screenshot_filename:filename,screenshot_sha256:hex(png)});
        if(result.violations.length||result.incomplete.length||overflow>2||attempts.length||errors.length)
          receipt.reasons.push("HOLD_"+viewport.name);
      } finally {await ctx.close();}
    }
    receipt.state=receipt.reasons.length?"HOLD_NEEDS_MANUAL_CONTRAST_ASSESSMENT":"PASS_SOURCE_CONTRAST_PROBES_NOT_HUMAN_ACCEPTED";
    if(receipt.reasons.length)process.exitCode=1;
  }catch(e){
    receipt.state="HOLD_SOURCE_BROWSER_ERROR";
    receipt.reasons.push(String(e.message||e).slice(0,200).replace(/https?:\/\/\S+/g,"URL_REDACTED"));
    process.exitCode=2;
  }finally{
    if(browser)await browser.close();
    fs.writeFileSync(path.join(OUT,"audit_receipt.json"),JSON.stringify(receipt,null,2)+"\n");
    console.log(JSON.stringify({state:receipt.state,views:receipt.views.map(v=>({
      viewport:v.viewport,violations:v.violations.length,incomplete:v.inconclusive_color_contrast_elements,
      hints:v.redacted_element_hints})),reasons:receipt.reasons}));
  }
}
main().catch(e=>{console.error("HOLD_UNHANDLED",e.name);process.exitCode=3;});
