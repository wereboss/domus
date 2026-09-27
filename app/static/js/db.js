// Dexie.js Client Database for Domus Offline-First Operations
const db = new Dexie("DomusClientDB");

db.version(1).stores({
  timelines: "date, last_cached",
  profiles: "id, name",
  session: "key",
  offline_queue: "++id, url, method, timestamp"
});

// Helper to save session locally
async function saveLocalSession(token, member) {
  await db.session.put({ key: "current_session", token, member, saved_at: new Date().toISOString() });
}

// Helper to get session locally
async function getLocalSession() {
  return await db.session.get("current_session");
}

// Helper to clear session locally
async function clearLocalSession() {
  await db.session.delete("current_session");
}

// Helper to cache timeline
async function cacheTimeline(dateStr, data) {
  try {
    await db.timelines.put({
      date: dateStr,
      summary: data.summary,
      items: data.items,
      last_cached: new Date().toISOString()
    });
  } catch (err) {
    console.warn("Failed to cache timeline:", err);
  }
}

// Helper to retrieve cached timeline
async function getCachedTimeline(dateStr) {
  try {
    return await db.timelines.get(dateStr);
  } catch (err) {
    console.warn("Failed to read cached timeline:", err);
    return null;
  }
}
