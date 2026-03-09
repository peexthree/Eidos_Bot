const fs = require('fs');

const file = 'frontend_v2/src/pages/Hub.jsx';
let content = fs.readFileSync(file, 'utf8');

// Ensure ProfileHeader import
if (!content.includes('import ProfileHeader')) {
    content = content.replace("import axios from 'axios';", "import axios from 'axios';\nimport ProfileHeader from '../components/ProfileHeader';");
}

// Replace nadpis (Title)
content = content.replace(
  /<img\s+src="\/video\/nadpis\.png"[^>]*\/>/g,
  `<img src="/video/nadpis.png" style={{ position: 'absolute', top: '3%', left: '10%', width: '80%', objectFit: 'contain', zIndex: 10, pointerEvents: 'none' }} />`
);

// Add Profile under Title if it doesn't exist
const profileHtml = `\n        {/* Profile Wrapper */}\n        <div style={{ position: 'absolute', top: '1%', left: '0', right: '0', zIndex: 50, transform: 'scale(0.60)', transformOrigin: 'top center', pointerEvents: 'none', backgroundColor: 'transparent' }}>\n          <ProfileHeader />\n        </div>`;

if (!content.includes('ProfileHeader />')) {
    const nadpisTagStr = `<img src="/video/nadpis.png" style={{ position: 'absolute', top: '3%', left: '10%', width: '80%', objectFit: 'contain', zIndex: 10, pointerEvents: 'none' }} />`;
    content = content.replace(nadpisTagStr, nadpisTagStr + profileHtml);
}

// Replace sinxr (Brain)
content = content.replace(
  /<img\s+src="\/video\/sinxr\.png"\s+className=\{btnHoverActiveStyle\}\s+style=\{\{[^}]+\}\}\s+onClick=\{[^}]+\}\s*\/>/g,
  `<img\n          src="/video/sinxr.png"\n          className={btnHoverActiveStyle}\n          style={{ position: 'absolute', top: '15%', left: '33%', width: '34%', cursor: 'pointer', zIndex: 10 }}\n          onClick={() => handleAction(null, '/api/action/synchron')}\n        />`
);

fs.writeFileSync(file, content);
console.log('patched');
