const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const versionFilePath = path.join(__dirname, '..', 'VERSION');
const filesToUpdate = [
  path.join(__dirname, '..', 'muts-desktop', 'electron-ui', 'package.json'),
  path.join(__dirname, '..', 'backend', 'package.json'),
  path.join(__dirname, '..', 'pyproject.toml')
];

// Read current version
const currentVersion = fs.readFileSync(versionFilePath, 'utf8').trim();
const [major, minor, patch] = currentVersion.split('.').map(Number);

// Determine bump type (default: patch)
const bumpType = process.argv[2] || 'patch';
let newVersion;

switch(bumpType) {
  case 'major':
    newVersion = `${major + 1}.0.0`;
    break;
  case 'minor':
    newVersion = `${major}.${minor + 1}.0`;
    break;
  default: // patch
    newVersion = `${major}.${minor}.${patch + 1}`;
}

// Update VERSION file
fs.writeFileSync(versionFilePath, newVersion);

// Update version in target files
filesToUpdate.forEach(filePath => {
  if (fs.existsSync(filePath)) {
    let content = fs.readFileSync(filePath, 'utf8');

    if (filePath.endsWith('package.json')) {
      const pkg = JSON.parse(content);
      pkg.version = newVersion;
      content = JSON.stringify(pkg, null, 2) + '\n';
    } else if (filePath.endsWith('pyproject.toml')) {
      content = content.replace(
        /version = ".+?"/,
        `version = "${newVersion}"`
      );
    }

    fs.writeFileSync(filePath, content);
  }
});

// Create git tag
const tagName = `v${newVersion}`;
execSync(`git add ${versionFilePath} ${filesToUpdate.join(' ')}`);
execSync(`git commit -m "chore: bump version to ${newVersion}"`);
execSync(`git tag -a ${tagName} -m "Version ${newVersion}"`);

console.log(`Successfully bumped version to ${newVersion} and created tag ${tagName}`);
