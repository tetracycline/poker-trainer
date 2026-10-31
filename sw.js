// v8 + postflop: network-first for the app (new versions show right away); river data cache-first (versioned file name).
const C='poker-v8-1101d';const F=['./','index.html','app.js','pf_data.js','solver.html','learn.html','learn.js','learn_data.js','reads_data.js','eq_data.js','eq.js','nav.js','keys.js','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const q=e.request,u=new URL(q.url);if(q.method!=='GET'||u.origin!==location.origin)return;if(u.pathname.includes('/postflop/')||u.pathname.includes('/review/'))return;// postflop module: plain network (its gz data is fetched on demand)
  const nav=q.mode==='navigate';const key=nav?(u.pathname.endsWith('solver.html')?'solver.html':u.pathname.endsWith('learn.html')?'learn.html':'./'):q;
  e.respondWith(caches.open(C).then(c=>{
    if(/\/data\/|\/river\//.test(u.pathname))return c.match(q,{ignoreSearch:true}).then(h=>h||fetch(q).then(r=>{if(r&&r.ok)c.put(q,r.clone());return r;}));
    const net=fetch(q,{cache:'no-store'}).then(r=>{if(r&&r.ok){c.put(key,r.clone());}return r;});
    const cached=()=>c.match(key,{ignoreSearch:true}).then(h=>h||(nav?c.match('index.html'):undefined));
    return new Promise(res=>{let done=false;const t=setTimeout(()=>cached().then(h=>{if(!done&&h){done=true;res(h);}}),3000);
      net.then(r=>{if(!done){done=true;clearTimeout(t);res(r);}}).catch(()=>cached().then(h=>{if(!done){done=true;res(h||Response.error());}}));});
  }));
});
