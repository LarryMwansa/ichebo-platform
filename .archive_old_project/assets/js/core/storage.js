// =========================
// ICS PLATFORM STORAGE LAYER
// =========================

const STORAGE_KEY = "ics_platform";

// =========================
// CORE STORAGE ENGINE
// =========================
const Storage = {
  // Initialize storage structure
  init() {
    if (!localStorage.getItem(STORAGE_KEY)) {
      const initialData = {
        session: null,
        user: null,
        apps: {
          users: [],
          records: [],
          activity: [],
          bible_notes: [],
        },
        settings: {
          theme: "light",
        },
        meta: {
          lastUpdated: new Date().toISOString(),
        },
      };

      localStorage.setItem(STORAGE_KEY, JSON.stringify(initialData));
    }
  },

  // Get full storage
  getAll() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
  },

  // Save full storage
  saveAll(data) {
    data.meta.lastUpdated = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  },
};

// =========================
// SESSION MANAGEMENT
// =========================
const Session = {
  set(user) {
    const data = Storage.getAll();
    data.session = {
      isAuthenticated: true,
      userId: user.id,
      loginTime: new Date().toISOString(),
    };
    data.user = user;
    Storage.saveAll(data);
  },

  get() {
    return Storage.getAll().session;
  },

  user() {
    return Storage.getAll().user;
  },

  isAuthenticated() {
    const session = this.get();
    return session && session.isAuthenticated;
  },

  clear() {
    const data = Storage.getAll();
    data.session = null;
    data.user = null;
    Storage.saveAll(data);
  },
};

// =========================
// APP DATA MANAGEMENT
// =========================
const AppStorage = {
  // Generic getter
  get(appName) {
    const data = Storage.getAll();
    return data.apps[appName] || [];
  },

  // Generic setter
  set(appName, items) {
    const data = Storage.getAll();
    data.apps[appName] = items;
    Storage.saveAll(data);
  },

  // Add item
  add(appName, item) {
    const data = Storage.getAll();
    const newItem = {
      id: this.generateId(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      ...item,
    };

    data.apps[appName].push(newItem);
    Storage.saveAll(data);
    return newItem;
  },

  // Update item
  update(appName, id, updates) {
    const data = Storage.getAll();
    const items = data.apps[appName];

    const index = items.findIndex((i) => i.id === id);
    if (index !== -1) {
      items[index] = {
        ...items[index],
        ...updates,
        updatedAt: new Date().toISOString(),
      };
      Storage.saveAll(data);
      return items[index];
    }

    return null;
  },

  // Delete item
  remove(appName, id) {
    const data = Storage.getAll();
    data.apps[appName] = data.apps[appName].filter((i) => i.id !== id);
    Storage.saveAll(data);
  },

  // Find one
  find(appName, id) {
    return this.get(appName).find((i) => i.id === id);
  },

  // Utility: ID generator
  generateId() {
    // For modern browsers, crypto.randomUUID() is a more robust and preferred option.
    if (window.crypto && window.crypto.randomUUID) {
      return window.crypto.randomUUID();
    }
    // Fallback for older browsers or non-secure contexts.
    // Adding timestamp for slightly better uniqueness.
    return (
      "id_" + Date.now().toString(36) + Math.random().toString(36).substr(2, 9)
    );
  },
};

// =========================
// SETTINGS MANAGEMENT
// =========================
const Settings = {
  get() {
    return Storage.getAll().settings;
  },

  set(updates) {
    const data = Storage.getAll();
    data.settings = {
      ...data.settings,
      ...updates,
    };
    Storage.saveAll(data);
  },
};

// =========================
// INITIALIZE ON LOAD
// =========================
Storage.init();

// =========================
// EXPORT (GLOBAL ACCESS)
// =========================
window.ICSStorage = {
  Storage,
  Session,
  AppStorage,
  Settings,
};

// RECORD STORAGE

export function getRecords() {
  return JSON.parse(localStorage.getItem("records")) || [];
}

export function saveRecords(records) {
  localStorage.setItem("records", JSON.stringify(records));
}
