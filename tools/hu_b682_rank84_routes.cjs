const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),cp=require('node:child_process');
const args=process.argv.slice(2),opt=n=>args.includes(n)?args[args.indexOf(n)+1]:null;
const route=JSON.parse(cp.execFileSync('node',['tools/hu_b674_threebet_call_routes.cjs',...args],{encoding:'utf8'}))['84'];
const app={innerHTML:'',querySelectorAll:()=>[],addEventListener(){}};
const c={console,__LINES_QA:true,location:{hash:'#lines'},scrollTo(){},addEventListener(){},document:{querySelector:()=>app,querySelectorAll:()=>[],getElementById:()=>null}};
c.window=c;vm.createContext(c);
for(const f of ['lines_data.js','nl2_rules.js','hwrange.js','nl2_reach.js','nl2_titles.js','nl2_hu_model.js','nl2.js'])
 vm.runInContext(fs.readFileSync(f==='nl2_hu_model.js'?(opt('--model-file')||f):f==='nl2.js'?(opt('--ui-file')||f):f,'utf8'),c,{filename:f});
c.__linesQA.render('3bp');
const start='ln-3bp-3b_f_cbet-1ueswd8',facing='ln-3bp-3b_f_vs_donk-12vwqfc';
assert.equal(route.source,facing);assert.equal(route.line,'x b33 c/');assert.equal(route.seat,0);
assert.deepEqual([route.turn_pot,route.turn_stack],[3486,8307]);
const section=app.innerHTML.split('id="'+start+'"')[1].split('<div class="sec"')[0],classes=['TPG','TPW','MID','DRAW','WDRAW'];
for(const [texture,data]of Object.entries(route.routes)){
 const row=section.match(new RegExp('<tr[^>]+id="'+start+'-'+texture+'">([\\s\\S]*?)</tr>'));assert.ok(row);
 const cells=[...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/g)].map(m=>m[1]);
 data.parents=data.parents.filter(cls=>{
  const html=cells[classes.indexOf(cls)],first=html.match(/<a class="jmp" href="#[^"]+">([^<]+)<\/a>/);
  return first?.[1].replace(/≈$/,'')==='過' && html.includes('class="jmp sub" href="#'+facing+'-'+texture+'"');
 });
 assert.ok(data.parents.length,'No genuine initial check -> call -> turn path on '+texture);
}
console.log(JSON.stringify({'84':route}));
