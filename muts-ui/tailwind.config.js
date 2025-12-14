/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./index.html"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Sci-fi Dylan theme colors
        cyan: {
          50: 'rgba(6, 182, 212, 0.05)',
          100: 'rgba(6, 182, 212, 0.10)',
          200: 'rgba(6, 182, 212, 0.20)',
          300: 'rgba(6, 182, 212, 0.30)',
          400: 'rgba(6, 182, 212, 0.40)',
          500: 'rgba(6, 182, 212, 0.50)',
          600: 'rgba(6, 182, 212, 0.60)',
          700: 'rgba(6, 182, 212, 0.70)',
          800: 'rgba(6, 182, 212, 0.80)',
          900: 'rgba(6, 182, 212, 0.90)',
          950: 'rgba(6, 182, 212, 0.95)',
          DEFAULT: '#06b6d4',
        },
        violet: {
          50: 'rgba(217, 70, 239, 0.05)',
          100: 'rgba(217, 70, 239, 0.10)',
          200: 'rgba(217, 70, 239, 0.20)',
          300: 'rgba(217, 70, 239, 0.30)',
          400: 'rgba(217, 70, 239, 0.40)',
          500: 'rgba(217, 70, 239, 0.50)',
          600: 'rgba(217, 70, 239, 0.60)',
          700: 'rgba(217, 70, 239, 0.70)',
          800: 'rgba(217, 70, 239, 0.80)',
          900: 'rgba(217, 70, 239, 0.90)',
          950: 'rgba(217, 70, 239, 0.95)',
          DEFAULT: '#d946ef',
        },
        fuchsia: {
          DEFAULT: '#d946ef',
        },
        red: {
          50: 'rgba(239, 68, 68, 0.05)',
          100: 'rgba(239, 68, 68, 0.10)',
          200: 'rgba(239, 68, 68, 0.20)',
          300: 'rgba(239, 68, 68, 0.30)',
          400: 'rgba(239, 68, 68, 0.40)',
          500: 'rgba(239, 68, 68, 0.50)',
          600: 'rgba(239, 68, 68, 0.60)',
          700: 'rgba(239, 68, 68, 0.70)',
          800: 'rgba(239, 68, 68, 0.80)',
          900: 'rgba(239, 68, 68, 0.90)',
          950: 'rgba(239, 68, 68, 0.95)',
          DEFAULT: '#ef4444',
        },
        amber: {
          50: 'rgba(245, 158, 11, 0.05)',
          100: 'rgba(245, 158, 11, 0.10)',
          200: 'rgba(245, 158, 11, 0.20)',
          300: 'rgba(245, 158, 11, 0.30)',
          400: 'rgba(245, 158, 11, 0.40)',
          500: 'rgba(245, 158, 11, 0.50)',
          600: 'rgba(245, 158, 11, 0.60)',
          700: 'rgba(245, 158, 11, 0.70)',
          800: 'rgba(245, 158, 11, 0.80)',
          900: 'rgba(245, 158, 11, 0.90)',
          950: 'rgba(245, 158, 11, 0.95)',
          DEFAULT: '#f59e0b',
        },
        green: {
          50: 'rgba(34, 197, 94, 0.05)',
          100: 'rgba(34, 197, 94, 0.10)',
          200: 'rgba(34, 197, 94, 0.20)',
          300: 'rgba(34, 197, 94, 0.30)',
          400: 'rgba(34, 197, 94, 0.40)',
          500: 'rgba(34, 197, 94, 0.50)',
          600: 'rgba(34, 197, 94, 0.60)',
          700: 'rgba(34, 197, 94, 0.70)',
          800: 'rgba(34, 197, 94, 0.80)',
          900: 'rgba(34, 197, 94, 0.90)',
          950: 'rgba(34, 197, 94, 0.95)',
          DEFAULT: '#22c55e',
        },
        rose: {
          50: 'rgba(244, 63, 94, 0.05)',
          100: 'rgba(244, 63, 94, 0.10)',
          200: 'rgba(244, 63, 94, 0.20)',
          300: 'rgba(244, 63, 94, 0.30)',
          400: 'rgba(244, 63, 94, 0.40)',
          500: 'rgba(244, 63, 94, 0.50)',
          600: 'rgba(244, 63, 94, 0.60)',
          700: 'rgba(244, 63, 94, 0.70)',
          800: 'rgba(244, 63, 94, 0.80)',
          900: 'rgba(244, 63, 94, 0.90)',
          950: 'rgba(244, 63, 94, 0.95)',
          DEFAULT: '#f43f5e',
        },
        // Background colors
        'bg-primary': 'rgba(15, 23, 42, 1)', // slate-950
        'bg-secondary': 'rgba(30, 41, 59, 1)', // slate-800
        'bg-panel': 'rgba(30, 41, 59, 0.8)', // slate-900/80
        'bg-glass': 'rgba(30, 41, 59, 0.5)', // slate-900/50
        'bg-overlay': 'rgba(0, 0, 0, 0.4)', // black/40
        'bg-scanline': 'rgba(18, 16, 16, 0.5)', // custom scanline color
        // Text colors
        'text-primary': 'rgba(248, 250, 252, 1)', // slate-50
        'text-secondary': 'rgba(203, 213, 225, 1)', // slate-300
        'text-tertiary': 'rgba(148, 163, 184, 1)', // slate-400
        'text-muted': 'rgba(100, 116, 139, 1)', // slate-500
      },
      backgroundImage: {
        'scanline': 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%)',
        'scanline-grid': 'linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
        'gradient-cyan-violet': 'linear-gradient(to right, rgba(6, 182, 212, 1), rgba(217, 70, 239, 1))',
        'sync-gradient': 'linear-gradient(to bottom, rgba(6, 182, 212, 1), rgba(255, 255, 255, 1), rgba(217, 70, 239, 1))',
        'ambient-glow': 'radial-gradient(ellipse at center, rgba(30, 41, 59, 1), rgba(0, 0, 0, 1))',
        'holo-cyan': 'linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(6, 182, 212, 0.05))',
        'holo-violet': 'linear-gradient(135deg, rgba(217, 70, 239, 0.1), rgba(217, 70, 239, 0.05))',
        'holo-red': 'linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05))',
        'holo-amber': 'linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05))',
        'holo-green': 'linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05))',
        'holo-rose': 'linear-gradient(135deg, rgba(244, 63, 94, 0.1), rgba(244, 63, 94, 0.05))',
      },
      boxShadow: {
        'glow-cyan': '0 0 15px rgba(6, 182, 212, 0.15)',
        'glow-violet': '0 0 15px rgba(217, 70, 239, 0.15)',
        'glow-red': '0 0 15px rgba(239, 68, 68, 0.15)',
        'glow-amber': '0 0 15px rgba(245, 158, 11, 0.15)',
        'glow-green': '0 0 15px rgba(34, 197, 94, 0.15)',
        'glow-rose': '0 0 15px rgba(244, 63, 94, 0.15)',
        'glow-active-cyan': '0 0 20px rgba(6, 182, 212, 0.4)',
        'glow-active-violet': '0 0 20px rgba(217, 70, 239, 0.4)',
        'glow-active-red': '0 0 20px rgba(239, 68, 68, 0.4)',
        'glow-active-amber': '0 0 20px rgba(245, 158, 11, 0.4)',
        'glow-active-green': '0 0 20px rgba(34, 197, 94, 0.4)',
        'glow-active-rose': '0 0 20px rgba(244, 63, 94, 0.4)',
      },
      backdropBlur: {
        'holo': '8px',
      },
      fontFamily: {
        'mono': ['"Fira Code"', '"SF Mono"', 'Monaco', '"Cascadia Code"', '"Roboto Mono"', 'Consolas', '"Courier New"', 'monospace'],
      },
      animation: {
        'scan': 'scan 2s linear infinite',
        'pulse-slow': 'pulse 6s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 20s linear infinite',
        'spin-fast': 'spin 3s linear infinite',
      },
      keyframes: {
        slideUp: {
          'from': { transform: 'translateY(10px)', opacity: '0' },
          'to': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}