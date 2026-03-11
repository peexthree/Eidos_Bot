const fs = require('fs');

const appFile = 'frontend_v2/src/App.jsx';
let content = fs.readFileSync(appFile, 'utf8');

const targetStr = `        <Layout>
          {renderView()}
        </Layout>`;

const replacementStr = `        <Layout>
          {renderView()}
          {/* GLOBAL UI FRAME (Hidden on Start/Loading screen) */}
          {currentView !== 'INTRO' && currentView !== 'LOADING' && (
            <img
              src="/video/frame.png"
              style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                objectFit: 'fill',
                zIndex: 9999,
                pointerEvents: 'none'
              }}
              alt="UI Frame"
            />
          )}
        </Layout>`;

if (content.includes(targetStr)) {
  content = content.replace(targetStr, replacementStr);
  fs.writeFileSync(appFile, content, 'utf8');
  console.log("App.jsx patched successfully!");
} else {
  console.log("Target string not found in App.jsx");
}
