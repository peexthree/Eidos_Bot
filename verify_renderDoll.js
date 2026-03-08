const fs = require('fs');
const content = fs.readFileSync('static/js/app.js', 'utf8');

if (content.includes("item.rarity === 'legendary'") && content.includes("overheatPulse") && content.includes("filter: drop-shadow")) {
    console.log("Visual excellence already implemented in step 1.");
} else {
    console.log("Needs update.");
}
