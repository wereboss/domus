// Domus Alpine.js Main Controller

document.addEventListener("alpine:init", () => {
  Alpine.data("domusApp", () => ({
    // Navigation & View State
    activeTab: "today",       // "today", "inbox", "logistics", "finances", "family"
    filterView: "all",        // "all", "mine"
    currentDate: new Date().toISOString().split("T")[0],
    todayDate: new Date().toISOString().split("T")[0],
    isOffline: !navigator.onLine,

    // Auth & Identity State
    currentMember: null,
    profiles: [],
    isPinModalOpen: false,
    selectedProfileForPin: null,
    enteredPin: "",
    pinError: "",

    // Data State
    timeline: {
      items: [],
      summary: { total_tasks: 0, completed_tasks: 0, total_due_bills_amount: 0, total_spent_today: 0 }
    },
    chores: [],
    notes: [],
    expenses: [],
    bills: [],

    // Quick-Add Bottom Sheet
    isAddOpen: false,
    addType: "task", // "task" | "expense"
    newTask: {
      title: "",
      due_time: "",
      priority: "normal",
      assigned_to_id: null
    },
    newExpense: {
      title: "",
      amount: "",
      category: "Groceries",
      payment_method: "Card"
    },
    isSubmitting: false,

    async init() {
      // Monitor online/offline events
      window.addEventListener("online", () => {
        this.isOffline = false;
        this.loadCurrentTab();
      });
      window.addEventListener("offline", () => {
        this.isOffline = true;
      });

      // Handle unauthorized events
      window.addEventListener("domus-unauthorized", () => {
        this.currentMember = null;
        this.openPinModal();
      });

      // Initialize session and profiles
      await this.initSession();
      await this.loadProfiles();
      await this.loadTimeline();
    },

    async initSession() {
      const member = await initAuthToken();
      if (member) {
        this.currentMember = member;
      }
    },

    async loadProfiles() {
      try {
        this.profiles = await api.getProfiles();
      } catch (err) {
        console.warn("Could not fetch profiles:", err);
      }
    },

    // ================= TIMELINE & NAVIGATION =================
    async loadTimeline() {
      const result = await api.getTimeline(this.currentDate, this.filterView);
      this.timeline = result.data;
      this.isOffline = result.isOffline;
    },

    setDate(offsetDays) {
      const d = new Date(this.currentDate);
      d.setDate(d.getDate() + offsetDays);
      this.currentDate = d.toISOString().split("T")[0];
      this.loadTimeline();
    },

    resetToToday() {
      this.currentDate = this.todayDate;
      this.loadTimeline();
    },

    setFilter(view) {
      this.filterView = view;
      this.loadTimeline();
    },

    switchTab(tab) {
      this.activeTab = tab;
      this.loadCurrentTab();
    },

    async loadCurrentTab() {
      if (this.activeTab === "today") {
        await this.loadTimeline();
      } else if (this.activeTab === "logistics") {
        this.chores = await api.getChores();
        this.notes = await api.getNotes();
      } else if (this.activeTab === "finances") {
        this.expenses = await api.getExpenses();
        this.bills = await api.getBills();
      }
    },

    // ================= TASK ACTIONS =================
    async toggleTask(item) {
      if (item.item_type !== "task") return;
      const taskId = parseInt(item.id.replace("task-", ""));
      
      // Optimistic local update
      const previousState = item.is_completed;
      item.is_completed = !previousState;
      if (item.is_completed) {
        this.timeline.summary.completed_tasks++;
      } else {
        this.timeline.summary.completed_tasks--;
      }

      try {
        await api.toggleTask(taskId, item.is_completed);
      } catch (err) {
        // Rollback on network failure
        item.is_completed = previousState;
        console.error("Task toggle failed:", err);
      }
    },

    async completeChoreItem(choreId) {
      try {
        await api.completeChore(choreId);
        await this.loadCurrentTab();
        await this.loadTimeline();
      } catch (err) {
        console.error("Chore completion failed:", err);
      }
    },

    // ================= QUICK-ADD BOTTOM SHEET =================
    openAddSheet(type = "task") {
      this.addType = type;
      this.newTask = {
        title: "",
        due_time: "",
        priority: "normal",
        assigned_to_id: this.currentMember ? this.currentMember.id : null
      };
      this.newExpense = {
        title: "",
        amount: "",
        category: "Groceries",
        payment_method: "Card"
      };
      this.isAddOpen = true;
    },

    closeAddSheet() {
      this.isAddOpen = false;
    },

    async submitQuickAdd() {
      if (this.isSubmitting) return;
      this.isSubmitting = true;

      try {
        if (this.addType === "task") {
          if (!this.newTask.title.trim()) return;
          await api.createTask({
            title: this.newTask.title.trim(),
            due_date: this.currentDate,
            due_time: this.newTask.due_time || null,
            priority: this.newTask.priority,
            assigned_to_id: this.newTask.assigned_to_id ? parseInt(this.newTask.assigned_to_id) : null
          });
        } else if (this.addType === "expense") {
          if (!this.newExpense.title.trim() || !this.newExpense.amount) return;
          await api.createExpense({
            title: this.newExpense.title.trim(),
            amount: parseFloat(this.newExpense.amount),
            category: this.newExpense.category,
            date: this.currentDate,
            payment_method: this.newExpense.payment_method,
            payer_member_id: this.currentMember ? this.currentMember.id : null
          });
        }

        this.closeAddSheet();
        await this.loadTimeline();
      } catch (err) {
        alert(err.message || "Failed to save entry");
      } finally {
        this.isSubmitting = false;
      }
    },

    // ================= PIN AUTH & PROFILE SWITCH =================
    openPinModal(profile = null) {
      this.selectedProfileForPin = profile || (this.profiles.length > 0 ? this.profiles[0] : null);
      this.enteredPin = "";
      this.pinError = "";
      this.isPinModalOpen = true;
    },

    closePinModal() {
      this.isPinModalOpen = false;
      this.enteredPin = "";
      this.pinError = "";
    },

    selectProfileForLogin(profile) {
      this.selectedProfileForPin = profile;
      this.enteredPin = "";
      this.pinError = "";
    },

    enterPinDigit(digit) {
      if (this.enteredPin.length < 8) {
        this.enteredPin += digit;
      }
      if (this.enteredPin.length === 4) {
        this.submitPin();
      }
    },

    deletePinDigit() {
      this.enteredPin = this.enteredPin.slice(0, -1);
      this.pinError = "";
    },

    async submitPin() {
      if (!this.selectedProfileForPin || !this.enteredPin) return;
      try {
        const member = await api.login(this.selectedProfileForPin.id, this.enteredPin);
        this.currentMember = member;
        this.closePinModal();
        await this.loadTimeline();
      } catch (err) {
        this.pinError = "Incorrect PIN";
        this.enteredPin = "";
      }
    },

    async logoutProfile() {
      await clearLocalSession();
      this.currentMember = null;
      await this.loadTimeline();
    },

    // Helpers
    formatCurrency(val) {
      if (val === null || val === undefined) return "$0.00";
      return "$" + Number(val).toFixed(2);
    },

    formatDisplayDate(dateStr) {
      if (!dateStr) return "";
      const d = new Date(dateStr + "T00:00:00");
      return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
    }
  }));
});

// Register service worker if supported
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.warn("ServiceWorker registration failed:", err);
    });
  });
}
