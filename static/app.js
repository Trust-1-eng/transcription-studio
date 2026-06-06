/* ════════════════════════════════════════════
   STATE
════════════════════════════════════════════ */
const state = {
  fileId: null,
  fileName: null,
  transcriptId: null,
  transcriptData: null,
  pollTimer: null,
  pollCount: 0,
  geminiData: null,
  lastConfig: null,
};

/* ════════════════════════════════════════════
   HELPERS
════════════════════════════════════════════ */
const $ = id => document.getElementById(id);

function showStep(name) {
  const steps = ['step-source','step-options','step-processing','step-results'];
  steps.forEach(s => { $(s).style.display = 'none'; });
  $(name).style.display = '';
  // Update step indicator
  const stepIndex = steps.indexOf(name);
  document.querySelectorAll('.step-dot').forEach((dot, i) => {
    dot.classList.toggle('active', i <= stepIndex);
    dot.classList.toggle('current', i === stepIndex);
  });
  document.querySelectorAll('.step-line').forEach((line, i) => {
    line.classList.toggle('active', i < stepIndex);
  });
  window.scrollTo(0, 0);
}

function toast(msg, type = '') {
  const el = $('toast');
  el.textContent = msg;
  const cls = type === 'success' ? 'toast-ok' : type === 'error' ? 'toast-err' : '';
  el.className = `toast ${cls} toast-show`;
  el.style.display = '';
  clearTimeout(el._timer);
  el._timer = setTimeout(() => {
    el.classList.remove('toast-show');
    setTimeout(() => { el.style.display = 'none'; }, 300);
  }, 3200);
}

function setProgress(pct, title, status) {
  $('progressBar').style.width = pct + '%';
  if (title) $('procTitle').textContent = title;
  if (status !== undefined) $('procStatus').textContent = status;
}

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || data.error || 'Request failed');
  return data;
}

async function apiGet(url) {
  const r = await fetch(url);
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

/* ════════════════════════════════════════════
   INIT — BUILD DYNAMIC UI
════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  checkApiHealth();
  buildLangSelect();
  buildCodeSwLangs();
  buildTransLangs();
  buildPiiGrid();
  addInitialSpeakerRow();
  loadHistory();
  bindEvents();
});

function checkApiHealth() {
  fetch('/api/health').then(r => r.json()).then(d => {
    const dot = $('apiStatus').querySelector('.dot');
    const label = $('apiLabel');
    if (d.ok) {
      dot.className = 'dot dot--ok';
      label.textContent = 'API Connected';
    } else {
      dot.className = 'dot dot--err';
      label.textContent = d.error || 'API Error';
    }
  }).catch(() => {
    const dot = $('apiStatus').querySelector('.dot');
    const label = $('apiLabel');
    dot.className = 'dot dot--err';
    label.textContent = 'Server offline';
  });
}

function buildLangSelect() {
  const sel = $('langSelect');
  TRANSCRIPTION_LANGS.forEach(l => {
    const opt = document.createElement('option');
    opt.value = l.code;
    opt.textContent = `${l.name} (${l.code})`;
    if (l.code === 'uk') opt.selected = true;
    sel.appendChild(opt);
  });
}

function buildCheckboxList(containerId, langs, namePrefix) {
  const container = $(containerId);
  container.innerHTML = '';
  langs.forEach(l => {
    const item = document.createElement('label');
    item.className = 'check-item';
    item.dataset.name = l.name.toLowerCase();
    item.innerHTML = `<input type="checkbox" name="${namePrefix}" value="${l.code}" />${l.name} <span style="color:var(--muted);font-size:11px">(${l.code})</span>`;
    container.appendChild(item);
  });
}

function buildCodeSwLangs() {
  buildCheckboxList('cswList', TRANSCRIPTION_LANGS, 'codeSwitchLang');
  $('cswSearch').addEventListener('input', e => {
    filterCheckboxList('cswList', e.target.value);
  });
}

function buildTransLangs() {
  buildCheckboxList('transList', TRANSLATION_LANGS, 'transLang');
  $('transSearch').addEventListener('input', e => {
    filterCheckboxList('transList', e.target.value);
  });
  $('transList').addEventListener('change', () => {
    const any = [...$('transList').querySelectorAll('input:checked')].length > 0;
    $('transOpts').style.display = any ? '' : 'none';
  });
}

function filterCheckboxList(containerId, query) {
  const q = query.toLowerCase();
  $(containerId).querySelectorAll('.check-item').forEach(item => {
    const match = !q || item.dataset.name.includes(q);
    item.style.display = match ? '' : 'none';
  });
}

function buildPiiGrid() {
  const grid = $('piiGrid');
  PII_POLICIES.forEach(p => {
    const item = document.createElement('label');
    item.className = 'pii-item';
    item.innerHTML = `<input type="checkbox" name="pii" value="${p.id}" />${p.label}`;
    grid.appendChild(item);
  });
}

function addInitialSpeakerRow() {
  addSpeakerRow('');
  addSpeakerRow('');
}

function addSpeakerRow(val = '') {
  const row = document.createElement('div');
  row.className = 'spk-row';
  row.innerHTML = `
    <input type="text" class="input input-sm speaker-val" placeholder="Name or Role" value="${val}" />
    <button class="btn btn-ghost btn-sm" onclick="this.parentElement.remove()">✕</button>`;
  $('spkValues').appendChild(row);
}

function addSpellingRule() {
  const row = document.createElement('div');
  row.className = 'spell-row';
  row.innerHTML = `
    <input type="text" class="input input-sm spell-from" placeholder="Written as…" />
    <span class="arrow-txt">→</span>
    <input type="text" class="input input-sm spell-to" placeholder="Should be…" />
    <button class="btn btn-ghost btn-sm" onclick="this.parentElement.remove()">✕</button>`;
  $('spellRules').appendChild(row);
}

/* ════════════════════════════════════════════
   BIND EVENTS
════════════════════════════════════════════ */
function bindEvents() {
  // Tabs
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      $('pane-file').style.display = 'none';
      $('pane-url').style.display = 'none';
      $('pane-' + tab.dataset.tab).style.display = '';
    });
  });

  // File upload
  $('btnBrowse').onclick = () => $('fileInput').click();
  $('fileInput').onchange = e => handleFileUpload(e.target.files[0]);

  const dz = $('dropzone');
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('over'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('over');
    if (e.dataTransfer.files[0]) handleFileUpload(e.dataTransfer.files[0]);
  });
  dz.addEventListener('click', e => {
    if (e.target === dz || e.target.closest('.dz-icon') || e.target.closest('.dz-title') || e.target.closest('.dz-sub'))
      $('fileInput').click();
  });

  // URL download
  $('btnDownloadUrl').onclick = handleUrlDownload;
  $('urlInput').addEventListener('keydown', e => { if (e.key === 'Enter') handleUrlDownload(); });

  // Navigate
  $('btnToOptions').onclick = () => showStep('step-options');
  $('btnBackSource').onclick = () => showStep('step-source');
  $('btnTranscribe').onclick = startTranscription;
  $('btnNew').onclick = resetAll;

  // Language mode
  $('btnAuto').onclick = () => setLangMode('auto');
  $('btnManual').onclick = () => setLangMode('manual');
  $('langSelect').addEventListener('change', () => {
    const sel = $('langSelect');
    const opt = sel.options[sel.selectedIndex];
    if (opt) {
      $('selectedLangBadge').textContent = `✓ ${opt.textContent}`;
      $('selectedLangBadge').style.display = '';
      toast(`Language: ${opt.textContent}`, 'success');
    }
  });
  $('langSearch').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    [...$('langSelect').options].forEach(opt => {
      opt.hidden = q && !opt.textContent.toLowerCase().includes(q);
    });
  });

  // Speaker labels toggle
  $('speakerLabels').onchange = function () {
    $('speakerBody').classList.toggle('disabled', !this.checked);
  };
  $('speakerID').onchange = function () {
    $('speakerIDBody').style.display = this.checked ? '' : 'none';
  };
  $('btnAddSpk').onclick = () => addSpeakerRow();

  // Speaker type buttons
  document.querySelectorAll('.spk-type-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.spk-type-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // Code switching
  $('codeSwitching').onchange = function () {
    $('cswLangsWrap').style.display = this.checked ? '' : 'none';
    $('langConfWrap').style.display = this.checked ? '' : 'none';
    if (!this.checked) {
      $('langConfThresh').value = 0.7;
      $('langConfVal').textContent = '0.7';
    }
  };

  // Language confidence threshold slider
  $('langConfThresh').oninput = function () { $('langConfVal').textContent = this.value; };

  // Auto-lower threshold for similar languages
  const SIMILAR_LANG_GROUPS = [
    ['ru', 'uk', 'be'],
    ['sr', 'hr', 'bs'],
    ['cs', 'sk'],
    ['da', 'no', 'nn'],
    ['ms', 'id'],
  ];
  function checkSimilarLangs() {
    const checked = [...document.querySelectorAll('input[name="codeSwitchLang"]:checked')].map(i => i.value);
    for (const group of SIMILAR_LANG_GROUPS) {
      const matched = checked.filter(c => group.includes(c));
      if (matched.length >= 2) {
        $('langConfThresh').value = 0.4;
        $('langConfVal').textContent = '0.4';
        toast('Language Confidence lowered to 0.4 for similar languages', 'info');
        return;
      }
    }
  }
  document.addEventListener('change', e => {
    if (e.target.name === 'codeSwitchLang') checkSimilarLangs();
  });

  // Speaker count: auto vs manual
  $('btnSpkAuto').onclick = () => setSpkMode('auto');
  $('btnSpkManual').onclick = () => setSpkMode('manual');
  $('spkRange').oninput = function () { $('spkVal').textContent = this.value; };

  // AI Analysis (Gemini)
  $('geminiEnabled').onchange = function () {
    $('geminiBody').classList.toggle('disabled', !this.checked);
  };

  // PII
  $('piiEnabled').onchange = function () {
    $('piiBody').classList.toggle('disabled', !this.checked);
  };
  $('piiAudio').onchange = function () {
    $('piiAudioOpts').style.display = this.checked ? '' : 'none';
  };

  // Content safety slider
  $('contentSafety').onchange = function () {
    $('safetyConfWrap').style.display = this.checked ? '' : 'none';
  };
  $('safetyConf').oninput = function () { $('safetyVal').textContent = this.value; };

  // Speech threshold
  $('speechThresh').oninput = function () { $('threshVal').textContent = this.value; };

  // Advanced collapse
  $('advHead').onclick = () => {
    const body = $('advBody');
    const ch = $('advChevron');
    const collapsed = body.style.display === 'none';
    body.style.display = collapsed ? '' : 'none';
    ch.classList.toggle('open', collapsed);
  };

  // Key terms
  $('keyInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      addTag('keyTags', e.target.value.trim());
      e.target.value = '';
      e.preventDefault();
    }
  });

  // Custom spelling
  $('btnAddSpell').onclick = addSpellingRule;

  // Copy transcript
  $('btnCopy').onclick = () => {
    navigator.clipboard.writeText($('transcriptBody').innerText);
    toast('Copied to clipboard', 'success');
  };

  // Edit toggle
  $('btnEdit').onclick = function () {
    const tc = $('transcriptBody');
    const editing = tc.contentEditable === 'true';
    tc.contentEditable = editing ? 'false' : 'true';
    this.textContent = editing ? 'Edit' : 'Done';
    if (!editing) tc.focus();
  };

  // Download buttons
  document.addEventListener('click', e => {
    const btn = e.target.closest('.dl-btn[data-fmt]');
    if (btn && state.transcriptId) {
      e.preventDefault();
      downloadExport(btn.dataset.fmt);
    }
  });

  // Download All ZIP
  $('btnZip').onclick = downloadAllZip;

  // History
  $('btnHistory').onclick = () => {
    const d = $('historyDrawer');
    d.style.display = d.style.display === 'none' ? '' : 'none';
  };
  $('btnCloseHistory').onclick = () => { $('historyDrawer').style.display = 'none'; };
  $('btnResume').onclick = resumeById;
  $('resumeInput').addEventListener('keydown', e => { if (e.key === 'Enter') resumeById(); });
}

function addTag(containerId, text) {
  const tag = document.createElement('span');
  tag.className = 'tag';
  tag.innerHTML = `${escHtml(text)} <span class="tag-x" onclick="this.parentElement.remove()">×</span>`;
  $(containerId).appendChild(tag);
}

function setLangMode(mode) {
  const isAuto = mode === 'auto';
  $('btnAuto').classList.toggle('active', isAuto);
  $('btnManual').classList.toggle('active', !isAuto);
  $('autoPane').style.display = isAuto ? '' : 'none';
  $('manualPane').style.display = isAuto ? 'none' : '';
  if (isAuto) $('selectedLangBadge').style.display = 'none';
}

function setSpkMode(mode) {
  const isAuto = mode === 'auto';
  $('btnSpkAuto').classList.toggle('active', isAuto);
  $('btnSpkManual').classList.toggle('active', !isAuto);
  $('spkAutoHint').style.display = isAuto ? '' : 'none';
  $('spkManualPane').style.display = isAuto ? 'none' : '';
}

/* ════════════════════════════════════════════
   FILE UPLOAD
════════════════════════════════════════════ */
async function handleFileUpload(file) {
  if (!file) return;
  showSourceStatus('⏳', 'Uploading…', file.name);

  const form = new FormData();
  form.append('file', file);

  try {
    const r = await fetch('/api/upload', { method: 'POST', body: form });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'Upload failed');
    state.fileId = data.file_id;
    state.fileName = data.name;
    showSourceStatus('✅', 'Ready', `${file.name} — audio extracted`);
    $('btnToOptions').disabled = false;
    toast('File ready', 'success');
  } catch (err) {
    showSourceStatus('❌', 'Error', err.message);
    toast(err.message, 'error');
  }
}

async function handleUrlDownload() {
  const url = $('urlInput').value.trim();
  if (!url) { toast('Enter a URL', 'error'); return; }
  showSourceStatus('⏳', 'Downloading…', url);
  $('btnDownloadUrl').disabled = true;

  try {
    const data = await apiPost('/api/download-url', { url });
    state.fileId = data.file_id;
    state.fileName = data.name;
    showSourceStatus('✅', 'Ready', data.name || url);
    $('btnToOptions').disabled = false;
    toast('Audio downloaded', 'success');
  } catch (err) {
    showSourceStatus('❌', 'Error', err.message);
    toast(err.message, 'error');
  } finally {
    $('btnDownloadUrl').disabled = false;
  }
}

function showSourceStatus(icon, title, sub) {
  const el = $('sourceStatus');
  el.style.display = '';
  $('statusIcon').textContent = icon;
  $('statusTitle').textContent = title;
  $('statusSub').textContent = sub;
}

/* ════════════════════════════════════════════
   BUILD CONFIG
════════════════════════════════════════════ */
function buildConfig() {
  const cfg = {};

  // Language
  const isAuto = $('btnAuto').classList.contains('active');
  if (isAuto) {
    cfg.language_detection = true;
    cfg.code_switching = $('codeSwitching').checked;
    if (cfg.code_switching) {
      cfg.code_switching_languages = [...document.querySelectorAll('input[name="codeSwitchLang"]:checked')].map(i => i.value);
      const lct = parseFloat($('langConfThresh').value);
      if (lct !== 0.7) cfg.language_confidence_threshold = lct;
    }
  } else {
    cfg.language_code = $('langSelect').value;
  }

  // Format
  cfg.punctuate = $('punctuate').checked;
  cfg.format_text = $('formatText').checked;
  cfg.disfluencies = $('disfluencies').checked;
  cfg.remove_audio_tags = $('removeAudioTags').checked;
  cfg.filter_profanity = $('filterProfanity').checked;

  // Speaker
  cfg.speaker_labels = $('speakerLabels').checked;
  if (cfg.speaker_labels) {
    if ($('btnSpkManual').classList.contains('active')) {
      cfg.speakers_expected = parseInt($('spkRange').value);
    }
    cfg.speaker_identification = $('speakerID').checked;
    if (cfg.speaker_identification) {
      cfg.speaker_type = document.querySelector('.spk-type-btn.active')?.dataset.v || 'name';
      cfg.speaker_known_values = [...document.querySelectorAll('.speaker-val')]
        .map(i => i.value.trim()).filter(Boolean);
    }
  }
  cfg.multichannel = $('multichannel').checked;

  // AI Analysis (Gemini)
  cfg.gemini_enabled = $('geminiEnabled').checked;
  if (cfg.gemini_enabled) {
    cfg.gemini_summary = $('geminiSummary').checked;
    cfg.gemini_notes = $('geminiNotes').checked;
    cfg.gemini_speakers = $('geminiSpeakers').checked;
  } else {
    cfg.gemini_summary = false;
    cfg.gemini_notes = false;
    cfg.gemini_speakers = false;
  }

  // Custom formatting
  const df = $('dateFormat').value;
  const pf = $('phoneFormat').value;
  const ef = $('emailFormat').value;
  if (df) cfg.date_format = df;
  if (pf) cfg.phone_format = pf;
  if (ef) cfg.email_format = ef;

  // Translation
  const transLangs = [...document.querySelectorAll('input[name="transLang"]:checked')].map(i => i.value);
  if (transLangs.length) {
    cfg.translation_languages = transLangs;
    cfg.translation_formal = $('transFormal').checked;
    cfg.translation_utterance = $('transUtterance').checked;
  }

  // PII
  cfg.redact_pii = $('piiEnabled').checked;
  if (cfg.redact_pii) {
    cfg.redact_pii_policies = [...document.querySelectorAll('input[name="pii"]:checked')].map(i => i.value);
    cfg.redact_pii_sub = $('piiSub').value;
    cfg.redact_pii_audio = $('piiAudio').checked;
    if (cfg.redact_pii_audio) {
      cfg.redact_pii_audio_quality = document.querySelector('input[name="audFmt"]:checked').value;
      cfg.redact_pii_audio_method = document.querySelector('input[name="audMethod"]:checked').value;
    }
  }

  // Medical
  cfg.medical_mode = $('medicalMode').checked;

  // English Pro
  cfg.entity_detection = $('entityDetection').checked;
  cfg.sentiment_analysis = $('sentimentAnalysis').checked;
  cfg.content_safety = $('contentSafety').checked;
  if (cfg.content_safety) cfg.content_safety_confidence = parseInt($('safetyConf').value);
  cfg.iab_categories = $('iabCategories').checked;
  cfg.auto_highlights = $('autoHighlights').checked;

  // Key terms
  cfg.keyterms_prompt = [...$('keyTags').querySelectorAll('.tag')].map(t => t.childNodes[0].textContent.trim());

  // Custom spelling
  const spellingRules = [...$('spellRules').querySelectorAll('.spell-row')];
  const spelling = spellingRules.map(r => ({
    from: [r.querySelector('.spell-from').value.trim()],
    to: r.querySelector('.spell-to').value.trim(),
  })).filter(r => r.from[0] && r.to);
  if (spelling.length) cfg.custom_spelling = spelling;

  // Advanced
  cfg.speech_threshold = parseFloat($('speechThresh').value);
  const af = $('trimFrom').value;
  const at = $('trimTo').value;
  if (af) cfg.audio_start_from = parseInt(af);
  if (at) cfg.audio_end_at = parseInt(at);

  return cfg;
}

/* ════════════════════════════════════════════
   TRANSCRIPTION
════════════════════════════════════════════ */
async function startTranscription() {
  if (!state.fileId) { toast('Upload a file first', 'error'); return; }
  const cfg = buildConfig();
  state.lastConfig = cfg;

  showStep('step-processing');
  setProgress(15, 'Uploading to AssemblyAI…', 'Sending audio to CDN');

  try {
    const data = await apiPost('/api/transcribe', { file_id: state.fileId, config: cfg, file_name: state.fileName });
    state.transcriptId = data.transcript_id;
    setProgress(30, 'Transcribing…', `Job ID: ${data.transcript_id}`);
    pollTranscript();
  } catch (err) {
    showStep('step-source');
    toast(err.message, 'error');
  }
}

function pollTranscript() {
  state.pollCount = 0;
  state.pollTimer = setInterval(async () => {
    state.pollCount++;
    const pct = Math.min(30 + state.pollCount * 3, 90);
    setProgress(pct);

    try {
      const data = await apiGet(`/api/transcript/${state.transcriptId}`);
      const status = data.status;

      const statusLabels = {
        queued: 'Queued — waiting for worker…',
        processing: 'Processing audio…',
        completed: 'Done!',
        error: `Error: ${data.error}`,
      };
      $('procStatus').textContent = statusLabels[status] || status;

      if (status === 'completed') {
        clearInterval(state.pollTimer);
        setProgress(100, 'Complete!', '');
        state.transcriptData = data;
        saveToHistory(state.transcriptId, state.fileName);
        setTimeout(() => { renderResults(data); fetchGeminiAnalysis(); }, 400);
      } else if (status === 'error') {
        clearInterval(state.pollTimer);
        showStep('step-source');
        toast(`Transcription error: ${data.error}`, 'error');
      }
    } catch (err) {
      // Network hiccup — keep polling
    }
  }, 3000);
}

/* ════════════════════════════════════════════
   RENDER RESULTS
════════════════════════════════════════════ */
function renderResults(data) {
  showStep('step-results');

  // Info bar
  const words = data.words?.length || 0;
  const duration = data.audio_duration ? Math.round(data.audio_duration) + 's' : '';
  const lang = data.language_code || '';
  $('transcriptMeta').textContent = [lang, duration, words ? `${words} words` : ''].filter(Boolean).join(' · ');
  $('tidDisplay').textContent = `ID: ${data.id}`;
  $('resultsTitle').textContent = state.fileName ? `Results: ${state.fileName}` : 'Transcription Complete';

  // Transcript body
  const tc = $('transcriptBody');
  if (data.utterances?.length) {
    tc.innerHTML = '';
    data.utterances.forEach(u => {
      const div = document.createElement('div');
      div.className = 'utterance';
      const ts = msToTime(u.start || 0);
      div.innerHTML = `<div class="spk-label">[${ts}] ${u.speaker || 'Speaker'}</div><div>${escHtml(u.text || '')}</div>`;
      tc.appendChild(div);
    });
  } else {
    tc.textContent = data.text || '';
  }

  // Analytics panels
  const ep = $('analyticsPanels');
  ep.innerHTML = '';

  if (data.entities?.length) {
    ep.appendChild(makePanel('Entities', renderEntities(data.entities)));
  }
  if (data.sentiment_analysis_results?.length) {
    ep.appendChild(makePanel('Sentiment', renderSentiment(data.sentiment_analysis_results)));
  }
  if (data.auto_highlights_result?.results?.length) {
    ep.appendChild(makePanel('Highlights', renderHighlights(data.auto_highlights_result.results)));
  }
  if (data.content_safety_labels?.results?.length) {
    ep.appendChild(makePanel('Content Safety', renderSafety(data.content_safety_labels.results)));
  }
  if (data.iab_categories_result?.results?.length) {
    ep.appendChild(makePanel('Topics', renderTopics(data.iab_categories_result.results)));
  }

  // Translation downloads
  const translationResult = getTranslationResult(data);
  const transLangs = Object.keys(translationResult);
  if (transLangs.length) {
    $('dlTranslation').style.display = '';
    const content = $('dlTransContent');
    content.innerHTML = '';
    transLangs.forEach(lang => {
      const name = TRANSLATION_LANGS.find(l => l.code === lang)?.name || lang.toUpperCase();
      const group = document.createElement('div');
      group.style.marginBottom = '12px';
      group.innerHTML = `<div class="dl-label" style="margin-bottom:6px">${name}</div>
        <div class="dl-btns">
          <button class="dl-btn" data-fmt="translation/${lang}/txt">TXT</button>
          <button class="dl-btn" data-fmt="translation/${lang}/docx">DOCX</button>
          <button class="dl-btn" data-fmt="translation/${lang}/srt">SRT</button>
          <button class="dl-btn" data-fmt="translation/${lang}/vtt">VTT</button>
        </div>
        <div class="dl-btns" style="margin-top:4px">
          <button class="dl-btn" data-fmt="bilingual/${lang}/txt">🌐 Bilingual TXT</button>
          <button class="dl-btn" data-fmt="bilingual/${lang}/docx">🌐 Bilingual DOCX</button>
        </div>`;
      content.appendChild(group);
    });
  }

  // Redacted audio
  if (data.redacted_audio_url) {
    $('dlRedacted').style.display = '';
    $('btnDlRedacted').onclick = () => downloadExport('redacted-audio');
  }

  // Analytics downloads
  const analyticsFormats = [];
  if (data.entities?.length) analyticsFormats.push(['entities/csv', 'Entities CSV']);
  if (data.sentiment_analysis_results?.length) analyticsFormats.push(['sentiment/csv', 'Sentiment CSV']);
  if (data.iab_categories_result) analyticsFormats.push(['topics/json', 'Topics JSON']);
  if (data.auto_highlights_result) analyticsFormats.push(['highlights/txt', 'Highlights TXT']);
  
  // Always offer AI Summary if Gemini panel was rendered (or if we assume it might be available)
  if ($('geminiSection')) {
      analyticsFormats.push(['summary/txt', 'AI Summary TXT']);
  }

  if (analyticsFormats.length) {
    $('dlAnalytics').style.display = '';
    $('dlAnalyticsContent').innerHTML = analyticsFormats.map(([fmt, label]) =>
      `<button class="dl-btn" data-fmt="${fmt}">${label}</button>`).join('');
  }

  // Settings used
  renderConfigPanel();
}

function makePanel(title, content) {
  const p = document.createElement('div');
  p.className = 'a-panel';
  p.innerHTML = `<div class="a-panel-head">${title}</div><div class="a-panel-body">${content}</div>`;
  return p;
}

/* ════════════════════════════════════════════
   CONFIG PANEL (settings used for this transcription)
════════════════════════════════════════════ */
function renderConfigPanel() {
  const wrap = $('configPanel');
  if (!wrap) return;
  const cfg = state.lastConfig;
  if (!cfg) { wrap.style.display = 'none'; return; }

  const lines = [];
  const add = (label, value) => lines.push(`<div class="cfg-row"><span class="cfg-label">${label}</span><span class="cfg-value">${value}</span></div>`);
  const on = '<span class="cfg-on">ON</span>';
  const off = '<span class="cfg-off">OFF</span>';
  const bool = v => v ? on : off;

  // Language
  if (cfg.language_detection) {
    add('Language', 'Auto-detect');
    if (cfg.code_switching) {
      const langs = (cfg.code_switching_languages || []).map(c => {
        const l = TRANSCRIPTION_LANGS.find(x => x.code === c);
        return l ? l.name : c;
      });
      add('Code Switching', langs.length ? langs.join(', ') : on);
      if (cfg.language_confidence_threshold) add('Language Confidence', cfg.language_confidence_threshold);
    }
  } else if (cfg.language_code) {
    const l = TRANSCRIPTION_LANGS.find(x => x.code === cfg.language_code);
    add('Language', l ? l.name : cfg.language_code);
  }

  // Format
  const fmtItems = [];
  if (cfg.punctuate) fmtItems.push('Punctuation');
  if (cfg.format_text) fmtItems.push('Formatting');
  if (cfg.disfluencies) fmtItems.push('Filler Words');
  if (cfg.remove_audio_tags) fmtItems.push('No Audio Tags');
  if (cfg.filter_profanity) fmtItems.push('Profanity Filter');
  if (fmtItems.length) add('Format', fmtItems.join(', '));

  // Speaker
  if (cfg.speaker_labels) {
    let spk = on;
    if (cfg.speakers_expected) spk = `${cfg.speakers_expected} speakers`;
    add('Speaker Diarization', spk);
    if (cfg.speaker_identification) {
      const type = cfg.speaker_type === 'role' ? 'Role' : 'Name';
      const vals = (cfg.speaker_known_values || []).filter(Boolean);
      add('Speaker ID', type + (vals.length ? ': ' + vals.join(', ') : ''));
    }
  }
  if (cfg.multichannel) add('Multichannel', on);

  // AI Analysis
  if (cfg.gemini_enabled === false) {
    add('AI Analysis', off);
  } else {
    if (cfg.gemini_summary === false) add('AI Summary', off);
    if (cfg.gemini_notes) add('Конспект', on);
    if (cfg.gemini_speakers === false) add('AI Speaker Names', off);
  }

  // Custom formatting
  if (cfg.date_format) add('Date Format', cfg.date_format);
  if (cfg.phone_format) add('Phone Format', cfg.phone_format);
  if (cfg.email_format) add('Email Format', cfg.email_format);

  // Translation
  if (cfg.translation_languages?.length) {
    const tlangs = cfg.translation_languages.map(c => {
      const l = TRANSLATION_LANGS.find(x => x.code === c);
      return l ? l.name : c;
    });
    let tr = tlangs.join(', ');
    if (cfg.translation_formal) tr += ' (formal)';
    if (cfg.translation_utterance) tr += ' · per-utterance';
    add('Translation', tr);
  }

  // PII
  if (cfg.redact_pii) {
    const policies = (cfg.redact_pii_policies || []).map(p => {
      const pol = PII_POLICIES.find(x => x.id === p);
      return pol ? pol.label : p;
    });
    add('PII Redaction', policies.length <= 5 ? policies.join(', ') : `${policies.length} categories`);
    add('PII Substitution', cfg.redact_pii_sub === 'hash' ? '####' : '[ENTITY_NAME]');
    if (cfg.redact_pii_audio) {
      add('Redact Audio', `${(cfg.redact_pii_audio_quality || 'mp3').toUpperCase()} / ${cfg.redact_pii_audio_method || 'beep'}`);
    }
  }

  // Medical
  if (cfg.medical_mode) add('Medical Mode', on);

  // English Pro
  const enPro = [];
  if (cfg.entity_detection) enPro.push('Entities');
  if (cfg.sentiment_analysis) enPro.push('Sentiment');
  if (cfg.content_safety) enPro.push(`Safety (${cfg.content_safety_confidence || 50}%)`);
  if (cfg.iab_categories) enPro.push('Topics');
  if (cfg.auto_highlights) enPro.push('Highlights');
  if (enPro.length) add('English Pro', enPro.join(', '));

  // Advanced
  if (cfg.keyterms_prompt?.length) add('Key Terms', cfg.keyterms_prompt.join(', '));
  if (cfg.custom_spelling?.length) add('Custom Spelling', `${cfg.custom_spelling.length} rules`);
  if (cfg.speech_threshold !== undefined && cfg.speech_threshold !== 0.2) add('Speech Threshold', cfg.speech_threshold);
  if (cfg.audio_start_from) add('Trim From', `${cfg.audio_start_from} ms`);
  if (cfg.audio_end_at) add('Trim To', `${cfg.audio_end_at} ms`);

  if (!lines.length) { wrap.style.display = 'none'; return; }

  wrap.style.display = '';
  wrap.innerHTML = `
    <div class="cfg-panel-head" onclick="this.parentElement.querySelector('.cfg-panel-body').classList.toggle('collapsed')">
      <span>⚙ Settings Used</span>
      <span class="cfg-chevron">▾</span>
    </div>
    <div class="cfg-panel-body">${lines.join('')}</div>`;
}

/* ════════════════════════════════════════════
   GEMINI AI ANALYSIS
════════════════════════════════════════════ */
async function fetchGeminiAnalysis() {
  if (!state.transcriptId) return;
  if (!state.lastConfig?.gemini_enabled) return;
  const ep = $('analyticsPanels');

  // Placeholder skeleton
  const sk = document.createElement('div');
  sk.id = 'geminiSection';
  sk.innerHTML = `
    <div class="gemini-header">
      <span class="gemini-badge">✦ AI Analysis</span>
      <span class="gemini-loading">Analyzing…</span>
    </div>
    <div class="a-panel"><div class="a-panel-body">
      <div class="skeleton-line" style="width:60%"></div>
      <div class="skeleton-line" style="width:90%"></div>
      <div class="skeleton-line" style="width:75%"></div>
    </div></div>`;
  ep.prepend(sk);

  try {
    const geminiOpts = {
      summary: state.lastConfig?.gemini_summary !== false,
      notes: !!state.lastConfig?.gemini_notes,
      speakers: state.lastConfig?.gemini_speakers !== false,
    };
    const result = await apiPost(`/api/gemini/${state.transcriptId}`, geminiOpts);
    if (result.error) { sk.remove(); return; }
    state.geminiData = result;
    renderGeminiPanels(result);
    // Add summary download button after Gemini loads
    const dlA = $('dlAnalytics');
    const dlC = $('dlAnalyticsContent');
    if (dlA && dlC && !dlC.querySelector('[data-fmt="summary/txt"]')) {
      dlA.style.display = '';
      dlC.insertAdjacentHTML('beforeend', '<button class="dl-btn" data-fmt="summary/txt">AI Summary TXT</button>');
    }
  } catch {
    sk.remove();
  }
}

function renderGeminiPanels(data) {
  let section = $('geminiSection');
  if (!section) {
    section = document.createElement('div');
    section.id = 'geminiSection';
    $('analyticsPanels').prepend(section);
  }
  section.innerHTML = '<div class="gemini-header"><span class="gemini-badge">✦ AI Analysis</span></div>';

  // Title + Summary
  if (data.title || data.summary) {
    let html = '';
    if (data.title) {
      html += `<div class="gemini-title">${escHtml(data.title)}</div>`;
      html += `<label class="toggle-row" style="margin:8px 0;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:8px">
        <input type="checkbox" id="useGeminiTitle" checked style="accent-color:var(--amber);width:16px;height:16px">
        <span style="color:var(--muted)">Використовувати AI-назву для файлів</span>
      </label>`;
    }
    if (data.summary) html += `<div class="gemini-summary">${escHtml(data.summary)}</div>`;
    section.appendChild(makePanel('Summary', html));
  }

  // Notes (Конспект)
  if (data.notes?.length) {
    const items = data.notes.map(n => `<li class="note-item">${escHtml(n)}</li>`).join('');
    section.appendChild(makePanel('Конспект', `<ul class="notes-list">${items}</ul>`));
  }

  // Topics
  if (data.topics?.length) {
    const tags = data.topics.map(t => `<span class="topic-tag">${escHtml(t)}</span>`).join('');
    section.appendChild(makePanel('Topics', tags));
  }

  // Sentiment
  if (data.sentiment) {
    const s = data.sentiment;
    const colors = { POSITIVE: 'var(--green)', NEGATIVE: 'var(--red)', NEUTRAL: 'var(--muted)', MIXED: 'var(--amber)' };
    const color = colors[s.overall] || 'var(--muted)';
    let html = `<div class="sentiment-overall" style="color:${color}"><strong>${s.overall}</strong>`;
    if (s.score !== undefined) html += ` <span class="sentiment-score">(${s.score > 0 ? '+' : ''}${s.score.toFixed(1)})</span>`;
    html += `</div>`;
    if (s.details) html += `<div class="sentiment-detail">${escHtml(s.details)}</div>`;
    section.appendChild(makePanel('Sentiment', html));
  }

  // Key Moments
  if (data.key_moments?.length) {
    const items = data.key_moments.map(m =>
      `<div class="key-moment">
        <div class="key-moment-quote">"${escHtml(m.text)}"</div>
        <div class="key-moment-reason">${escHtml(m.reason)}</div>
      </div>`).join('');
    section.appendChild(makePanel('Key Moments', items));
  }

  // Speakers
  const useGeminiSpeakers = state.lastConfig?.gemini_speakers !== false;
  if (data.speakers && Object.keys(data.speakers).length) {
    const rows = Object.entries(data.speakers).map(([label, info]) => {
      const name = typeof info === 'object' ? (info.name || label) : info;
      const role = typeof info === 'object' ? (info.role || '') : '';
      return `<div class="speaker-map">
        <span class="speaker-label">${escHtml(label)}</span>
        <span class="speaker-arrow">→</span>
        <span class="speaker-name">${escHtml(name)}${role ? ' <span class="muted">(' + escHtml(role) + ')</span>' : ''}</span>
      </div>`;
    }).join('');
    section.appendChild(makePanel('Speakers', rows));

    // Replace Latin speaker names with Cyrillic in utterances (only if enabled)
    if (useGeminiSpeakers) {
      const tc = $('transcriptBody');
      if (tc) {
        tc.querySelectorAll('.spk-label').forEach(el => {
          for (const [label, info] of Object.entries(data.speakers)) {
            const name = typeof info === 'object' ? (info.name || '') : '';
            if (name && el.textContent.includes(label)) {
              el.textContent = el.textContent.replace(label, name);
            }
          }
        });
      }
    }
  }
}

function renderEntities(entities) {
  return entities.slice(0, 50).map(e =>
    `<span class="entity-tag">
      <strong>${e.entity_type}</strong>: ${escHtml(e.text)}
    </span>`
  ).join('');
}

function renderSentiment(results) {
  const colors = { POSITIVE: 'var(--green)', NEGATIVE: 'var(--red)', NEUTRAL: 'var(--muted)' };
  return `<div style="display:flex;flex-direction:column;gap:6px">` +
    results.slice(0, 20).map(s => {
      const c = colors[s.sentiment] || 'var(--muted)';
      return `<div style="display:flex;gap:10px;align-items:baseline">
        <span style="color:${c};font-weight:600;font-size:11px;min-width:70px">${s.sentiment}</span>
        <span style="font-size:13px">${escHtml(s.text)}</span>
      </div>`;
    }).join('') + '</div>';
}

function renderHighlights(results) {
  return results.slice(0, 20).sort((a, b) => b.rank - a.rank).map(r =>
    `<span class="highlight-tag">
      ${escHtml(r.text)} <span style="opacity:.7">${Math.round(r.rank * 100)}%</span>
    </span>`
  ).join('');
}

function renderSafety(results) {
  return results.slice(0, 10).map(r =>
    `<div style="font-size:13px;margin-bottom:4px"><strong>${r.label}</strong>: ${Math.round(r.confidence * 100)}%</div>`
  ).join('');
}

function renderTopics(results) {
  return results.slice(0, 10).map(r =>
    `<div style="font-size:13px;margin-bottom:4px">${escHtml(r.labels?.map(l => l.label).join(' > ') || r.text || '')}</div>`
  ).join('');
}

function getTranslationResult(data) {
  // AssemblyAI returns translations in top-level "translated_texts" key
  // Format: { "en": "translated text...", "es": "texto traducido..." }
  const tt = data.translated_texts;
  if (tt && typeof tt === 'object' && Object.keys(tt).length) {
    // Normalize to { lang: { text: "..." } } format for consistent rendering
    const result = {};
    for (const [lang, val] of Object.entries(tt)) {
      result[lang] = typeof val === 'string' ? { text: val } : val;
    }
    return result;
  }
  return {};
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function msToTime(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  if (h) return `${h}:${pad(m%60)}:${pad(s%60)}`;
  return `${pad(m)}:${pad(s%60)}`;
}
function pad(n) { return String(n).padStart(2,'0'); }

/* ════════════════════════════════════════════
   DOWNLOADS
════════════════════════════════════════════ */
function downloadExport(format) {
  const useGemini = document.getElementById('useGeminiTitle')?.checked !== false;
  const titleParam = useGemini ? '' : '?title=file';
  const url = `/api/export/${state.transcriptId}/${format}${titleParam}`;
  const a = document.createElement('a');
  a.href = url;
  a.click();
}

async function downloadAllZip() {
  if (!state.transcriptId) return;
  const cfg = buildConfig();

  const formats = [
    'txt', 'docx', 'pdf', 'md', 'srt', 'vtt',
    'table_docx', 'table_pdf',
    'literary_txt', 'literary_docx',
    'interview_docx',
    'verbatim_txt', 'verbatim_docx',
    'paragraphs_txt', 'paragraphs_json',
    'sentences_txt', 'sentences_csv', 'sentences_srt',
    'words_json', 'words_csv',
  ];

  if (cfg.translation_languages?.length) {
    cfg.translation_languages.forEach(lang => {
      formats.push(`translation_${lang}_txt`);
      if (cfg.translation_utterance) formats.push(`translation_${lang}_srt`);
      formats.push(`bilingual_${lang}_txt`);
      formats.push(`bilingual_${lang}_docx`);
    });
  }

  if ($('entityDetection').checked) formats.push('entities_csv');

  toast('Building ZIP…', '');
  try {
    const r = await fetch(`/api/export/${state.transcriptId}/zip`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ formats, title_mode: document.getElementById('useGeminiTitle')?.checked === false ? 'file' : null }),
    });
    if (!r.ok) throw new Error('ZIP failed');
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript_${state.transcriptId}_bundle.zip`;
    a.click();
    URL.revokeObjectURL(url);
    toast('ZIP downloaded', 'success');
  } catch (err) {
    toast(err.message, 'error');
  }
}

/* ════════════════════════════════════════════
   HISTORY
════════════════════════════════════════════ */
const HISTORY_KEY = 'aai_history';

function saveToHistory(id, name) {
  const history = getHistory();
  history.unshift({ id, name: name || id, date: new Date().toISOString() });
  const trimmed = history.slice(0, 15);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
  renderHistory();
}

function getHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch { return []; }
}

function loadHistory() { renderHistory(); }

function renderHistory() {
  const list = $('historyList');
  const history = getHistory();
  if (!history.length) {
    list.innerHTML = '<p class="muted text-sm" style="padding:20px;text-align:center">No history yet.</p>';
    return;
  }
  list.innerHTML = history.map(item => `
    <div class="history-item" data-id="${item.id}">
      <div class="history-item-name">${escHtml(item.name)}</div>
      <div class="history-item-meta">${item.id} · ${new Date(item.date).toLocaleString()}</div>
    </div>`).join('');
  list.querySelectorAll('.history-item').forEach(el => {
    el.onclick = () => { $('resumeInput').value = el.dataset.id; resumeById(); };
  });
}

async function resumeById() {
  const id = $('resumeInput').value.trim();
  if (!id) { toast('Enter a transcript ID', 'error'); return; }
  try {
    const data = await apiGet(`/api/resume/${id}`);
    state.transcriptId = id;
    state.transcriptData = data;
    // Restore original filename from history, fallback to ID
    const historyItem = getHistory().find(h => h.id === id);
    state.fileName = (historyItem && historyItem.name !== id) ? historyItem.name : id;
    $('historyDrawer').style.display = 'none';
    renderResults(data);
    fetchGeminiAnalysis();
    toast('Transcript loaded', 'success');
  } catch (err) {
    toast(err.message, 'error');
  }
}

/* ════════════════════════════════════════════
   RESET
════════════════════════════════════════════ */
function resetAll() {
  state.fileId = null;
  state.fileName = null;
  state.transcriptId = null;
  state.transcriptData = null;
  state.geminiData = null;
  state.lastConfig = null;
  if (state.pollTimer) clearInterval(state.pollTimer);

  $('fileInput').value = '';
  $('urlInput').value = '';
  $('sourceStatus').style.display = 'none';
  $('btnToOptions').disabled = true;
  $('dlTranslation').style.display = 'none';
  $('dlRedacted').style.display = 'none';
  $('dlAnalytics').style.display = 'none';
  $('configPanel').style.display = 'none';
  $('analyticsPanels').innerHTML = '';
  $('transcriptBody').innerHTML = '';
  $('progressBar').style.width = '0%';

  showStep('step-source');
}
