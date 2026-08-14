try {
    const db = require('./server/db.js');
    console.log('Books count:', db.getBooks().length);
    console.log('Chapter 1001 verses:', db.getChapterVerses(1001).verses.length);
    console.log('Search test:', db.searchVerses('태초에').total);
    console.log('SUCCESS!');
} catch (e) {
    console.error('Error detail:', e);
}
