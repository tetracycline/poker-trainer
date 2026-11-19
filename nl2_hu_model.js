/*
 * NL2 HU modeled continuation bridge (100bb assumptions), NOT a GTO certification.
 * Creates full turn/river navigation for otherwise unrepresented legal action
 * histories, preserving real nodes where they exist. No implicit cross-pot CERT.
 * Every modeled node says ASSUMED; references never masquerade as CFR outputs.
 */
(function(root){
'use strict';
const BTS=[['low','9 以下低牌面'],['mid_high','J/T 高面'],['KQ_high','K/Q 高面'],['A_high','A 高面'],['paired','成對面'],['mono','單色面']];
const HC=['頂對好','頂對弱','中小對','強聽','弱聽'];
const PFX=['3b_','3c_','lmp_','iso_'];
const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const strip=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/\s+/g,' ').trim();
const btId=txt=>{const t=strip(txt); for(const [id,zh] of BTS)if(t===zh||t.endsWith('・'+zh))return id;return null;};
const pfxOf=nd=>PFX.find(x=>nd.startsWith(x))||'';
const stOf=nd=>{nd=nd.replace(/^(3b_|3c_|lmp_|iso_)/,'');return nd.startsWith('r_')?2:nd.startsWith('t_')?1:0;};
const HASH=s=>{let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619);return (h>>>0).toString(36);};
const isTerminal=txt=>/^棄|^加注\s*全下|^全下/.test(strip(txt));
function action(text){
  const t=strip(text);
  if(/^棄/.test(t))return 'fold';
  if(/^全下|^加注\s*全下/.test(t))return 'terminal';
  if(/^跟/.test(t))return 'call';
  if(/^加注/.test(t))return 'raise';
  if(/^過/.test(t))return 'check';
  if(/^下注/.test(t))return 'bet';
  return 'unknown';
}
function sizeRatio(text,stage){
  const x=strip(text),m=x.match(/(⅓|½|⅔|¾|1½|1\.5|\d+(?:\.\d+)?%|\d+(?:\.\d+)?)/);
  const A={'⅓':1/3,'½':1/2,'⅔':2/3,'¾':3/4,'1½':1.5};
  if(m){const z=m[1];return z in A?A[z]:z.endsWith('%')?+z.slice(0,-1)/100:+z;}
  return stage===0?1/3:stage===1?1/2:3/4;
}
const round=n=>Math.round(1000*n)/1000;
function profile(pre){
  const p=strip(pre),is3=/3-bet/.test(p),isL=/溜入/.test(p);
  let fam='SRP',spot='ASSUMED_SRP',pot=5.5,stack=97.5;
  if(is3){
    fam='3BP';pot=20.5;stack=90;spot='BB3_BTN';
    if(/SB 3-bet/.test(p)){pot=21;spot='SB3_BTN';}
    if(/BTN 3-bet/.test(p)){pot=16.5;stack=92.5;spot='CO3_BTN';}
  }else if(isL){
    if(/加注隔離/.test(p)){fam='ISO';spot='ASSUMED_ISO_4BB';pot=/SB 加注隔離/.test(p)?9:9.5;stack=96;}
    else{fam='LMP';spot='ASSUMED_LMP';pot=2.5;stack=99;}
  }else{
    if(/SB 開/.test(p)){pot=6;stack=97;spot='SB_BB';}
    else if(/UTG 開/.test(p)&&/CO 跟/.test(p)){pot=6.5;spot='UTG_CO';}
    else if(/CO 開/.test(p)){spot='CO_BB';}
    else if(/BTN 開/.test(p)){spot='BTN_BB';}
  }
  const range=(fam==='ISO')?'ASSUMED: isolator top~22%, limp/caller ~28%, suited broadway/pairs/connectors':
    fam==='LMP'?'ASSUMED: limper ~35%, BB check unrestricted after no raise':
    'PRE_FLOP_CFR: poker-solver 169 hand classes weighted by exact preflop action';
  return {family:fam,spot,pot,stack,rootSPR:round(stack/pot),range};
}
function roleHistory(s){
  const parts=String(s.key||'').split('|');
  while(parts.length<=s.st)parts.push('');
  return parts;
}
function walkActions(s){
  const P=profile(s.pre),hist=roleHistory(s);
  let pot=P.pot,stack=P.stack;
  const ratios={0:1/3,1:1/2,2:3/4};
  for(let st=0;st<=s.st;st++){
    const a=(hist[st]||'').split('、').filter(Boolean);
    let spent=[0,0],base=pot;
    for(const token of a){
      const p=token.startsWith('你')?0:1;
      const v=token.replace(/^(你|對手)/,'');
      if(v==='過'||v==='棄')continue;
      const high=Math.max(...spent);
      if(v==='跟'){spent[p]=high;}
      else if(v==='下注'||v==='超池下注'){
        const target=(v==='超池下注'?1.5:ratios[st])*base;
        spent[p]=Math.min(Math.max(spent[p],target),stack);
      } else if(v==='加注'){
        spent[p]=Math.min(Math.max(high*3,base*ratios[st],spent[p]),stack);
      }
    }
    const inc=spent[0]+spent[1];pot=base+inc;
    stack=Math.max(0,stack-Math.max(...spent));
  }
  return {pot:round(pot),stack:round(stack),root:P};
}
function transition(meta,action,size,stage){
  const P=meta.pot,S=meta.stack;
  const ratio=Math.max(0.25,Math.min(1.5,size||sizeRatio('',stage)));
  let addPot=0,spent=0;
  if(action==='bet') {spent=Math.min(S,ratio*P);addPot=2*spent;}
  else if(action==='raise') {spent=Math.min(S,Math.max(1.5*P,ratio*P*2));addPot=2*spent;}
  else if(action==='call') {spent=Math.min(S,0.5*P);addPot=spent;}
  return {pot:round(P+addPot),stack:round(Math.max(0,S-spent)),root:meta.root};
}
function keyNext(source,action,stage){
  const parts=roleHistory(source);const last=parts[source.st]||'';
  const w={bet:'下注',raise:'加注',check:'過',call:'跟'}[action]||'過';
  const response=action==='bet'||action==='raise'?'、對手跟':action==='check'?'、對手過':'';
  parts[source.st]=last+(last?'、':'')+'你'+w+response;
  const next=source.st+1;
  if(next<=2)parts[next]=stage===2?'對手過':'對手過';
  return parts.slice(0,next+1).join('|');
}
function titleFor(pre,key,stage){
  const p=String(key).split('|');
  const a=[pre];
  for(let i=0;i<=stage;i++){
    const st=['翻牌','轉牌','河牌'][i];
    if(i===stage) a.push(st+'：'+(p[i]||'')+((p[i]||'')?'，':'')+'輪到你，下注或過牌？');
    else if(p[i])a.push(st+'：'+p[i]);
  }
  return a.join(' → ');
}
function modeledDecision(stage,bt,ci,spr){
  // Provisional size/mix assumptions. They MUST NOT be represented as CERT GTO.
  const wet=bt==='mono'||bt==='paired',short=spr<1.5;
  if(ci===0)return short?['bet','下注 ½']:wet?['bet','下注 ¾']:['bet','下注 ½'];
  if(ci===1)return stage===2?['check','過']:wet?['check','過']:['bet','下注 ⅓'];
  if(ci===2)return ['check','過'];
  if(ci===3)return stage===2?['check','過']:['bet','下注 ½'];
  return ['check','過'];
}
function repair(html,sp,catalog){
  const map=new Map((catalog||[]).map(it=>[it.id,it]));
  const tags=[...html.matchAll(/<div class="sec" data-node="([^"]+)" id="([^"]+)">/g)];
  if(!tags.length)return html;
  const sections=tags.map((m,i)=>{
    const [ssp,nd]=m[1].split('/'),item=map.get(m[2]);
    const part=html.slice(m.index,i+1<tags.length?tags[i+1].index:html.length);
    const title=strip((part.match(/<b class="ttl">([\s\S]*?)<\/b>/)||[])[1]);
    return {sp:ssp,nd,st:stOf(nd),pfx:pfxOf(nd),id:m[2],title,pre:title.split(' → ')[0],
      key:item?.key||'',pf:item?.pf||'',part};
  });
  const model=new Map(),created=[],ids=new Set(sections.map(x=>x.id));
  const make=(s,action,label)=>{
    const stage=s.st+1;
    if(stage>2)throw Error('No street beyond river');
    const size=sizeRatio(label,s.st);
    const key=[s.sp,s.id,stage,action,round(size)].join('|');
    if(model.has(key))return model.get(key);
    const nd=s.pfx+(stage===1?'t_model':'r_model');
    let id='ln-'+s.sp+'-'+nd+'-'+HASH(key);
    if(ids.has(id))id+='x'+HASH(key+'collision');
    if(ids.has(id))throw Error('Unexpected modeled id collision');
    ids.add(id);
    const m=s.modelMeta||walkActions(s);
    const next=transition(m,action,size,s.st),line=keyNext(s,action,stage);
    const x={id,sp:s.sp,nd,st:stage,pfx:s.pfx,source:s.id,action,size:round(size),
      pre:s.pre,modelMeta:next,key:line,title:titleFor(s.pre,line,stage),allowed:new Set(),
      facts:{root:next.root,pot:next.pot,stack:next.stack,spr:next.pot?round(next.stack/next.pot):0}};
    model.set(key,x);created.push(x);return x;
  };
  function destinationClassReach(dest,bt,ci){
    const rows=[...dest.part.matchAll(/<tr\b([^>]*)>([\s\S]*?)<\/tr>/g)];
    for(const m of rows){
      const rowid=(m[1].match(/\bid="([^"]+)"/)||[])[1]||'';
      let tx=BTS.find(([id])=>rowid.endsWith('-'+id))?.[0];
      if(!tx){const th=(m[2].match(/<th[^>]*>([\s\S]*?)<\/th>/)||[])[1];tx=btId(th);}
      if(tx!==bt)continue;
      const cells=[...m[2].matchAll(/<td\b([^>]*)>([\s\S]*?)<\/td>/g)];
      const c=cells[ci];if(c&&!/\bna\b/.test(c[1])&&strip(c[2])!=='—')return true;
    }
    return false;
  }
  function firstText(cell){
    const p=(cell.match(/<a class="jmp" href="#[^"]+">([\s\S]*?)<\/a>/)||[])[1];
    if(p)return strip(p);
    const at=cell.split(/<a class="jmp sub"|<small\b/)[0];
    return strip(at);
  }
  function fromCell(section,bt,ci,inner){
    const text=firstText(inner),act=action(text);
    if(act==='fold'||act==='terminal'||act==='unknown')return inner;
    const primary=(inner.match(/<a class="jmp" href="#([^"]+)"/ )||[])[1];
    if(primary){
      // Existing real table's next-street links are retained; repair their
      // downstream nodes instead of bypassing authentic available strategies.
      const dest=sections.find(s=>primary===s.id||primary.startsWith(s.id+'-'));
      if(dest && dest.st===section.st+1 && destinationClassReach(dest,bt,ci))return inner;
      // Existing same-street main links must not be silently counted as river.
    }
    const dst=make(section,act,text);dst.allowed.add(bt+':'+ci);
    let clean=inner.replace(/<small class="lo"[^>]*>待解：缺下一街<\/small>/g,'');
    const link='<a class="jmp" href="#'+dst.id+'-'+bt+'">'+esc(text)+'</a>';
    if(primary)clean=clean.replace(/<a class="jmp" href="#[^"]+">[\s\S]*?<\/a>/,link);
    else if(clean.includes(text))clean=clean.replace(text,link);
    else clean=link+' '+clean;
    clean+=' <small class="df" data-df="MODEL（假設續街，不是解算）">假設續街</small>';
    return clean;
  }
  let patched=html.slice(0,tags[0].index);
  for(const s of sections){
    if(s.sp!==sp||s.st>=2){patched+=s.part;continue;}
    let rows=0;
    const updated=s.part.replace(/<tr\b([^>]*)>([\s\S]*?)<\/tr>/g,(whole,attrs,body)=>{
      if(!/<td\b/.test(body))return whole;
      const rowid=(attrs.match(/\bid="([^"]+)"/)||[])[1]||'';
      let bt=BTS.find(([id])=>rowid.endsWith('-'+id))?.[0];
      if(!bt){const th=(body.match(/<th[^>]*>([\s\S]*?)<\/th>/)||[])[1];bt=btId(th);}
      if(!bt)return whole;
      let ci=0;
      const cells=body.replace(/<td\b([^>]*)>([\s\S]*?)<\/td>/g,(c,ta,inner)=>{
        const idx=ci++;
        if(idx>=5||/\bna\b/.test(ta)||strip(inner)==='—')return c;
        return '<td'+ta+'>'+fromCell(s,bt,idx,inner)+'</td>';
      });
      rows++;return '<tr'+attrs+'>'+cells+'</tr>';
    });
    if(!rows)throw Error('Expected some rows in '+s.id);
    patched+=updated;
  }
  // Every assumed table contains ONLY the row/class combinations reachable
  // from a source visible parent. The rest stay NA, not invented GTO ranges.
  for(let pos=0;pos<created.length;pos++){
    const n=created[pos];
    const P=n.facts;const rootP=P.root;
    const tr=BTS.map(([bt,zh])=>{
      const cells=HC.map((hand,ci)=>{
        if(!n.allowed.has(bt+':'+ci))return '<td class="na">—</td>';
        const [a,label]=modeledDecision(n.st,bt,ci,P.spr);
        let link='';
        if(n.st===1){
          const r=make(n,a,label);r.allowed.add(bt+':'+ci);
          link='<a class="jmp" href="#'+r.id+'-'+bt+'">'+esc(label)+'</a>';
        } else link=esc(label);
        return '<td class="'+(a==='check'?'x':'b')+'">'+link+
          ' <small class="df" data-df="ASSUMED（非 GTO，非 CERT）">MODEL</small></td>';
      }).join('');
      return '<tr data-cl="'+esc(zh)+'" id="'+n.id+'-'+bt+'"><th class="cl"><span class="df" data-df="'+esc(zh)+'">'+esc(zh)+'</span></th>'+cells+'</tr>';
    }).join('');
    const sizeDesc='100bb；'+rootP.family+'；'+rootP.range+'；根底池 '+rootP.pot+'bb／根餘額 '+rootP.stack+
      'bb／根 SPR '+rootP.rootSPR+'；模型節點底池約 '+P.pot+'bb、剩餘有效籌碼約 '+P.stack+'bb、SPR 約 '+P.spr+
      '；每街採常見 ⅓／½／¾ 底池下注、加注到 3 倍並由對手跟注；所有值是明示假設，非真實逐 combo 解算。';
    patched+='<div class="sec" data-node="'+n.sp+'/'+n.nd+'" id="'+n.id+'"><b class="ttl">'+esc(n.title)+'</b>'+
      '<p class="navln"><a class="jmp" href="#'+n.source+'">↑ 上一步</a></p>'+
      '<p class="small muted"><b>MODEL／待真實 CFR：</b>'+esc(sizeDesc)+
      ' 預設代表同分類（brick）延續；實際發牌轉換分類應重新判斷，不能視為 CERT 或 EST。</p>'+
      '<div class="tw"><table class="rt lt"><tr><th></th>'+HC.map(h=>'<th>'+esc(h)+'</th>').join('')+'</tr>'+tr+'</table></div></div>';
  }
  // A few legacy secondary action links point to filtered-out/unpublished
  // line IDs. An impossible anchor must never masquerade as a valid line.
  patched=patched.replace(/<a class="jmp sub" href="#([^"]+)">([\s\S]*?)<\/a>/g,(all,href,label)=>{
    const base=href.replace(/-(?:low|mid_high|KQ_high|A_high|paired|mono)$/,'');
    return ids.has(base) ? all : '<small class="lo" title="無可達來源，未建立該支線">'+strip(label).replace(/→$/,'')+'（待證）</small>';
  });
  root.__HU_MODEL_LAST={spot:sp,synthetic:created.length,assumption:true,sourceSections:sections.length};
  return patched;
}
root.NL2HUModel={repair,version:'hu-nl2-100bb-assumption-v1'};
})(typeof window!=='undefined'?window:globalThis);