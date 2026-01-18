async function loadJson(p){ const r = await fetch(p); return await r.json(); }
(async function(){
  const el = document.getElementById('app');
  try{
    const history = await loadJson('../data/history.json');
    const metrics = await loadJson('../data/metrics.json');
    el.innerHTML = '<h3>Latest</h3><pre>'+JSON.stringify({latest: history.latest, metrics}, null, 2)+'</pre>'
                 + '<h3>History</h3><pre>'+JSON.stringify(history.items.slice(-25), null, 2)+'</pre>';
  }catch(e){
    el.textContent = 'Dashboard data not found yet. Run a freeze to populate dashboard/data/.';
  }
})();
