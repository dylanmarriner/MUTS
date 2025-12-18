/**
 * React Renderer Entry Point
 * Main React application entry
 */

console.log('=== main.tsx starting ===');

import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import App from './App';
import './index.css';

// Declare the electronAPI on the window object
declare global {
  interface Window {
    electronAPI: import('./preload').ElectronAPI;
    hideBootScreen: () => void;
  }
}

// Hide boot screen and show React app
window.hideBootScreen = function() {
  console.log('React main.tsx: Hiding boot screen');
  document.body.classList.add('react-loaded');
};

// Main render function
const renderApp = () => {
  try {
    console.log('React main.tsx: Getting root element');
    const rootElement = document.getElementById('root');
    
    if (!rootElement) {
      console.error('React main.tsx: Root element not found!');
      // Show error in boot screen
      const statusText = document.getElementById('status-text');
      if (statusText) {
        statusText.textContent = 'Error: Root element not found';
      }
      // Don't render React if root element missing
      return;
    }
    
    console.log('React main.tsx: Creating React root');
    const root = ReactDOM.createRoot(rootElement);
    
    console.log('React main.tsx: Rendering App component');
    root.render(
      <React.StrictMode>
        <HashRouter>
          <App />
        </HashRouter>
      </React.StrictMode>
    );
    
    // Always hide boot screen after React renders (App component will handle startup screen)
    // Wait a bit longer to ensure CSS has loaded
    setTimeout(() => {
      // Hide boot screen first
      if (window.hideBootScreen) {
        console.log('React main.tsx: Hiding boot screen after render');
        window.hideBootScreen();
      }
      
      // Then verify UI is actually visible (not blank) after boot screen is hidden
      setTimeout(() => {
        const root = document.getElementById('root');
        if (root && root.children.length > 0) {
          const computedStyle = window.getComputedStyle(root);
          const bodyHasReactLoaded = document.body.classList.contains('react-loaded');
          const rootIsVisible = computedStyle.display !== 'none' && computedStyle.display !== '';
          const hasContent = root.innerHTML.trim().length > 0;
          
          if (bodyHasReactLoaded && rootIsVisible && hasContent) {
            if (window.electronAPI?.healthCheckpoint) {
              window.electronAPI.healthCheckpoint('UI_VISIBLE', 'UI rendered with visible content', 'PASS');
            }
          } else {
            if (window.electronAPI?.healthCheckpoint) {
              window.electronAPI.healthCheckpoint('UI_VISIBLE', 'UI rendered with visible content', 'FAIL', 
                `Root not visible: bodyHasReactLoaded=${bodyHasReactLoaded}, rootIsVisible=${rootIsVisible}, hasContent=${hasContent}`);
            }
          }
        } else {
          if (window.electronAPI?.healthCheckpoint) {
            window.electronAPI.healthCheckpoint('UI_VISIBLE', 'UI rendered with visible content', 'FAIL', 'Root element not found or has no children');
          }
        }
      }, 200); // Wait for CSS transition
    }, 500);
    
    console.log('React main.tsx: App rendered successfully');
    
    // Report renderer loaded successfully
    if (window.electronAPI?.healthCheckpoint) {
      window.electronAPI.healthCheckpoint('RENDERER_LOADED', 'Renderer script loaded and React rendered', 'PASS');
    }
  } catch (error) {
    console.error('React main.tsx: Failed to render app:', error);
    
    // Report renderer failure
    if (window.electronAPI?.healthCheckpoint) {
      window.electronAPI.healthCheckpoint('RENDERER_LOADED', 'Renderer script loaded and React rendered', 'FAIL', error instanceof Error ? error.message : String(error));
    }
    
    // Show error in boot screen
    const statusText = document.getElementById('status-text');
    const statusEl = document.getElementById('status');
    
    if (statusText && statusEl) {
      statusEl.classList.add('error');
      statusText.textContent = `Error: ${error instanceof Error ? error.message : 'Unknown error'}`;
    }
  }
};

// Call the render function
renderApp();
