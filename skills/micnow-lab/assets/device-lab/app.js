'use strict';

const $ = (id) => document.getElementById(id);
const all = (selector) => [...document.querySelectorAll(selector)];
const labels = {RightOption: '右 Option', LeftOption: '左 Option', Fn: 'Fn'};
const targets = {codex: 'Codex', workbuddy: 'WorkBuddy', general: '通用输入'};
const commandLabels = {
  'device.info': '识别设备', 'device.capabilities': '确认支持的功能',
  'device.status': '检查设备状态', 'config.get': '读取设备设置',
  'config.set': '保存设备设置', 'config.verify': '核验设备设置',
  'speak.press': '按下 Speak', 'speak.release': '松开 Speak',
  'speak.test': '完成模拟试说', 'lab.scenario': '切换模拟情况',
  'lab.permission': '允许模拟连接', 'setup': '自动设置',
};
const viewNames = {device: ['设置与使用', '我的 MicNow'], ai: ['一起完成设置', '连接 AI'], history: ['设备与 AI 的每一步', '设置记录']};
let state = null;
let token = '';
let connectionFile = '';
let clientScript = '';
let busy = false;
let online = false;
let editing = false;
let editingRevision = null;
let filter = 'all';
let historySignature = '';
let latestNotice = '';
let toastTimer;
let polling = false;
let connectionError = false;

function text(id, value) { $(id).textContent = value; }
function shortShortcut(value) { return labels[value] || value || '尚未设置'; }
function modeText(value) { return value === 'hold' ? '按住说，松开结束' : '按一下开始，再按一下结束'; }
function showToast(message) {
  text('toast', message); $('toast').hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('toast').hidden = true; }, 3500);
}
function showError(message) {
  text('error-message', message); $('error-banner').hidden = false;
}
function changeView(name, updateHash = true) {
  if (!viewNames[name]) name = 'device';
  all('.view').forEach((view) => { view.hidden = view.id !== 'view-' + name; });
  all('.navigation [data-view]').forEach((button) => {
    if (button.dataset.view === name) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
  text('page-eyebrow', viewNames[name][0]); text('page-title', viewNames[name][1]);
  if (updateHash) history.replaceState(null, '', '#' + name);
  if (name === 'history') renderHistory(true);
  window.scrollTo({top: 0, left: 0, behavior: 'instant'});
}
function requestId() { return 'web-' + (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2)); }
function applyEnvelope(payload) {
  if (payload.token) token = payload.token;
  if (payload.connection_file) connectionFile = payload.connection_file;
  if (payload.client_script) clientScript = payload.client_script;
  if (payload.state) { state = payload.state; online = true; render(); }
}
async function loadState() {
  if (polling || busy) return;
  polling = true;
  try {
    const response = await fetch('/api/state', {cache: 'no-store'});
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error?.message || '本地状态暂时无法读取。');
    if (connectionError) { $('error-banner').hidden = true; connectionError = false; }
    applyEnvelope(payload);
  } catch (error) {
    connectionError = true;
    online = false; renderConnection(); refreshDisabled();
    showError('本地服务未连接。已暂停操作，请保持连接程序运行后重试。');
  } finally { polling = false; }
}
async function post(path, body, allowFailure = false) {
  if (!online || !token) throw new Error('本地服务尚未连接，请先重试。');
  const response = await fetch(path, {
    method: 'POST', headers: {'Content-Type': 'application/json', 'X-MicNow-Token': token},
    body: JSON.stringify({...body, source: 'web'}),
  });
  const payload = await response.json();
  applyEnvelope(payload);
  if ((!response.ok || !payload.ok) && !allowFailure) {
    throw new Error(payload.result?.error?.message || payload.error?.message || '本次操作未完成，请查看设备状态。');
  }
  return payload;
}
const command = (name, args = {}, allowFailure = false) => post('/api/command', {id: requestId(), command: name, args}, allowFailure);
async function mutation(action, successMessage) {
  if (busy) return;
  busy = true; $('error-banner').hidden = true; refreshDisabled();
  try { await action(); if (successMessage) showToast(successMessage); }
  catch (error) { showError(error.message || '操作未完成，请重试。'); }
  finally { busy = false; refreshDisabled(); await loadState(); }
}
function refreshDisabled() {
  all('[data-mutation], [data-scenario], #settings-form button[type=submit]').forEach((button) => { button.disabled = busy || !online; });
  $('setup-button').classList.toggle('loading-label', busy);
  $('speak-button').disabled = busy || !online || !state?.verification?.config || !state?.connection?.connected;
  $('copy-prompt').disabled = !connectionFile || !online;
}
function renderConnection() {
  const connected = online && state?.connection?.connected;
  const pill = $('connection-pill');
  pill.classList.toggle('connected', !!connected); pill.classList.toggle('offline', !connected);
  pill.querySelector('span').textContent = !online ? '本地服务未连接' : connected ? 'MicNow 已连接' : state?.connection?.receiver ? '等待麦克风' : '设备已断开';
  if (!online) {
    $('speak-stage').classList.remove('listening');
    text('trial-badge', '状态待确认');
    $('trial-badge').classList.remove('passed');
    text('trial-instruction', '连接恢复后，再读取设备的最新状态。');
    text('verification-note', '本地服务未连接，当前设置状态待确认。');
    $('verification-note').className = 'verification-note failed';
    renderStep('step-device', 'error', '连接状态待确认', '恢复本地服务后继续');
    renderStep('step-config', '', '等待重新读取', '当前状态暂时无法核验');
    renderStep('step-trial', '', '连接后再试用', '等待设备的最新回应');
    text('trial-feedback-text', '等待重新连接');
    $('trial-feedback').classList.remove('passed');
  }
}
function renderStep(id, style, title, detail) {
  const element = $(id); element.className = 'journey-step ' + style;
  element.querySelector('strong').textContent = title;
  element.querySelector('small').textContent = detail;
}
function updateForm() {
  const config = state.config;
  if (!labels[config.shortcut] && config.shortcut) {
    let option = [...$('shortcut-select').options].find((item) => item.value === config.shortcut);
    if (!option) { option = document.createElement('option'); option.value = config.shortcut; option.textContent = config.shortcut; $('shortcut-select').append(option); }
  }
  $('shortcut-select').value = config.shortcut || state.known_shortcut || 'RightOption';
  $('target-select').value = config.target_app || 'codex';
  all('input[name=speak_mode]').forEach((input) => { input.checked = input.value === config.speak_mode; });
}
function setEditing(value) {
  if (value && !state) { showError('请等本地设备连接后再调整设置。'); return; }
  editing = value; $('settings-form').hidden = !value; $('settings-summary').hidden = value;
  $('edit-settings').setAttribute('aria-expanded', String(value));
  $('edit-settings').textContent = value ? '收起设置 ↑' : '调整设置 ↗';
  if (value) { updateForm(); editingRevision = state.revision; }
}
function render() {
  if (!state) return;
  renderConnection();
  const connected = state.connection.connected;
  const permission = state.connection.permission !== 'required';
  const verified = !!state.verification.config;
  const passed = !!state.verification.trial;
  const phase = state.workflow.phase;
  text('mode-summary', modeText(state.config.speak_mode));
  text('shortcut-summary', shortShortcut(state.config.shortcut));
  text('target-summary', targets[state.config.target_app] || state.config.target_app || '待选择');
  if (!editing) updateForm();
  const note = $('verification-note');
  note.className = 'verification-note' + (verified ? ' verified' : phase === 'blocked-readback' ? ' failed' : '');
  note.replaceChildren();
  const dot = document.createElement('span'); dot.className = 'status-dot'; note.append(dot);
  const noteText = document.createElement('span'); noteText.textContent = verified ? '本次模拟配置已保存，并已回读核验' : phase === 'blocked-readback' ? '回读不一致，设置尚未通过核验' : '设置尚未核验'; note.append(noteText);
  renderStep('step-device', connected && permission ? 'done' : 'error', connected ? permission ? '设备已连接' : '等待你授权' : '等待设备连接', connected ? permission ? '正在使用本地模拟设备' : '仅模拟一次授权' : state.connection.receiver ? '接收器在线，麦克风未连接' : '恢复后继续当前流程');
  renderStep('step-config', verified ? 'done' : connected && permission ? 'current' : '', verified ? '设置已核验' : '沿用你的习惯', verified ? shortShortcut(state.config.shortcut) + ' · ' + (state.config.speak_mode === 'hold' ? '按住说' : '按两次') : phase === 'blocked-readback' ? '回读不一致，请先处理' : '读取、保存，再核对');
  renderStep('step-trial', passed ? 'done' : verified ? 'current' : '', passed ? '模拟试用通过' : '按一下，试试看', passed ? '按键与样例反馈已确认' : verified ? '现在可以试按 Speak' : '核验后体验 Speak');
  text('trial-badge', passed ? '模拟已通过' : verified ? '可以试按' : '等待设置');
  $('trial-badge').classList.toggle('passed', passed);
  $('speak-stage').classList.toggle('listening', !!state.speak.active);
  text('trial-instruction', !connected ? '恢复连接后，再试一次。' : !verified ? '设置核验完成后，就可以试按。' : passed ? '收到设备回应。你可以继续调整并再次试用。' : '点击 Speak，完成一次模拟试用。');
  text('trial-feedback-text', passed && state.trial?.text ? state.trial.text : phase === 'waiting-audio' ? '没有收到模拟声音，请检查后重试' : '等待模拟输入');
  $('trial-feedback').classList.toggle('passed', passed);
  const commands = state.commands || [];
  const latest = commands.at(-1);
  const latestText = latest ? (latest.source === 'agent' ? 'AI · ' : 'Web · ') + (commandLabels[latest.command] || latest.command) + ' · ' + humanResult(latest) : '还没有操作。可以自己设置，也可以让 AI 来完成。';
  text('latest-activity', latestText);
  if (latestText !== latestNotice) { text('live-status', latestText); latestNotice = latestText; }
  text('history-count', String(commands.length));
  const agentCalled = commands.some((item) => item.source === 'agent' && item.ok);
  text('codex-status', agentCalled ? '已收到 AI 指令' : '等待本地调用');
  $('agent-evidence').classList.toggle('verified', agentCalled);
  $('agent-evidence').querySelector('span:last-child').textContent = agentCalled ? '已经收到 AI 的实际指令与设备回执。可回到设备页查看结果。' : '等待 AI 第一次调用。本页不会代替 AI 生成回复。';
  text('agent-prompt', connectionFile ? '使用已安装的 micnow-lab Skill 连接当前 MicNow 模拟设备，沿用我的使用习惯，完成设置并回读核验。请把执行结果同步到这个页面，继续使用当前会话。' : '正在准备当前会话的连接指令…');
  text('transport-label', state.connection.label || '本地模拟连接');
  text('revision-label', 'v' + state.revision + (verified ? ' · 已核验' : ' · 待核验'));
  text('session-label', state.session_id ? state.session_id.slice(0, 12) : '—');
  all('[data-scenario]').forEach((button) => { button.classList.toggle('active', button.dataset.scenario === state.scenario); });
  if (latest) text('raw-response', JSON.stringify({request: latest.request, response: latest.response}, null, 2));
  else text('raw-response', '尚无指令。');
  renderRecovery(); renderHistory(); refreshDisabled();
}
function renderRecovery() {
  const phase = state.workflow.phase;
  const recoveries = {
    'waiting-connection': ['先把模拟麦克风连上', state.connection.receiver ? '接收器已经在线。恢复麦克风后，我们继续核验。' : '模拟设备已断开。恢复连接后，会重新确认设置。', '恢复模拟连接'],
    'waiting-permission': ['允许这次模拟连接', '这一步只演练授权流程，不改变系统的真实权限。', '允许模拟连接'],
    'blocked-readback': ['设置还没有核验通过', '设备返回的设置与目标不同。已停止继续写入，先恢复正常环境再试。', '恢复正常并核验'],
    'waiting-audio': ['暂时没有模拟声音', '恢复声音演练后，需要再按一次 Speak。', '恢复模拟声音'],
    'partial': ['这个应用还未完成适配', '可以切换到通用输入继续模拟，当前不代表真实应用已接入。', '恢复正常环境'],
  };
  const item = recoveries[phase];
  $('recovery-card').hidden = !item;
  if (item) { text('recovery-title', item[0]); text('recovery-message', item[1]); text('recovery-button', item[2]); }
}
function humanResult(record) {
  if (!record.ok) return record.message || '未完成';
  if (record.command === 'config.set') return '模拟设备已保存';
  if (record.command === 'speak.test') return '模拟样例已返回';
  if (record.command === 'config.get') return '已收到设备设置';
  return '已收到设备回执';
}
function icon(name) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', '#i-' + name); svg.append(use); return svg;
}
function renderHistory(force = false) {
  if (!state) return;
  const records = (state.commands || []).filter((item) => filter === 'all' || item.source === filter).slice().reverse();
  const signature = state.session_id + filter + records.map((item) => item.request_id + item.status).join('|');
  if (!force && signature === historySignature) return;
  historySignature = signature;
  text('record-count', records.length + ' 条操作');
  const list = $('history-list'); list.replaceChildren();
  if (!records.length) {
    const empty = document.createElement('div'); empty.className = 'empty-state'; empty.append(icon('history'));
    const title = document.createElement('h3'); title.textContent = filter === 'agent' ? '等待 AI 的第一条指令。' : '第一条记录，从你开始。';
    const message = document.createElement('p'); message.textContent = filter === 'agent' ? '到「连接 AI」复制指令，在当前对话里继续。' : '完成一次设置，设备的回应就会出现在这里。';
    const button = document.createElement('button'); button.className = 'button secondary'; button.textContent = filter === 'agent' ? '连接 AI' : '返回设备'; button.addEventListener('click', () => changeView(filter === 'agent' ? 'ai' : 'device'));
    empty.append(title, message, button); list.append(empty); return;
  }
  records.forEach((record) => {
    const row = document.createElement('article'); row.className = 'record' + (record.ok ? '' : ' error');
    const mark = document.createElement('div'); mark.className = 'record-icon'; mark.append(icon(record.source === 'agent' ? 'spark' : 'device'));
    const main = document.createElement('div'); main.className = 'record-main';
    const head = document.createElement('div'); head.className = 'record-head';
    const title = document.createElement('strong'); title.textContent = commandLabels[record.command] || record.command;
    const source = document.createElement('span'); source.className = 'record-source'; source.textContent = record.source === 'agent' ? 'AI' : 'WEB'; head.append(title, source);
    const message = document.createElement('p'); message.textContent = humanResult(record);
    const detail = document.createElement('details'); const summary = document.createElement('summary'); summary.textContent = '查看设备回执';
    const raw = document.createElement('pre'); raw.textContent = JSON.stringify({request: record.request, response: record.response}, null, 2); detail.append(summary, raw);
    main.append(head, message, detail);
    const time = document.createElement('time');
    const date = new Date(typeof record.at === 'number' ? record.at * 1000 : record.at);
    time.textContent = Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false});
    if (!Number.isNaN(date.getTime())) time.dateTime = date.toISOString();
    row.append(mark, main, time); list.append(row);
  });
}

all('[data-view]').forEach((button) => button.addEventListener('click', () => changeView(button.dataset.view)));
all('[data-open-ai]').forEach((button) => button.addEventListener('click', () => changeView('ai')));
$('open-manual').addEventListener('click', () => { setEditing(true); $('settings-card').scrollIntoView({behavior: 'smooth', block: 'center'}); });
$('edit-settings').addEventListener('click', () => setEditing(!editing));
$('cancel-edit').addEventListener('click', () => setEditing(false));
$('settings-form').addEventListener('submit', (event) => {
  event.preventDefault();
  mutation(async () => {
    const patch = {shortcut: $('shortcut-select').value, speak_mode: document.querySelector('input[name=speak_mode]:checked').value, target_app: $('target-select').value};
    const expected = {...state.config, ...patch};
    const response = await command('config.set', {patch, expected_revision: editingRevision}, true);
    const error = response.result?.error || response.error;
    if (!response.ok && error?.code !== 'RESPONSE_TIMEOUT') throw new Error(error?.message || '设置未保存，请检查设备状态。');
    await command('config.verify', {expected_config: expected});
    setEditing(false);
  }, '本次模拟设置已保存并核验。');
});
$('setup-button').addEventListener('click', () => mutation(async () => {
  await post('/api/setup', {id: requestId()});
}, '配置已核验，可以试按 Speak。'));
$('speak-button').addEventListener('click', () => mutation(async () => {
  await command('speak.press');
  try { await command('speak.test'); }
  finally {
    await command('speak.release');
    if (state.config.speak_mode === 'toggle' && state.speak.active) {
      await command('speak.press');
      await command('speak.release');
    }
  }
}, '模拟试说完成，没有采集真实声音。'));
all('[data-scenario]').forEach((button) => button.addEventListener('click', () => mutation(async () => {
  await command('lab.scenario', {name: button.dataset.scenario});
}, '已切换模拟情况，请查看设备状态。')));
$('recovery-button').addEventListener('click', () => mutation(async () => {
  const phase = state.workflow.phase;
  if (phase === 'waiting-permission') await command('lab.permission', {allow: true});
  else await command('lab.scenario', {name: 'ready'});
  await post('/api/setup', {id: requestId()});
}, '配置已重新核验，请再试按 Speak。'));
$('reset-button').addEventListener('click', () => mutation(async () => {
  await post('/api/reset', {}); setEditing(false); historySignature = ''; renderHistory(true);
}, '已开启新的模拟会话。'));
$('show-codex').addEventListener('click', () => { $('connect-guide').scrollIntoView({behavior: 'smooth', block: 'start'}); $('copy-prompt').focus({preventScroll: true}); });
$('copy-prompt').addEventListener('click', async () => {
  const prompt = $('agent-prompt').textContent + '\n\n本机会话连接文件：' + connectionFile + '\n调用工具：' + clientScript + '\n只操作本次模拟设备，不修改真实硬件或应用。';
  try { await navigator.clipboard.writeText(prompt); showToast('已复制。发给能执行本地命令的当前助手。'); }
  catch (_) {
    const area = document.createElement('textarea'); area.value = prompt; area.style.cssText = 'position:fixed;left:-9999px'; document.body.append(area); area.select();
    let copied = false; try { copied = document.execCommand('copy'); } catch (_) { /* Browser may disallow clipboard. */ } area.remove();
    if (copied) showToast('已复制。发给能执行本地命令的当前助手。');
    else showError('浏览器未允许复制。请在当前对话中说“连接当前 MicNow 模拟会话”。');
  }
});
all('[data-provider]').forEach((button) => button.addEventListener('click', () => {
  $('provider-note').hidden = false;
  text('provider-note', button.dataset.provider === 'WorkBuddy' ? 'WorkBuddy 可通过项目 .codebuddy/skills 目录或技能 ZIP 安装。需要本机 Python 和本地命令执行权限；安装方法见 GitHub 仓库，客户端体验仍待实测。' : '请按 GitHub 仓库中的客户端安装说明加载同一份 Skill。助手必须能执行本机命令并访问当前 localhost；普通云端聊天不能直接连接这个页面。');
  $('provider-note').scrollIntoView({behavior: 'smooth', block: 'nearest'});
}));
all('[data-filter]').forEach((button) => button.addEventListener('click', () => {
  filter = button.dataset.filter; all('[data-filter]').forEach((item) => item.setAttribute('aria-pressed', String(item === button))); renderHistory(true);
}));
$('retry-connection').addEventListener('click', async () => { $('error-banner').hidden = true; await loadState(); });
$('dismiss-error').addEventListener('click', () => { $('error-banner').hidden = true; });
window.addEventListener('hashchange', () => changeView(location.hash.slice(1), false));
changeView(location.hash.slice(1) || 'device', false);
refreshDisabled();
loadState();
setInterval(() => { if (!document.hidden) loadState(); }, 1200);
document.addEventListener('visibilitychange', () => { if (!document.hidden) loadState(); });
