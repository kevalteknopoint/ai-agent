#!/usr/bin/env node

/**
 * Quality Gate Report Aggregator
 *
 * Parses all raw engine outputs and generates unified quality report
 * with normalized severities and dimension ratings (A-E).
 */

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node aggregate-report.js <reportsDir>');
  process.exit(1);
}

const reportsDir = args[0];

const severityLevelMap = {
  blocker: { rating: 'E', weight: 5 },
  critical: { rating: 'D', weight: 4 },
  major: { rating: 'C', weight: 3 },
  minor: { rating: 'B', weight: 2 },
  info: { rating: 'A', weight: 1 },
};

const findings = [];
const dimensionCounts = {
  'Java': { blocker: 0, critical: 0, major: 0, minor: 0, info: 0, totalWeight: 0 },
  'Sling/AEM': { blocker: 0, critical: 0, major: 0, minor: 0, info: 0, totalWeight: 0 },
  'HTL': { blocker: 0, critical: 0, major: 0, minor: 0, info: 0, totalWeight: 0 },
  'JavaScript': { blocker: 0, critical: 0, major: 0, minor: 0, info: 0, totalWeight: 0 },
  'CSS': { blocker: 0, critical: 0, major: 0, minor: 0, info: 0, totalWeight: 0 },
  'HTML': { blocker: 0, critical: 0, major: 0, minor: 0, info: 0, totalWeight: 0 },
};

function getRating(totalWeight) {
  // Scale: 0-5 = A, 5-15 = B, 15-30 = C, 30-50 = D, 50+ = E
  if (totalWeight === 0) return 'A';
  if (totalWeight < 5) return 'B';
  if (totalWeight < 15) return 'C';
  if (totalWeight < 30) return 'D';
  return 'E';
}

// Parse PMD report
const pmdPath = path.join(reportsDir, 'pmd-report.json');
if (fs.existsSync(pmdPath)) {
  try {
    const pmdData = JSON.parse(fs.readFileSync(pmdPath, 'utf8'));
    (pmdData.files || []).forEach(file => {
      (file.violations || []).forEach(v => {
        // Map PMD priority to severity
        const severity = v.priority <= 1 ? 'blocker'
          : v.priority === 2 ? 'critical'
          : v.priority === 3 ? 'major'
          : v.priority === 4 ? 'minor'
          : 'info';

        // Determine dimension based on rule name
        let dimension = 'Java';
        if (v.rule.includes('aem-') || v.rule.includes('Sling')) {
          dimension = 'Sling/AEM';
        }

        findings.push({
          engine: 'pmd',
          file: file.name,
          line: v.line,
          severity,
          ruleId: v.rule,
          message: v.message,
          dimension,
        });

        dimensionCounts[dimension][severity]++;
        dimensionCounts[dimension].totalWeight += severityLevelMap[severity].weight;
      });
    });
  } catch (e) {
    console.error('Error parsing PMD report:', e.message);
  }
}

// Parse Checkstyle report
const checkstylePath = path.join(reportsDir, 'checkstyle-report.xml');
if (fs.existsSync(checkstylePath)) {
  try {
    const xml = fs.readFileSync(checkstylePath, 'utf8');
    const fileRegex = /<file name="([^"]*)">[\s\S]*?<\/file>/g;
    const errorRegex = /<error line="(\d+)"[^>]*severity="([^"]*)"[^>]*message="([^"]*)"/g;

    let fileMatch;
    while ((fileMatch = fileRegex.exec(xml)) !== null) {
      const fileName = fileMatch[1];
      const fileContent = fileMatch[0];

      let errorMatch;
      const fileErrorRegex = /<error line="(\d+)"[^>]*severity="([^"]*)"[^>]*message="([^"]*)"/g;
      while ((errorMatch = fileErrorRegex.exec(fileContent)) !== null) {
        const severity = errorMatch[2] === 'error' ? 'critical' : 'minor';

        findings.push({
          engine: 'checkstyle',
          file: fileName,
          line: parseInt(errorMatch[1]),
          severity,
          ruleId: 'checkstyle',
          message: errorMatch[3],
          dimension: 'Java',
        });

        dimensionCounts['Java'][severity]++;
        dimensionCounts['Java'].totalWeight += severityLevelMap[severity].weight;
      }
    }
  } catch (e) {
    console.error('Error parsing Checkstyle report:', e.message);
  }
}

// Parse ESLint report
const eslintPath = path.join(reportsDir, 'eslint-report.json');
if (fs.existsSync(eslintPath)) {
  try {
    const eslintData = JSON.parse(fs.readFileSync(eslintPath, 'utf8'));
    eslintData.forEach(file => {
      (file.messages || []).forEach(msg => {
        const severity = msg.severity === 2 ? 'major' : msg.severity === 1 ? 'minor' : 'info';

        findings.push({
          engine: 'eslint',
          file: file.filePath,
          line: msg.line,
          column: msg.column,
          severity,
          ruleId: msg.ruleId || 'eslint',
          message: msg.message,
          dimension: 'JavaScript',
        });

        dimensionCounts['JavaScript'][severity]++;
        dimensionCounts['JavaScript'].totalWeight += severityLevelMap[severity].weight;
      });
    });
  } catch (e) {
    console.error('Error parsing ESLint report:', e.message);
  }
}

// Parse Stylelint report
const stylelintPath = path.join(reportsDir, 'stylelint-report.json');
if (fs.existsSync(stylelintPath)) {
  try {
    const stylelintData = JSON.parse(fs.readFileSync(stylelintPath, 'utf8'));
    stylelintData.forEach(file => {
      (file.warnings || []).forEach(warning => {
        const severity = warning.severity === 'error' ? 'major' : 'minor';

        findings.push({
          engine: 'stylelint',
          file: file.source,
          line: warning.line,
          column: warning.column,
          severity,
          ruleId: warning.rule,
          message: warning.text,
          dimension: 'CSS',
        });

        dimensionCounts['CSS'][severity]++;
        dimensionCounts['CSS'].totalWeight += severityLevelMap[severity].weight;
      });
    });
  } catch (e) {
    console.error('Error parsing Stylelint report:', e.message);
  }
}

// Parse Clientlib report
const clientlibPath = path.join(reportsDir, 'clientlib-report.json');
if (fs.existsSync(clientlibPath)) {
  try {
    const clientlibData = JSON.parse(fs.readFileSync(clientlibPath, 'utf8'));
    (clientlibData.findings || []).forEach(f => {
      findings.push({
        engine: 'custom',
        file: f.file,
        severity: f.severity,
        ruleId: f.ruleId,
        message: f.message,
        dimension: 'HTML',
      });

      dimensionCounts['HTML'][f.severity]++;
      dimensionCounts['HTML'].totalWeight += severityLevelMap[f.severity].weight;
    });
  } catch (e) {
    console.error('Error parsing Clientlib report:', e.message);
  }
}

// Generate aggregated report
const report = {
  summary: {
    totalFindings: findings.length,
    severityCounts: {
      blocker: Object.values(dimensionCounts).reduce((sum, d) => sum + d.blocker, 0),
      critical: Object.values(dimensionCounts).reduce((sum, d) => sum + d.critical, 0),
      major: Object.values(dimensionCounts).reduce((sum, d) => sum + d.major, 0),
      minor: Object.values(dimensionCounts).reduce((sum, d) => sum + d.minor, 0),
      info: Object.values(dimensionCounts).reduce((sum, d) => sum + d.info, 0),
    },
  },
  dimensionRatings: {},
  findings: findings.sort((a, b) => {
    const severityOrder = { blocker: 0, critical: 1, major: 2, minor: 3, info: 4 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  }),
};

// Calculate dimension ratings
for (const [dimension, counts] of Object.entries(dimensionCounts)) {
  const rating = getRating(counts.totalWeight);
  report.dimensionRatings[dimension] = {
    rating,
    findings: counts.blocker + counts.critical + counts.major + counts.minor + counts.info,
    blocker: counts.blocker,
    critical: counts.critical,
    major: counts.major,
    minor: counts.minor,
    info: counts.info,
  };
}

// Calculate overall rating
const totalWeight = Object.values(dimensionCounts).reduce((sum, d) => sum + d.totalWeight, 0);
const overallRating = getRating(totalWeight);
report.summary.overallRating = overallRating;

// Output as JSON
console.log(JSON.stringify(report, null, 2));
