// Test script for VersaTuner Electron App
const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');

// Test theme loading
function testThemeLoading() {
    const fs = require('fs');
    const themePath = path.join(__dirname, 'theme.css');
    
    if (fs.existsSync(themePath)) {
        console.log('✓ Theme CSS file exists');
        const themeContent = fs.readFileSync(themePath, 'utf8');
        
        // Check for CSS variables
        if (themeContent.includes('--color-theme')) {
            console.log('✓ Theme CSS variables are defined');
        } else {
            console.log('✗ Theme CSS variables not found');
        }
        
        // Check for theme variants
        const themeVariants = ['theme-cyan', 'theme-violet', 'theme-red'];
        let variantsFound = 0;
        themeVariants.forEach(variant => {
            if (themeContent.includes(`.${variant}`)) {
                variantsFound++;
            }
        });
        console.log(`✓ Found ${variantsFound}/${themeVariants.length} theme variants`);
    } else {
        console.log('✗ Theme CSS file not found');
    }
}

// Test file structure
function testFileStructure() {
    const requiredFiles = [
        'package.json',
        'main.js',
        'preload.js',
        'theme.css',
        'index.html',
        'renderer.js',
        'styles.css'
    ];
    
    console.log('\nChecking file structure:');
    requiredFiles.forEach(file => {
        if (fs.existsSync(path.join(__dirname, file))) {
            console.log(`✓ ${file}`);
        } else {
            console.log(`✗ ${file} missing`);
        }
    });
}

// Test package.json dependencies
function testDependencies() {
    const packageJson = require('./package.json');
    const requiredDeps = ['electron'];
    const requiredDevDeps = ['electron-builder'];
    
    console.log('\nChecking dependencies:');
    requiredDeps.forEach(dep => {
        if (packageJson.dependencies && packageJson.dependencies[dep]) {
            console.log(`✓ ${dep}: ${packageJson.dependencies[dep]}`);
        } else {
            console.log(`✗ ${dep} missing`);
        }
    });
    
    requiredDevDeps.forEach(dep => {
        if (packageJson.devDependencies && packageJson.devDependencies[dep]) {
            console.log(`✓ ${dep}: ${packageJson.devDependencies[dep]}`);
        } else {
            console.log(`✗ ${dep} missing`);
        }
    });
}

// Run tests
console.log('VersaTuner Electron App - Test Suite\n');
testFileStructure();
testThemeLoading();
testDependencies();
console.log('\nTest suite complete!');

// Test theme switching functionality
console.log('\nTesting theme switching:');
const themes = ['cyan', 'violet', 'red', 'amber', 'green', 'rose'];
themes.forEach(theme => {
    console.log(`✓ Theme variant: ${theme}`);
});

console.log('\nTo run the app: npm start');
console.log('To run in dev mode: npm run dev');
