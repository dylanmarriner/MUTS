/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dylan Sci-fi Theme Colors
        'dylan-cyan': '#06b6d4',
        'dylan-violet': '#d946ef',
        'dylan-red': '#ef4444',
        'dylan-amber': '#f59e0b',
        'dylan-green': '#22c55e',
        'dylan-rose': '#f43f5e',
        // Legacy
        'mazda-red': '#B71234',
        'gray-950': '#030712',
      },
      backgroundImage: {
        'dylan-gradient': 'linear-gradient(to right, rgba(6, 182, 212, 1), rgba(217, 70, 239, 1))',
        'dylan-ambient': 'radial-gradient(ellipse at center, rgba(30, 41, 59, 1), rgba(0, 0, 0, 1))',
        'dylan-scanline': 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%)',
      },
      boxShadow: {
        'dylan-glow-cyan': '0 0 15px rgba(6, 182, 212, 0.15)',
        'dylan-glow-violet': '0 0 15px rgba(217, 70, 239, 0.15)',
        'dylan-glow-red': '0 0 15px rgba(239, 68, 68, 0.15)',
        'dylan-glow-cyan-strong': '0 0 20px rgba(6, 182, 212, 0.4)',
        'dylan-glow-violet-strong': '0 0 20px rgba(217, 70, 239, 0.4)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'dylan-pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      backdropBlur: {
        'dylan': '8px',
      },
    },
  },
  plugins: [],
}
