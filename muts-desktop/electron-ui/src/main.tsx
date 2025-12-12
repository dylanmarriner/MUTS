/**
 * React Renderer Entry Point
 * Main React application entry
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

// Declare the electronAPI on the window object
declare global {
  interface Window {
    electronAPI: import('./preload').ElectronAPI;
    hideBootScreen: () => void;
  }
}

// Add debugging
console.log('React main.tsx: Starting to load');
console.log('React main.tsx: Window object:', window);
console.log('React main.tsx: electronAPI available:', !!window.electronAPI);

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
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </React.StrictMode>
    );
    
    console.log('React main.tsx: App rendered successfully');
  } catch (error) {
    console.error('React main.tsx: Failed to render app:', error);
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
