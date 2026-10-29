// v6: offline-first. Pages open from cache at once (any ?p= deep link), and refresh the cache in the background.
// No forced reloads: the page never reloads itself when a new version installs; the new copy is used next time it opens.
const C='poker-v6-1030';const F=['./','index.html','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const q=e.request;if(q.method!=='GET'||new URL(q.url).origin!==location.origin)return;
  const nav=q.mode==='navigate';
  e.respondWith(caches.open(C).then(c=>c.match(nav?'./':q,{ignoreSearch:true}).then(hit=>{
    const net=fetch(q).then(r=>{if(r&&r.ok){c.put(nav?'./':q,r.clone());}return r;}).catch(()=>null);
    if(hit){e.waitUntil(net);return hit;}
    return net.then(r=>r||c.match('index.html'));
  })));
});
