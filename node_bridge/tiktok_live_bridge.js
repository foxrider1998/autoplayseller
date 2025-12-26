#!/usr/bin/env node
// Tiny bridge: Use tiktok-live-connector to emit chat as NDJSON to stdout
let ConnectorCtor = null;
try {
  // CommonJS (0.9.x)
  const mod = require('tiktok-live-connector');
  ConnectorCtor = mod.WebcastPushConnection || mod.TikTokLiveConnection || mod.default?.TikTokLiveConnection || mod.default?.WebcastPushConnection || null;
} catch (e) {
  // ESM fallback
  try {
    const mod = await import('tiktok-live-connector');
    ConnectorCtor = mod.WebcastPushConnection || mod.TikTokLiveConnection || mod.default?.TikTokLiveConnection || mod.default?.WebcastPushConnection || null;
  } catch (e2) {
    console.error('Failed to load tiktok-live-connector:', e2?.message || e2);
    process.exit(1);
  }
}
if (!ConnectorCtor) {
  console.error('tiktok-live-connector does not export a compatible connector.');
  process.exit(1);
}

function getArg(flag, defVal) {
  const i = process.argv.indexOf(flag);
  if (i >= 0 && i + 1 < process.argv.length) return process.argv[i + 1];
  return defVal;
}

const uniqueId = getArg('--uniqueId', process.env.TIKTOK_UNIQUE_ID || '').trim();
if (!uniqueId) {
  console.error('Missing --uniqueId');
  process.exit(2);
}

const tiktok = new ConnectorCtor(uniqueId);

function emit(obj) {
  try { process.stdout.write(JSON.stringify(obj) + '\n'); } catch (e) {}
}

tiktok.connect().then(state => {
  emit({ type: 'status', status: 'connected', roomId: state.roomId });
}).catch(err => {
  emit({ type: 'status', status: 'error', message: String(err) });
  process.exit(1);
});

// Support both legacy and new event payloads
tiktok.on('chat', data => {
  emit({
    type: 'comment',
    comment: data.comment || data?.data?.comment || data?.text || '',
    msgId: data.msgId || data.eventId || data?.data?.msgId || undefined,
    user: { uniqueId: data.uniqueId || data?.user?.uniqueId, nickname: data.nickname || data?.user?.nickname },
    timestamp: Date.now()
  });
});

// Optional: basic logs suppressed to stdout; errors to stderr
tiktok.on('disconnected', () => emit({ type: 'status', status: 'disconnected' }));
