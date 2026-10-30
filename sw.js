// v7b: pages load network-first (cache only when offline / slow >3s), so new versions show right away.
const C='poker-v7d-1030';const F=['./','index.html','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const q=e.request;if(q.method!=='GET'||new URL(q.url).origin!==location.origin)return;
  const nav=q.mode==='navigate';const key=nav?'./':q;
  e.respondWith(caches.open(C).then(c=>{
    const net=fetch(q,{cache:'no-store'}).then(r=>{if(r&&r.ok){c.put(key,r.clone());}return r;});
    const cached=()=>c.match(key,{ignoreSearch:true}).then(h=>h||c.match('index.html'));
    if(!nav)return c.match(q,{ignoreSearch:true}).then(h=>{if(h){e.waitUntil(net.catch(()=>{}));return h;}return net.catch(cached);});
    return new Promise(res=>{let done=false;const t=setTimeout(()=>cached().then(h=>{if(!done&&h){done=true;res(h);}}),3000);
      net.then(r=>{if(!done){done=true;clearTimeout(t);res(r);}}).catch(()=>cached().then(h=>{if(!done){done=true;res(h);}}));});
  }));
});
