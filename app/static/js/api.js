// Domus API Client with Offline Resilience

let currentToken = null;

async function initAuthToken() {
  const session = await getLocalSession();
  if (session && session.token) {
    currentToken = session.token;
    return session.member;
  }
  return null;
}

async function request(url, options = {}) {
  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (currentToken) {
    headers["Authorization"] = `Bearer ${currentToken}`;
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers
    });

    if (res.status === 401) {
      // Clear invalid session
      await clearLocalSession();
      currentToken = null;
      window.dispatchEvent(new CustomEvent("domus-unauthorized"));
      throw new Error("Unauthorized");
    }

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Request failed with status ${res.status}`);
    }

    if (res.status === 204) {
      return null;
    }

    return await res.json();
  } catch (err) {
    if (!navigator.onLine || err.message === "Failed to fetch" || err.message === "Unauthorized") {
      throw err;
    }
    throw err;
  }
}

const api = {
  // Profiles & Auth
  async getProfiles() {
    return await request("/api/auth/profiles");
  },

  async login(memberId, pin) {
    const res = await request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ member_id: memberId, pin })
    });
    currentToken = res.access_token;
    await saveLocalSession(res.access_token, res.member);
    return res.member;
  },

  // Timeline with Dexie offline fallback
  async getTimeline(dateStr, view = "all") {
    try {
      const data = await request(`/api/timeline?date=${dateStr}&view=${view}`);
      await cacheTimeline(dateStr, data);
      return { data, isOffline: false };
    } catch (err) {
      console.warn("Using offline timeline cache:", err);
      const cached = await getCachedTimeline(dateStr);
      if (cached) {
        return { data: cached, isOffline: true };
      }
      return {
        data: {
          date: dateStr,
          summary: { date: dateStr, total_tasks: 0, completed_tasks: 0, total_due_bills_amount: 0, total_spent_today: 0 },
          items: []
        },
        isOffline: true
      };
    }
  },

  // Logistics
  async createTask(taskData) {
    return await request("/api/tasks", {
      method: "POST",
      body: JSON.stringify(taskData)
    });
  },

  async toggleTask(taskId, isCompleted) {
    return await request(`/api/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_completed: isCompleted })
    });
  },

  async completeChore(choreId) {
    return await request(`/api/chores/${choreId}/complete`, {
      method: "POST"
    });
  },

  async getChores() {
    return await request("/api/chores");
  },

  async getNotes() {
    return await request("/api/notes");
  },

  async createNote(noteData) {
    return await request("/api/notes", {
      method: "POST",
      body: JSON.stringify(noteData)
    });
  },

  // Finances
  async createExpense(expenseData) {
    return await request("/api/expenses", {
      method: "POST",
      body: JSON.stringify(expenseData)
    });
  },

  async getExpenses() {
    return await request("/api/expenses");
  },

  async getBills() {
    return await request("/api/bills");
  },

  // Family Inbox
  async getInbox() {
    return await request("/api/inbox");
  },

  async getInboxCount() {
    return await request("/api/inbox/count");
  },

  async createInboxItem(data) {
    return await request("/api/inbox", {
      method: "POST",
      body: JSON.stringify(data)
    });
  },

  async uploadInboxFile(formData) {
    return await request("/api/inbox/upload", {
      method: "POST",
      body: formData
    });
  },

  async triageInboxItem(itemId, triageData) {
    return await request(`/api/inbox/${itemId}/triage`, {
      method: "POST",
      body: JSON.stringify(triageData)
    });
  },

  async dismissInboxItem(itemId) {
    return await request(`/api/inbox/${itemId}`, {
      method: "DELETE"
    });
  }
};
