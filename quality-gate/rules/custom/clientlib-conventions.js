#!/usr/bin/env node

/**
 * Custom Clientlib Conventions Checker for AEMaaCS
 *
 * Validates:
 * - Clientlib category naming conventions
 * - js.txt and css.txt file references
 * - embed vs. dependencies proper usage
 * - .content.xml structural correctness
 */

const fs = require('fs');
const path = require('path');

const results = {
  findings: [],
  summary: {
    blocker: 0,
    critical: 0,
    major: 0,
    minor: 0,
    info: 0,
  },
};

function addFinding(severity, ruleId, file, message) {
  results.findings.push({
    severity,
    ruleId,
    file,
    message,
  });
  results.summary[severity]++;
}

function findClientlibs(startPath) {
  const clientlibs = [];

  function walk(dir) {
    try {
      const files = fs.readdirSync(dir);

      for (const file of files) {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);

        if (file === '.content.xml' && stat.isFile()) {
          // Check if this is a clientlib
          const content = fs.readFileSync(filePath, 'utf8');
          if (content.includes('cq:ClientLibraryFolder')) {
            clientlibs.push(path.dirname(filePath));
          }
        } else if (stat.isDirectory() && !file.startsWith('.')) {
          walk(filePath);
        }
      }
    } catch (e) {
      // Silently skip inaccessible dirs
    }
  }

  walk(startPath);
  return clientlibs;
}

function validateClientlib(clientlibPath) {
  const contentXmlPath = path.join(clientlibPath, '.content.xml');

  if (!fs.existsSync(contentXmlPath)) {
    addFinding('major', 'clientlib-missing-content-xml', clientlibPath, 'Missing .content.xml');
    return;
  }

  let contentXml;
  try {
    contentXml = fs.readFileSync(contentXmlPath, 'utf8');
  } catch (e) {
    addFinding('critical', 'clientlib-content-xml-unreadable', contentXmlPath, `Cannot read: ${e.message}`);
    return;
  }

  // Extract category
  const categoryMatch = contentXml.match(/categories="([^"]*)"/);
  const categories = categoryMatch ? categoryMatch[1].split(',').map(c => c.trim()) : [];

  if (categories.length === 0) {
    addFinding('major', 'clientlib-category-naming', contentXmlPath, 'No categories defined');
  } else {
    categories.forEach(cat => {
      // Validate naming: should be lowercase with dots
      if (!/^[a-z0-9_][a-z0-9._-]*$/.test(cat)) {
        addFinding('major', 'clientlib-category-naming', contentXmlPath, `Invalid category name: ${cat} (should be lowercase with dots)`);
      }
    });
  }

  // Check for js.txt
  const jsTextPath = path.join(clientlibPath, 'js.txt');
  if (fs.existsSync(jsTextPath)) {
    validateFileReferences(jsTextPath, clientlibPath, 'js');
  }

  // Check for css.txt
  const cssTextPath = path.join(clientlibPath, 'css.txt');
  if (fs.existsSync(cssTextPath)) {
    validateFileReferences(cssTextPath, clientlibPath, 'css');
  }

  // Validate embed vs dependencies
  const embedMatch = contentXml.match(/embed="([^"]*)"/);
  const depsMatch = contentXml.match(/dependencies="([^"]*)"/);

  if (embedMatch && depsMatch) {
    const embeds = embedMatch[1].split(',').map(e => e.trim());
    const deps = depsMatch[1].split(',').map(d => d.trim());

    // Check for overlap (bad practice)
    const overlap = embeds.filter(e => deps.includes(e));
    if (overlap.length > 0) {
      addFinding('major', 'clientlib-embed-vs-dependencies', contentXmlPath,
        `Clientlib appears in both embed and dependencies: ${overlap.join(', ')}`);
    }
  }

  // Validate allowProxy attribute
  const allowProxyMatch = contentXml.match(/allowProxy="([^"]*)"/);
  if (!allowProxyMatch) {
    addFinding('minor', 'clientlib-allow-proxy', contentXmlPath, 'Missing allowProxy attribute (recommend true)');
  }
}

function validateFileReferences(filePath, clientlibPath, type) {
  let fileList;
  try {
    fileList = fs.readFileSync(filePath, 'utf8').split('\n');
  } catch (e) {
    addFinding('critical', 'clientlib-file-unreadable', filePath, `Cannot read: ${e.message}`);
    return;
  }

  fileList.forEach(line => {
    line = line.trim();
    if (!line || line.startsWith('#')) return;

    const fullPath = path.join(clientlibPath, line);
    if (!fs.existsSync(fullPath)) {
      addFinding('major', 'clientlib-file-references', filePath,
        `Referenced file not found: ${line}`);
    }
  });
}

// Main execution
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node clientlib-conventions.js <path-to-ui.apps>');
  process.exit(1);
}

const uiAppsPath = args[0];

if (!fs.existsSync(uiAppsPath)) {
  console.error(`Path not found: ${uiAppsPath}`);
  process.exit(1);
}

const clientlibs = findClientlibs(uiAppsPath);

if (clientlibs.length === 0) {
  console.log('No clientlibs found in', uiAppsPath);
  process.stdout.write(JSON.stringify(results, null, 2));
  process.exit(0);
}

clientlibs.forEach(clientlibPath => {
  validateClientlib(clientlibPath);
});

// Output results
process.stdout.write(JSON.stringify(results, null, 2));

// Exit with error code if any blockers/critical found
const exitCode = results.summary.blocker > 0 || results.summary.critical > 0 ? 1 : 0;
process.exit(exitCode);
