package uploadportal

import "fmt"

// buildPage returns the self-contained HTML for the upload portal.
// All three dynamic values are injected as JS constants so the same HTML
// template works for every tenant and token.
func buildPage(token, tenantID, callbackURL string) string {
	// Language: text/html — the %s placeholders are the only Go format verbs;
	// all %% in the CSS (background-image radial-gradient) are literal %.
	const tmpl = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ichebo Upload Portal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d0f14;--surface:#161a22;--border:#252a35;
  --primary:#6366f1;--pg:rgba(99,102,241,.18);
  --success:#22c55e;--error:#ef4444;
  --text:#f1f5f9;--muted:#64748b;--r:14px
}
body{
  font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);
  min-height:100vh;display:flex;flex-direction:column;
  align-items:center;justify-content:center;padding:24px;
  background-image:radial-gradient(ellipse at 50%% 0%%,rgba(99,102,241,.08) 0%%,transparent 70%%)
}
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);width:100%%;max-width:560px;padding:40px;
  box-shadow:0 24px 64px rgba(0,0,0,.4)
}
.logo{display:flex;align-items:center;gap:10px;margin-bottom:32px}
.logo-dot{
  width:32px;height:32px;border-radius:8px;
  background:linear-gradient(135deg,var(--primary),#818cf8);
  display:flex;align-items:center;justify-content:center
}
.logo-dot .material-symbols-outlined{font-size:18px;color:#fff}
.logo-name{
  font-size:16px;font-weight:700;
  background:linear-gradient(90deg,#6366f1,#a5b4fc);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent
}
.logo-sub{font-size:12px;color:var(--muted);font-weight:500}
h1{font-size:22px;font-weight:700;margin-bottom:6px}
.subtitle{font-size:14px;color:var(--muted);margin-bottom:32px;line-height:1.5}
.dropzone{
  border:2px dashed var(--border);border-radius:10px;
  padding:40px 24px;text-align:center;cursor:pointer;
  transition:border-color .2s,background .2s;position:relative
}
.dropzone:hover,.dropzone.drag-over{border-color:var(--primary);background:var(--pg)}
.dropzone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%%;height:100%%}
.dz-icon{font-size:48px;color:var(--primary);margin-bottom:12px;display:block}
.dz-title{font-size:15px;font-weight:600;margin-bottom:4px}
.dz-sub{font-size:13px;color:var(--muted)}
.field{margin-top:20px}
.field label{
  display:block;font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.07em;color:var(--muted);margin-bottom:6px
}
.field input{
  display:block;width:100%%;height:44px;padding:0 14px;
  background:#1e2330;border:1px solid var(--border);border-radius:8px;
  font-size:14px;color:var(--text);outline:none;font-family:inherit;
  transition:border-color .15s
}
.field input:focus{border-color:var(--primary)}
#progress-section{display:none;margin-top:28px}
.prog-file{font-size:13px;font-weight:600;margin-bottom:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.prog-bar-bg{width:100%%;height:6px;background:var(--border);border-radius:99px;overflow:hidden;margin-bottom:10px}
.prog-bar-fill{height:100%%;width:0;background:linear-gradient(90deg,var(--primary),#818cf8);border-radius:99px;transition:width .3s ease}
.prog-meta{display:flex;justify-content:space-between;font-size:12px;color:var(--muted)}
.prog-status{font-size:12px;color:var(--muted);margin-top:8px}
#done-section{display:none;flex-direction:column;align-items:center;text-align:center;padding:24px 0;gap:12px}
#done-section .check-icon{font-size:56px;color:var(--success)}
#done-section h2{font-size:18px;font-weight:700}
#done-section p{font-size:14px;color:var(--muted);line-height:1.5}
.btn{
  display:inline-flex;align-items:center;gap:8px;
  height:40px;padding:0 20px;background:var(--primary);color:#fff;
  border:none;border-radius:8px;font-size:14px;font-weight:600;
  cursor:pointer;font-family:inherit;transition:opacity .15s
}
.btn:hover{opacity:.88}
#error-section{
  display:none;margin-top:20px;
  background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);
  border-radius:8px;padding:12px 16px;
  font-size:13px;color:var(--error);line-height:1.5
}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <div class="logo-dot"><span class="material-symbols-outlined">videocam</span></div>
    <div>
      <div class="logo-name">Ichebo Upload Portal</div>
      <div class="logo-sub">Powered by Ichebo Media Engine</div>
    </div>
  </div>

  <div id="upload-section">
    <h1>Upload a Video</h1>
    <p class="subtitle">Your video will be transcoded and added to your Media Library automatically. You can close this tab after uploading — transcoding continues in the background.</p>
    <div class="dropzone" id="dropzone">
      <input type="file" id="file-input" accept="video/*">
      <span class="material-symbols-outlined dz-icon">cloud_upload</span>
      <div class="dz-title">Drag &amp; drop your video here</div>
      <div class="dz-sub">or click to browse &mdash; MP4, MOV, MKV, AVI and more</div>
    </div>
    <div class="field">
      <label for="title-input">Video Title (optional)</label>
      <input type="text" id="title-input" placeholder="Leave blank to use filename">
    </div>
    <div id="progress-section">
      <div class="prog-file" id="prog-filename">-</div>
      <div class="prog-bar-bg"><div class="prog-bar-fill" id="prog-fill"></div></div>
      <div class="prog-meta"><span id="prog-pct">0%%</span><span id="prog-speed">-</span></div>
      <div class="prog-status" id="prog-status">Preparing...</div>
    </div>
    <div id="error-section"></div>
  </div>

  <div id="done-section">
    <span class="material-symbols-outlined check-icon">check_circle</span>
    <h2>Upload Complete!</h2>
    <p>Your video has been sent for transcoding. It will appear in the Media Library once processing finishes - usually within a few minutes for short clips.</p>
    <button class="btn" onclick="window.close()">
      <span class="material-symbols-outlined" style="font-size:16px">close</span>Close this tab
    </button>
  </div>
</div>
<script>
var UPLOAD_TOKEN = %q;
var TENANT_ID    = %q;
var CALLBACK_URL = %q;
var ENGINE_BASE  = window.location.origin;
var CHUNK_SIZE   = 5 * 1024 * 1024;

var dropzone = document.getElementById('dropzone');
var fileInput = document.getElementById('file-input');
dropzone.addEventListener('dragover', function(e){e.preventDefault();dropzone.classList.add('drag-over')});
dropzone.addEventListener('dragleave', function(){dropzone.classList.remove('drag-over')});
dropzone.addEventListener('drop', function(e){
  e.preventDefault();dropzone.classList.remove('drag-over');
  if(e.dataTransfer.files[0]) startUpload(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', function(e){if(e.target.files[0]) startUpload(e.target.files[0])});

function setStatus(m){document.getElementById('prog-status').textContent=m}
function setProgress(p){
  document.getElementById('prog-fill').style.width=p+'%%';
  document.getElementById('prog-pct').textContent=Math.round(p)+'%%';
}
function showError(m){
  var el=document.getElementById('error-section');
  el.textContent=m;el.style.display='block';
  document.getElementById('progress-section').style.display='none';
}
function sleep(ms){return new Promise(function(r){setTimeout(r,ms)})}
function fmtSpeed(b){
  if(b>1048576) return (b/1048576).toFixed(1)+' MB/s';
  if(b>1024)    return (b/1024).toFixed(0)+' KB/s';
  return b.toFixed(0)+' B/s';
}

async function startUpload(file){
  document.getElementById('dropzone').style.pointerEvents='none';
  document.getElementById('progress-section').style.display='block';
  document.getElementById('prog-filename').textContent=file.name;
  document.getElementById('error-section').style.display='none';
  setProgress(0); setStatus('Initialising...');

  var title = document.getElementById('title-input').value.trim() || file.name;
  var recordId = crypto.randomUUID();

  var initData;
  try {
    var r = await fetch(ENGINE_BASE+'/engine/upload/init', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        filename: file.name,
        file_size_bytes: file.size,
        content_type: file.type || 'video/mp4',
        tenant_id: TENANT_ID,
        record_id: recordId,
        chunk_size_bytes: CHUNK_SIZE
      })
    });
    if(!r.ok) throw new Error('Engine init failed: '+r.status);
    initData = await r.json();
  } catch(e) { showError('Could not connect to the media engine. '+e.message); return; }

  var upload_id = initData.upload_id;
  var total_chunks = initData.total_chunks;
  var chunk_size_bytes = initData.chunk_size_bytes;
  var chunkChecksums = [];
  var t0 = Date.now();

  for(var n=0; n<total_chunks; n++){
    var chunk = file.slice(n*chunk_size_bytes, (n+1)*chunk_size_bytes);
    var data  = await chunk.arrayBuffer();
    var cr;
    try {
      var r2 = await fetch(ENGINE_BASE+'/engine/upload/'+upload_id+'/chunk/'+n, {
        method:'PUT',
        headers:{'Content-Type':'application/octet-stream'},
        body: data
      });
      if(!r2.ok) throw new Error('Chunk '+n+' rejected: '+r2.status);
      cr = await r2.json();
    } catch(e) { showError('Upload interrupted at chunk '+n+'. '+e.message); return; }
    chunkChecksums.push({n:n, checksum:cr.checksum});
    setProgress((n+1)/total_chunks*70);
    var speed = (n+1)*chunk_size_bytes / ((Date.now()-t0)/1000);
    document.getElementById('prog-speed').textContent = fmtSpeed(speed);
    setStatus('Uploading... chunk '+(n+1)+' / '+total_chunks);
  }

  setStatus('Finalising upload...');
  var completeData;
  try {
    var r3 = await fetch(ENGINE_BASE+'/engine/upload/'+upload_id+'/complete', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({chunk_checksums: chunkChecksums})
    });
    if(!r3.ok) throw new Error('Assembly failed: '+r3.status);
    completeData = await r3.json();
  } catch(e) { showError('Could not finalise upload. '+e.message); return; }

  setProgress(75); setStatus('Submitting for transcoding...');
  var jobData;
  try {
    var r4 = await fetch(ENGINE_BASE+'/engine/transcode', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        upload_id: upload_id,
        record_id: recordId,
        raw_object_key: completeData.raw_object_key,
        tenant_id: TENANT_ID,
        title: title,
        quality_profiles: []
      })
    });
    if(!r4.ok) throw new Error('Transcode submit: '+r4.status);
    jobData = await r4.json();
  } catch(e) { showError('Could not start transcoding. '+e.message); return; }

  setProgress(80); setStatus('Transcoding... this may take a few minutes.');
  for(var i=0; i<600; i++){
    await sleep(2000);
    try {
      var r5 = await fetch(ENGINE_BASE+'/engine/transcode/'+jobData.job_id+'/status');
      if(!r5.ok) continue;
      var d = await r5.json();
      setProgress(Math.min(80+(d.progress_pct||0)*0.18, 98));
      setStatus('Transcoding... '+(d.progress_pct||0)+'%%');
      if(d.status === 'complete'){
        setProgress(100);
        // Best-effort browser-side notification (the Go engine also fires
        // a server-side webhook after transcode completes — this is just
        // a fast-path for the "done" display in case that fires first).
        fetch(CALLBACK_URL, {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({
            token: UPLOAD_TOKEN,
            title: title,
            tenant_id: TENANT_ID,
            video_url: d.video_url || '',
            thumbnail_url: d.thumbnail_url || '',
            duration_seconds: d.duration_seconds || 0,
            record_type: 'broadcast_video',
            job_id: jobData.job_id
          })
        }).catch(function(){});
        document.getElementById('upload-section').style.display='none';
        document.getElementById('done-section').style.display='flex';
        return;
      }
      if(d.status === 'failed'){
        showError('Transcoding failed. Please try uploading again.'); return;
      }
    } catch(_){}
  }
  showError('Transcoding is taking longer than expected. Check the Media Library in a few minutes.');
}
</script>
</body>
</html>`

	return fmt.Sprintf(tmpl, token, tenantID, callbackURL)
}
