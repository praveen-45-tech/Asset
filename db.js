// db.js — tiny JSON-file "database" (no external DB needed for the demo)
const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');

const DB_PATH = path.join(__dirname, 'db.json');

function seed() {
  const now = new Date().toISOString();
  const hash = (p) => bcrypt.hashSync(p, 8);
  return {
    users: [
      { id: 'u1', name: 'Ava Admin',      email: 'admin@assetflow.io', password: hash('admin123'), role: 'Admin',         dept: 'Operations', createdAt: now },
      { id: 'u2', name: 'Dave Head',      email: 'head@assetflow.io',  password: hash('pass123'),  role: 'Dept Head',     dept: 'Engineering', createdAt: now },
      { id: 'u3', name: 'Mia Manager',    email: 'mgr@assetflow.io',   password: hash('pass123'),  role: 'Asset Manager', dept: 'IT',          createdAt: now },
      { id: 'u4', name: 'Eli Employee',   email: 'emp@assetflow.io',   password: hash('pass123'),  role: 'Employee',      dept: 'Engineering', createdAt: now }
    ],
    assets: [
      { id: 'AF-0001', name: 'Dell Latitude 5440', category: 'Laptop', status: 'Available', dept: 'Engineering', purchaseDate: '2024-01-10', value: 85000, holderId: null, createdAt: now },
      { id: 'AF-0002', name: 'Room B2 - Conference', category: 'Room', status: 'Available', dept: 'Operations', purchaseDate: '2023-06-01', value: 0, holderId: null, createdAt: now },
      { id: 'AF-0003', name: 'HP LaserJet Pro', category: 'Printer', status: 'Available', dept: 'IT', purchaseDate: '2023-11-20', value: 22000, holderId: null, createdAt: now }
    ],
    allocations: [],
    transferRequests: [],
    bookings: [],
    maintenanceRequests: [],
    auditCycles: [],
    notifications: [],
    activityLog: [],
    _seq: { asset: 4, alloc: 1, transfer: 1, booking: 1, maint: 1, audit: 1, notif: 1, log: 1 }
  };
}

function load() {
  if (!fs.existsSync(DB_PATH)) {
    const data = seed();
    fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 2));
    return data;
  }
  return JSON.parse(fs.readFileSync(DB_PATH, 'utf-8'));
}

let db = load();

function save() {
  fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2));
}

function reset() {
  db = seed();
  save();
  return db;
}

function nextId(prefix, kind) {
  const n = db._seq[kind]++;
  save();
  return `${prefix}-${String(n).padStart(4, '0')}`;
}

module.exports = { get db() { return db; }, save, reset, nextId };
