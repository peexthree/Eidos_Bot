const fs = require('fs');
const content = fs.readFileSync('static/js/app.js', 'utf8');
if (content.includes('function renderDoll() {') && content.includes('data-slot-type')) {
  console.log("SUCCESS");
} else {
  console.log("FAILED");
}
