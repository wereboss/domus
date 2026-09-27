// Domus Alpine.js Main Controller

document.addEventListener("alpine:init", () => {
  Alpine.data("domusApp", () => ({
    // Navigation & View State
    activeTab: "today",       // "inbox", "logistics", "today", "finances", "family"
    filterView: "all",        // "all", "mine"
    currentDate: new Date().toISOString().split("T")[0],
    todayDate: new Date().toISOString().split("T")[0],
    isOffline: !navigator.onLine,

    // PWA Installation & Environment State
    isStandalone: window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true,
    isIOS: /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream,
    canInstallPrompt: false,
    deferredInstallPrompt: null,
    showInstallBanner: false,

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

    // Family Inbox & Capture State
    inboxItems: [],
    inboxPendingCount: 0,
    isTriageOpen: false,
    selectedInboxItem: null,
    isUploadingInbox: false,
    triageForm: {
      target_type: "task",
      title: "",
      due_date: "",
      due_time: "",
      priority: "normal",
      assigned_to_id: null,
      amount: "",
      category: "General",
      content: ""
    },

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

      // PWA Installation Prompts
      if (!this.isStandalone && !localStorage.getItem("domus_install_dismissed")) {
        this.showInstallBanner = true;
      }
      window.addEventListener("beforeinstallprompt", (e) => {
        e.preventDefault();
        this.deferredInstallPrompt = e;
        this.canInstallPrompt = true;
        if (!this.isStandalone && !localStorage.getItem("domus_install_dismissed")) {
          this.showInstallBanner = true;
        }
      });

      // Initialize session, profiles, inbox badge, and timeline
      console.log("[Domus] Initializing application...");
      try {
        await this.initSession();
        await this.loadProfiles();
        await this.loadInboxCount();
        await this.loadTimeline();
        console.log("[Domus] App initialized successfully.", {
          member: this.currentMember?.name || "Guest",
          offline: this.isOffline,
          tab: this.activeTab,
          items: this.timeline.items.length
        });
      } catch (err) {
        console.error("[Domus] Error during initialization:", err);
      }
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
      await this.loadInboxCount();
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
      if (tab === "today") {
        this.currentDate = this.todayDate;
      }
      this.activeTab = tab;
      this.loadCurrentTab();
    },

    async loadCurrentTab() {
      if (this.activeTab === "today") {
        await this.loadTimeline();
      } else if (this.activeTab === "inbox") {
        await this.loadInbox();
      } else if (this.activeTab === "logistics") {
        this.chores = await api.getChores();
        this.notes = await api.getNotes();
      } else if (this.activeTab === "finances") {
        this.expenses = await api.getExpenses();
        this.bills = await api.getBills();
      }
      await this.loadInboxCount();
    },

    // ================= FAMILY INBOX & CAPTURE =================
    async loadInbox() {
      try {
        this.inboxItems = await api.getInbox();
        this.inboxPendingCount = this.inboxItems.length;
      } catch (err) {
        console.warn("Could not load inbox items:", err);
      }
    },

    async loadInboxCount() {
      try {
        const res = await api.getInboxCount();
        this.inboxPendingCount = res.pending_count;
      } catch (err) {
        console.warn("Could not fetch inbox count:", err);
      }
    },

    async pasteFromClipboard() {
      try {
        if (!navigator.clipboard || !navigator.clipboard.readText) {
          throw new Error("Clipboard API unavailable");
        }
        const text = await navigator.clipboard.readText();
        if (!text || !text.trim()) {
          alert("Clipboard is empty or contains no readable text.");
          return;
        }
        await api.createInboxItem({
          source: "clipboard",
          raw_content: text.trim(),
          title: text.trim().substring(0, 60)
        });
        await this.loadInbox();
        await this.loadInboxCount();
      } catch (err) {
        const manualText = prompt("Paste your link or text below:");
        if (manualText && manualText.trim()) {
          await api.createInboxItem({
            source: "manual_paste",
            raw_content: manualText.trim(),
            title: manualText.trim().substring(0, 60)
          });
          await this.loadInbox();
          await this.loadInboxCount();
        }
      }
    },

    async handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("file", file);
      this.isUploadingInbox = true;

      try {
        await api.uploadInboxFile(formData);
        await this.loadInbox();
        await this.loadInboxCount();
      } catch (err) {
        alert(err.message || "Failed to upload file. Ensure it is an image or PDF under 25MB.");
      } finally {
        this.isUploadingInbox = false;
        event.target.value = "";
      }
    },

    openTriage(item) {
      this.selectedInboxItem = item;
      this.triageForm = {
        target_type: "task",
        title: item.title || item.raw_content || "",
        due_date: this.todayDate,
        due_time: "",
        priority: "normal",
        assigned_to_id: this.currentMember ? this.currentMember.id : null,
        amount: "",
        category: "General",
        content: item.raw_content || (item.file_name ? `File: ${item.file_name}` : "")
      };
      this.isTriageOpen = true;
    },

    closeTriage() {
      this.isTriageOpen = false;
      this.selectedInboxItem = null;
    },

    async submitTriage() {
      if (!this.selectedInboxItem) return;
      this.isSubmitting = true;

      try {
        const payload = {
          target_type: this.triageForm.target_type,
          title: this.triageForm.title.trim(),
          due_date: this.triageForm.due_date || this.todayDate,
          due_time: this.triageForm.due_time || null,
          priority: this.triageForm.priority,
          assigned_to_id: this.triageForm.assigned_to_id ? parseInt(this.triageForm.assigned_to_id) : null,
          amount: this.triageForm.amount ? parseFloat(this.triageForm.amount) : null,
          category: this.triageForm.category,
          payment_method: "Card",
          content: this.triageForm.content
        };

        await api.triageInboxItem(this.selectedInboxItem.id, payload);
        this.closeTriage();
        await this.loadInbox();
        await this.loadInboxCount();
        await this.loadTimeline();
      } catch (err) {
        alert(err.message || "Failed to convert inbox item");
      } finally {
        this.isSubmitting = false;
      }
    },

    async dismissItem(item) {
      try {
        // Optimistic removal
        this.inboxItems = this.inboxItems.filter(i => i.id !== item.id);
        this.inboxPendingCount = Math.max(0, this.inboxPendingCount - 1);
        await api.dismissInboxItem(item.id);
      } catch (err) {
        console.error("Failed to dismiss inbox item:", err);
        await this.loadInbox();
      }
    },

    // ================= PWA INSTALLATION HELPERS =================
    dismissInstallBanner() {
      this.showInstallBanner = false;
      localStorage.setItem("domus_install_dismissed", "true");
    },

    async triggerAndroidInstall() {
      if (this.deferredInstallPrompt) {
        this.deferredInstallPrompt.prompt();
        const choiceResult = await this.deferredInstallPrompt.userChoice;
        if (choiceResult.outcome === "accepted") {
          this.showInstallBanner = false;
        }
        this.deferredInstallPrompt = null;
      }
    },

    // ================= TASK ACTIONS =================
    async toggleTask(item) {
      if (item.item_type !== "task") return;
      const taskId = parseInt(item.id.replace("task-", ""));
      
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
    },

    formatFileSize(bytes) {
      if (!bytes) return "";
      if (bytes < 1024) return bytes + " B";
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
      return (bytes / (1024 * 1024)).toFixed(1) + " MB";
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
