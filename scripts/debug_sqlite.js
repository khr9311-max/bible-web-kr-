const fs = require('fs');
const path = require('path');

console.log('__dirname:', __dirname);
console.log('CWD:', process.cwd());
const dbPath = path.resolve(__dirname, '..', 'server', 'data', 'bible.db');
console.log('dbPath:', dbPath);
console.log('Exists:', fs.existsSync(dbPath));

const { DatabaseSync } = require('node:sqlite');
try {
    const db = new DatabaseSync(dbPath);
    console.log('DB created successfully');
    const stmt = db.prepare('SELECT count(*) as cnt FROM books');
    console.log('Stmt created');
    const res = stmt.get();
    console.log('Result:', res);
} catch (e) {
    console.error('ERROR in DatabaseSync:', e);
}
