/**
 * Dylan Sci-fi - Visual Style System
 *
 * Extracted from NEW-UI-THEME-INTEGRATE-ALL.tsx
 * Pixel-perfect visual tokens for holographic UI components
 *
 * @description Complete theme definition preserving exact visual appearance
 * @version 1.0.0
 * @author Dylan UI System
 */
// ------------------------------------------------------------------
// COLOR SYSTEM
// ------------------------------------------------------------------
export const colors = {
    // Primary color palette with exact hex values
    primary: {
        cyan: '#06b6d4',
        violet: '#d946ef',
        red: '#ef4444',
        amber: '#f59e0b',
        green: '#22c55e',
        rose: '#f43f5e',
    },
    // Extended color variants with opacity
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
    },
    // Neutral colors
    slate: {
        50: 'rgba(248, 250, 252, 0.05)',
        100: 'rgba(241, 245, 249, 0.10)',
        200: 'rgba(226, 232, 240, 0.20)',
        300: 'rgba(203, 213, 225, 0.30)',
        400: 'rgba(148, 163, 184, 0.40)',
        500: 'rgba(100, 116, 139, 0.50)',
        600: 'rgba(71, 85, 105, 0.60)',
        700: 'rgba(51, 65, 85, 0.70)',
        800: 'rgba(30, 41, 59, 0.80)',
        900: 'rgba(15, 23, 42, 0.90)',
        950: 'rgba(2, 6, 23, 0.95)',
    },
    // Background colors
    background: {
        primary: 'rgba(15, 23, 42, 1)', // slate-950
        secondary: 'rgba(30, 41, 59, 1)', // slate-800
        panel: 'rgba(30, 41, 59, 0.8)', // slate-900/80
        glass: 'rgba(30, 41, 59, 0.5)', // slate-900/50
        overlay: 'rgba(0, 0, 0, 0.4)', // black/40
        light: 'rgba(0, 0, 0, 0.2)', // black/20
        scanline: 'rgba(18, 16, 16, 0.5)', // custom scanline color
    },
    // Text colors
    text: {
        primary: 'rgba(248, 250, 252, 1)', // slate-50
        secondary: 'rgba(203, 213, 225, 1)', // slate-300
        tertiary: 'rgba(148, 163, 184, 1)', // slate-400
        muted: 'rgba(100, 116, 139, 1)', // slate-500
        disabled: 'rgba(71, 85, 105, 1)', // slate-600
    },
};
// ------------------------------------------------------------------
// GLOW & SHADOW SYSTEM
// ------------------------------------------------------------------
export const glow = {
    // Primary glow effects with exact rgba values
    cyan: {
        light: 'rgba(6, 182, 212, 0.15)',
        medium: 'rgba(6, 182, 212, 0.2)',
        strong: 'rgba(6, 182, 212, 0.3)',
        intense: 'rgba(6, 182, 212, 0.5)',
    },
    violet: {
        light: 'rgba(217, 70, 239, 0.15)',
        medium: 'rgba(217, 70, 239, 0.2)',
        strong: 'rgba(217, 70, 239, 0.3)',
        intense: 'rgba(217, 70, 239, 0.5)',
    },
    red: {
        light: 'rgba(239, 68, 68, 0.15)',
        medium: 'rgba(239, 68, 68, 0.2)',
        strong: 'rgba(239, 68, 68, 0.3)',
        intense: 'rgba(239, 68, 68, 0.5)',
    },
    amber: {
        light: 'rgba(245, 158, 11, 0.15)',
        medium: 'rgba(245, 158, 11, 0.2)',
        strong: 'rgba(245, 158, 11, 0.3)',
        intense: 'rgba(245, 158, 11, 0.5)',
    },
    green: {
        light: 'rgba(34, 197, 94, 0.15)',
        medium: 'rgba(34, 197, 94, 0.2)',
        strong: 'rgba(34, 197, 94, 0.3)',
        intense: 'rgba(34, 197, 94, 0.5)',
    },
    rose: {
        light: 'rgba(244, 63, 94, 0.15)',
        medium: 'rgba(244, 63, 94, 0.2)',
        strong: 'rgba(244, 63, 94, 0.3)',
        intense: 'rgba(244, 63, 94, 0.5)',
    },
    // Shadow definitions
    shadows: {
        small: '0 1px 2px rgba(0, 0, 0, 0.3)',
        medium: '0 4px 6px rgba(0, 0, 0, 0.4)',
        large: '0 10px 15px rgba(0, 0, 0, 0.5)',
        glow: '0 0 15px rgba(6, 182, 212, 0.15)',
        glowActive: '0 0 10px rgba(6, 182, 212, 0.2)',
        glowIntense: '0 0 20px rgba(6, 182, 212, 0.3)',
    },
};
// ------------------------------------------------------------------
// GRADIENT SYSTEM
// ------------------------------------------------------------------
export const gradients = {
    // Linear gradients
    scanline: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%)',
    scanlineGrid: 'linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
    header: 'linear-gradient(to right, rgba(6, 182, 212, 1), rgba(217, 70, 239, 1))',
    sync: 'linear-gradient(to bottom, rgba(6, 182, 212, 1), rgba(255, 255, 255, 1), rgba(217, 70, 239, 1))',
    // Radial gradients
    background: 'radial-gradient(ellipse at center, var(--tw-gradient-stops))',
    ambient: 'radial-gradient(ellipse at center, rgba(30, 41, 59, 1), rgba(0, 0, 0, 1))',
    // Component-specific gradients
    panel: {
        cyan: 'linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(6, 182, 212, 0.05))',
        violet: 'linear-gradient(135deg, rgba(217, 70, 239, 0.1), rgba(217, 70, 239, 0.05))',
        red: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05))',
        amber: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05))',
        green: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05))',
        rose: 'linear-gradient(135deg, rgba(244, 63, 94, 0.1), rgba(244, 63, 94, 0.05))',
    },
};
// ------------------------------------------------------------------
// HOLOGRAPHIC EFFECTS
// ------------------------------------------------------------------
export const hologram = {
    // Scanline patterns
    scanlines: {
        fine: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%)',
        medium: 'linear-gradient(rgba(18, 16, 16, 0) 25%, rgba(0, 0, 0, 0.25) 25%, rgba(0, 0, 0, 0.25) 50%, rgba(18, 16, 16, 0) 50%, rgba(18, 16, 16, 0) 75%, rgba(0, 0, 0, 0.25) 75%)',
        thick: 'linear-gradient(rgba(18, 16, 16, 0) 33%, rgba(0, 0, 0, 0.25) 33%, rgba(0, 0, 0, 0.25) 66%, rgba(18, 16, 16, 0) 66%)',
    },
    // Noise patterns
    noise: {
        light: 'url("data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.05"/%3E%3C/svg%3E")',
        medium: 'url("data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.1"/%3E%3C/svg%3E")',
        heavy: 'url("data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.15"/%3E%3C/svg%3E")',
    },
    // Glass morphism
    glass: {
        light: {
            background: 'rgba(30, 41, 59, 0.5)',
            backdropFilter: 'blur(4px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
        },
        medium: {
            background: 'rgba(30, 41, 59, 0.8)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
        },
        heavy: {
            background: 'rgba(15, 23, 42, 0.9)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
        },
    },
};
// ------------------------------------------------------------------
// FRAME & BORDER SYSTEM
// ------------------------------------------------------------------
export const frames = {
    // Border styles
    borders: {
        default: '1px solid',
        thick: '2px solid',
        thin: '0.5px solid',
        dashed: '1px dashed',
        dotted: '1px dotted',
    },
    // Corner accents
    corners: {
        small: {
            width: '8px',
            height: '8px',
            borderWidth: '2px',
            opacity: 0.6,
        },
        medium: {
            width: '12px',
            height: '12px',
            borderWidth: '2px',
            opacity: 0.6,
        },
        large: {
            width: '16px',
            height: '16px',
            borderWidth: '3px',
            opacity: 0.8,
        },
    },
    // Frame presets
    holo: {
        cyan: 'border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.15)]',
        violet: 'border-fuchsia-500/50 shadow-[0_0_15px_rgba(217,70,239,0.15)]',
        red: 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.15)]',
        amber: 'border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.15)]',
        green: 'border-green-500/50 shadow-[0_0_15px_rgba(34,197,94,0.15)]',
        rose: 'border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.15)]',
    },
    // Active frame states
    active: {
        cyan: 'border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.4)]',
        violet: 'border-fuchsia-400 shadow-[0_0_20px_rgba(217,70,239,0.4)]',
        red: 'border-red-400 shadow-[0_0_20px_rgba(239,68,68,0.4)]',
        amber: 'border-amber-400 shadow-[0_0_20px_rgba(245,158,11,0.4)]',
        green: 'border-green-400 shadow-[0_0_20px_rgba(34,197,94,0.4)]',
        rose: 'border-rose-400 shadow-[0_0_20px_rgba(244,63,94,0.4)]',
    },
};
// ------------------------------------------------------------------
// ANIMATION SYSTEM
// ------------------------------------------------------------------
export const animations = {
    // Pulse animations
    pulse: {
        slow: 'pulse 6s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        normal: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        fast: 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    },
    // Spin animations
    spin: {
        slow: 'spin 20s linear infinite',
        normal: 'spin 10s linear infinite',
        fast: 'spin 3s linear infinite',
        reverse: 'spin 10s linear infinite reverse',
    },
    // Scan animations
    scan: {
        slow: 'scan 4s linear infinite',
        normal: 'scan 2s linear infinite',
        fast: 'scan 1s linear infinite',
    },
    // Transition timings
    transitions: {
        fast: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
        normal: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        slow: 'all 0.7s cubic-bezier(0.4, 0, 0.2, 1)',
        slower: 'all 1s cubic-bezier(0.4, 0, 0.2, 1)',
        slowest: 'all 2s cubic-bezier(0.4, 0, 0.2, 1)',
    },
    // Easing functions
    easing: {
        easeOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
        easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
        easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
        bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    },
};
// ------------------------------------------------------------------
// PANEL COMPONENT PRESETS
// ------------------------------------------------------------------
// Base panel styles defined separately to avoid circular reference
const basePanelStyles = {
    background: 'rgba(30, 41, 59, 0.8)',
    backdropFilter: 'blur(8px)',
    border: '1px solid',
    borderRadius: '0.125rem',
    overflow: 'hidden',
    position: 'relative',
};
export const panels = {
    // Base panel styles
    base: basePanelStyles,
    // HoloPanel variants
    holoPanel: {
        cyan: {
            background: 'rgba(30, 41, 59, 0.8)',
            backdropFilter: 'blur(8px)',
            border: '1px solid',
            borderColor: 'rgba(6, 182, 212, 0.5)',
            borderRadius: '0.125rem',
            overflow: 'hidden',
            position: 'relative',
            boxShadow: '0 0 15px rgba(6, 182, 212, 0.15)',
            titleColor: 'rgba(6, 182, 212, 1)',
        },
        violet: {
            background: 'rgba(30, 41, 59, 0.8)',
            backdropFilter: 'blur(8px)',
            border: '1px solid',
            borderColor: 'rgba(217, 70, 239, 0.5)',
            borderRadius: '0.125rem',
            overflow: 'hidden',
            position: 'relative',
            boxShadow: '0 0 15px rgba(217, 70, 239, 0.15)',
            titleColor: 'rgba(217, 70, 239, 1)',
        },
        red: {
            background: 'rgba(30, 41, 59, 0.8)',
            backdropFilter: 'blur(8px)',
            border: '1px solid',
            borderColor: 'rgba(239, 68, 68, 0.5)',
            borderRadius: '0.125rem',
            overflow: 'hidden',
            position: 'relative',
            boxShadow: '0 0 15px rgba(239, 68, 68, 0.15)',
            titleColor: 'rgba(239, 68, 68, 1)',
        },
        amber: {
            background: 'rgba(30, 41, 59, 0.8)',
            backdropFilter: 'blur(8px)',
            border: '1px solid',
            borderColor: 'rgba(245, 158, 11, 0.5)',
            borderRadius: '0.125rem',
            overflow: 'hidden',
            position: 'relative',
            boxShadow: '0 0 15px rgba(245, 158, 11, 0.15)',
            titleColor: 'rgba(245, 158, 11, 1)',
        },
        green: {
            background: 'rgba(30, 41, 59, 0.8)',
            backdropFilter: 'blur(8px)',
            border: '1px solid',
            borderColor: 'rgba(34, 197, 94, 0.5)',
            borderRadius: '0.125rem',
            overflow: 'hidden',
            position: 'relative',
            boxShadow: '0 0 15px rgba(34, 197, 94, 0.15)',
            titleColor: 'rgba(34, 197, 94, 1)',
        },
        rose: {
            background: 'rgba(30, 41, 59, 0.8)',
            backdropFilter: 'blur(8px)',
            border: '1px solid',
            borderColor: 'rgba(244, 63, 94, 0.5)',
            borderRadius: '0.125rem',
            overflow: 'hidden',
            position: 'relative',
            boxShadow: '0 0 15px rgba(244, 63, 94, 0.15)',
            titleColor: 'rgba(244, 63, 94, 1)',
        },
    },
    // Panel header styles
    header: {
        background: 'rgba(0, 0, 0, 0.4)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        padding: '0.5rem 1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 10,
    },
    // Panel content styles
    content: {
        padding: '1rem',
        position: 'relative',
        zIndex: 10,
        flex: 1,
    },
};
// ------------------------------------------------------------------
// BACKGROUND SYSTEM
// ------------------------------------------------------------------
export const backgrounds = {
    // Main backgrounds
    main: {
        primary: 'radial-gradient(ellipse at center, rgba(30, 41, 59, 1), rgba(0, 0, 0, 1))',
        dark: 'radial-gradient(ellipse at center, rgba(15, 23, 42, 1), rgba(0, 0, 0, 1))',
        light: 'radial-gradient(ellipse at center, rgba(51, 65, 85, 1), rgba(0, 0, 0, 1))',
    },
    // Ambient glow backgrounds
    ambient: {
        cyan: 'rgba(6, 182, 212, 0.1) blur(150px)',
        violet: 'rgba(217, 70, 239, 0.1) blur(150px)',
        mixed: 'linear-gradient(45deg, rgba(6, 182, 212, 0.1), rgba(217, 70, 239, 0.1))',
    },
    // Pattern backgrounds
    patterns: {
        grid: 'linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
        dots: 'radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px)',
        lines: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255, 255, 255, 0.03) 2px, rgba(255, 255, 255, 0.03) 4px)',
    },
    // Overlay backgrounds
    overlays: {
        scanline: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%)',
        vignette: 'radial-gradient(ellipse at center, transparent 0%, rgba(0, 0, 0, 0.4) 100%)',
        noise: 'url("data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.05"/%3E%3C/svg%3E")',
    },
};
// ------------------------------------------------------------------
// TYPOGRAPHY SYSTEM
// ------------------------------------------------------------------
export const typography = {
    // Font families
    fonts: {
        mono: '"Fira Code", "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',
        sans: '"Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        display: '"Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    },
    // Font sizes
    sizes: {
        xs: '0.625rem', // 10px
        sm: '0.75rem', // 12px
        base: '0.875rem', // 14px
        lg: '1rem', // 16px
        xl: '1.125rem', // 18px
        '2xl': '1.25rem', // 20px
        '3xl': '1.5rem', // 24px
        '4xl': '1.875rem', // 30px
        '5xl': '2.25rem', // 36px
        '6xl': '3rem', // 48px
        // Micro sizes for UI
        '8px': '0.5rem',
        '9px': '0.5625rem',
        '10px': '0.625rem',
        '12px': '0.75rem',
        '14px': '0.875rem',
        '16px': '1rem',
        '18px': '1.125rem',
        '20px': '1.25rem',
        '24px': '1.5rem',
        '28px': '1.75rem',
        '32px': '2rem',
    },
    // Font weights
    weights: {
        thin: '100',
        light: '300',
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
        extrabold: '800',
        black: '900',
    },
    // Letter spacing
    tracking: {
        tighter: '-0.05em',
        tight: '-0.025em',
        normal: '0em',
        wide: '0.025em',
        wider: '0.05em',
        widest: '0.1em',
        ultra: '0.2em',
    },
    // Line heights
    leading: {
        none: '1',
        tight: '1.25',
        snug: '1.375',
        normal: '1.5',
        relaxed: '1.625',
        loose: '2',
    },
    // Text transforms
    transforms: {
        none: 'none',
        uppercase: 'uppercase',
        lowercase: 'lowercase',
        capitalize: 'capitalize',
    },
};
// ------------------------------------------------------------------
// EFFECTS SYSTEM
// ------------------------------------------------------------------
export const effects = {
    // Blur effects
    blur: {
        none: 'blur(0px)',
        sm: 'blur(4px)',
        md: 'blur(8px)',
        lg: 'blur(16px)',
        xl: 'blur(24px)',
        '2xl': 'blur(40px)',
        '3xl': 'blur(64px)',
    },
    // Brightness effects
    brightness: {
        dim: 'brightness(0.8)',
        normal: 'brightness(1)',
        bright: 'brightness(1.1)',
        brighter: 'brightness(1.2)',
        brightest: 'brightness(1.3)',
    },
    // Contrast effects
    contrast: {
        low: 'contrast(0.8)',
        normal: 'contrast(1)',
        high: 'contrast(1.1)',
        higher: 'contrast(1.25)',
        highest: 'contrast(1.5)',
    },
    // Saturation effects
    saturation: {
        desaturated: 'saturate(0.8)',
        normal: 'saturate(1)',
        saturated: 'saturate(1.2)',
        vibrant: 'saturate(1.4)',
    },
    // Filter combinations
    filters: {
        avatar: 'contrast(1.25) brightness(1.1) saturate(1.2)',
        hologram: 'brightness(1.1) saturate(1.2) contrast(1.1)',
        scanline: 'brightness(0.9) contrast(1.1)',
        glow: 'brightness(1.2) saturate(1.3)',
    },
    // Special effects
    special: {
        hueRotate: {
            cyan: 'hue-rotate-0deg',
            violet: 'hue-rotate-15deg',
            amber: 'hue-rotate-30deg',
            green: 'hue-rotate-90deg',
            red: 'hue-rotate-180deg',
        },
        scale: {
            hover: 'scale(1.05)',
            active: 'scale(0.98)',
            grow: 'scale(1.1)',
            shrink: 'scale(0.9)',
        },
        rotate: {
            slow: 'rotate(360deg)',
            fast: 'rotate(720deg)',
            reverse: 'rotate(-360deg)',
        },
    },
};
// ------------------------------------------------------------------
// LAYOUT PRIMITIVES
// ------------------------------------------------------------------
export const layout = {
    // Spacing scale
    spacing: {
        0: '0px',
        1: '0.25rem', // 4px
        2: '0.5rem', // 8px
        3: '0.75rem', // 12px
        4: '1rem', // 16px
        5: '1.25rem', // 20px
        6: '1.5rem', // 24px
        8: '2rem', // 32px
        10: '2.5rem', // 40px
        12: '3rem', // 48px
        16: '4rem', // 64px
        20: '5rem', // 80px
        24: '6rem', // 96px
        32: '8rem', // 128px
    },
    // Border radius
    borderRadius: {
        none: '0px',
        sm: '0.125rem', // 2px
        md: '0.25rem', // 4px
        lg: '0.5rem', // 8px
        xl: '0.75rem', // 12px
        '2xl': '1rem', // 16px
        full: '9999px',
    },
    // Grid systems
    grid: {
        cols: {
            1: 'grid-cols-1',
            2: 'grid-cols-2',
            3: 'grid-cols-3',
            4: 'grid-cols-4',
            5: 'grid-cols-5',
            6: 'grid-cols-6',
            8: 'grid-cols-8',
            10: 'grid-cols-10',
            12: 'grid-cols-12',
        },
        gap: {
            1: 'gap-1',
            2: 'gap-2',
            3: 'gap-3',
            4: 'gap-4',
            6: 'gap-6',
            8: 'gap-8',
        },
    },
    // Flex utilities
    flex: {
        direction: {
            row: 'flex-row',
            col: 'flex-col',
            'row-reverse': 'flex-row-reverse',
            'col-reverse': 'flex-col-reverse',
        },
        align: {
            start: 'items-start',
            center: 'items-center',
            end: 'items-end',
            stretch: 'items-stretch',
        },
        justify: {
            start: 'justify-start',
            center: 'justify-center',
            end: 'justify-end',
            between: 'justify-between',
            around: 'justify-around',
            evenly: 'justify-evenly',
        },
    },
};
// COMPONENT PRESETS
// ------------------------------------------------------------------
export const components = {
    // HoloPanel preset
    holoPanel: (color = 'cyan') => {
        const colorMap = {
            cyan: {
                background: 'rgba(30, 41, 59, 0.8)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(6, 182, 212, 0.5)',
                borderRadius: '0.125rem',
                boxShadow: '0 0 15px rgba(6, 182, 212, 0.15)',
                position: 'relative',
                overflow: 'hidden',
            },
            violet: {
                background: 'rgba(30, 41, 59, 0.8)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(217, 70, 239, 0.5)',
                borderRadius: '0.125rem',
                boxShadow: '0 0 15px rgba(217, 70, 239, 0.15)',
                position: 'relative',
                overflow: 'hidden',
            },
            red: {
                background: 'rgba(30, 41, 59, 0.8)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
                borderRadius: '0.125rem',
                boxShadow: '0 0 15px rgba(239, 68, 68, 0.15)',
                position: 'relative',
                overflow: 'hidden',
            },
            amber: {
                background: 'rgba(30, 41, 59, 0.8)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(245, 158, 11, 0.5)',
                borderRadius: '0.125rem',
                boxShadow: '0 0 15px rgba(245, 158, 11, 0.15)',
                position: 'relative',
                overflow: 'hidden',
            },
            green: {
                background: 'rgba(30, 41, 59, 0.8)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(34, 197, 94, 0.5)',
                borderRadius: '0.125rem',
                boxShadow: '0 0 15px rgba(34, 197, 94, 0.15)',
                position: 'relative',
                overflow: 'hidden',
            },
            rose: {
                background: 'rgba(30, 41, 59, 0.8)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(244, 63, 94, 0.5)',
                borderRadius: '0.125rem',
                boxShadow: '0 0 15px rgba(244, 63, 94, 0.15)',
                position: 'relative',
                overflow: 'hidden',
            },
        };
        return colorMap[color];
    },
    // HoloStatBar preset
    holoStatBar: (color = 'cyan') => {
        const colorMap = {
            cyan: {
                height: '0.375rem',
                background: 'rgba(30, 41, 59, 1)',
                borderRadius: '0.125rem',
                overflow: 'hidden',
                fill: 'rgba(6, 182, 212, 1)',
                shadow: '0 0 10px rgba(6, 182, 212, 0.5)',
            },
            violet: {
                height: '0.375rem',
                background: 'rgba(30, 41, 59, 1)',
                borderRadius: '0.125rem',
                overflow: 'hidden',
                fill: 'rgba(217, 70, 239, 1)',
                shadow: '0 0 10px rgba(217, 70, 239, 0.5)',
            },
            red: {
                height: '0.375rem',
                background: 'rgba(30, 41, 59, 1)',
                borderRadius: '0.125rem',
                overflow: 'hidden',
                fill: 'rgba(239, 68, 68, 1)',
                shadow: '0 0 10px rgba(239, 68, 68, 0.5)',
            },
            amber: {
                height: '0.375rem',
                background: 'rgba(30, 41, 59, 1)',
                borderRadius: '0.125rem',
                overflow: 'hidden',
                fill: 'rgba(245, 158, 11, 1)',
                shadow: '0 0 10px rgba(245, 158, 11, 0.5)',
            },
            green: {
                height: '0.375rem',
                background: 'rgba(30, 41, 59, 1)',
                borderRadius: '0.125rem',
                overflow: 'hidden',
                fill: 'rgba(34, 197, 94, 1)',
                shadow: '0 0 10px rgba(34, 197, 94, 0.5)',
            },
            rose: {
                height: '0.375rem',
                background: 'rgba(30, 41, 59, 1)',
                borderRadius: '0.125rem',
                overflow: 'hidden',
                fill: 'rgba(244, 63, 94, 1)',
                shadow: '0 0 10px rgba(244, 63, 94, 0.5)',
            },
        };
        return colorMap[color];
    },
    // CircularGauge preset
    circularGauge: (color = 'cyan', size = 60) => {
        const colorMap = {
            cyan: {
                size: `${size}px`,
                stroke: 'rgba(6, 182, 212, 1)',
                strokeWidth: '3px',
                shadow: '0 0 6px rgba(6, 182, 212, 0.5)',
                background: 'rgba(30, 41, 59, 0.3)',
            },
            violet: {
                size: `${size}px`,
                stroke: 'rgba(217, 70, 239, 1)',
                strokeWidth: '3px',
                shadow: '0 0 6px rgba(217, 70, 239, 0.5)',
                background: 'rgba(30, 41, 59, 0.3)',
            },
            red: {
                size: `${size}px`,
                stroke: 'rgba(239, 68, 68, 1)',
                strokeWidth: '3px',
                shadow: '0 0 6px rgba(239, 68, 68, 0.5)',
                background: 'rgba(30, 41, 59, 0.3)',
            },
            amber: {
                size: `${size}px`,
                stroke: 'rgba(245, 158, 11, 1)',
                strokeWidth: '3px',
                shadow: '0 0 6px rgba(245, 158, 11, 0.5)',
                background: 'rgba(30, 41, 59, 0.3)',
            },
            green: {
                size: `${size}px`,
                stroke: 'rgba(34, 197, 94, 1)',
                strokeWidth: '3px',
                shadow: '0 0 6px rgba(34, 197, 94, 0.5)',
                background: 'rgba(30, 41, 59, 0.3)',
            },
            rose: {
                size: `${size}px`,
                stroke: 'rgba(244, 63, 94, 1)',
                strokeWidth: '3px',
                shadow: '0 0 6px rgba(244, 63, 94, 0.5)',
                background: 'rgba(30, 41, 59, 0.3)',
            },
        };
        return colorMap[color];
    },
    // NeonButton preset
    neonButton: (color = 'cyan') => {
        const colorMap = {
            cyan: {
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(6, 182, 212, 0.5)',
                color: 'rgba(6, 182, 212, 1)',
                borderRadius: '0.25rem',
                padding: '0.5rem 1rem',
                fontSize: '0.75rem',
                fontWeight: '700',
                fontFamily: typography.fonts.mono,
                transition: animations.transitions.normal,
                boxShadow: '0 0 10px rgba(6, 182, 212, 0.5)',
            },
            violet: {
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(217, 70, 239, 0.5)',
                color: 'rgba(217, 70, 239, 1)',
                borderRadius: '0.25rem',
                padding: '0.5rem 1rem',
                fontSize: '0.75rem',
                fontWeight: '700',
                fontFamily: typography.fonts.mono,
                transition: animations.transitions.normal,
                boxShadow: '0 0 10px rgba(217, 70, 239, 0.5)',
            },
            red: {
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(239, 68, 68, 0.5)',
                color: 'rgba(239, 68, 68, 1)',
                borderRadius: '0.25rem',
                padding: '0.5rem 1rem',
                fontSize: '0.75rem',
                fontWeight: '700',
                fontFamily: typography.fonts.mono,
                transition: animations.transitions.normal,
                boxShadow: '0 0 10px rgba(239, 68, 68, 0.5)',
            },
            amber: {
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(245, 158, 11, 0.5)',
                color: 'rgba(245, 158, 11, 1)',
                borderRadius: '0.25rem',
                padding: '0.5rem 1rem',
                fontSize: '0.75rem',
                fontWeight: '700',
                fontFamily: typography.fonts.mono,
                transition: animations.transitions.normal,
                boxShadow: '0 0 10px rgba(245, 158, 11, 0.5)',
            },
            green: {
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(34, 197, 94, 0.5)',
                color: 'rgba(34, 197, 94, 1)',
                borderRadius: '0.25rem',
                padding: '0.5rem 1rem',
                fontSize: '0.75rem',
                fontWeight: '700',
                fontFamily: typography.fonts.mono,
                transition: animations.transitions.normal,
                boxShadow: '0 0 10px rgba(34, 197, 94, 0.5)',
            },
            rose: {
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(244, 63, 94, 0.5)',
                color: 'rgba(244, 63, 94, 1)',
                borderRadius: '0.25rem',
                padding: '0.5rem 1rem',
                fontSize: '0.75rem',
                fontWeight: '700',
                fontFamily: typography.fonts.mono,
                transition: animations.transitions.normal,
                boxShadow: '0 0 10px rgba(244, 63, 94, 0.5)',
            },
        };
        return colorMap[color];
    },
    // HoloAvatar preset
    holoAvatar: (color = 'cyan') => {
        const colorMap = {
            cyan: {
                border: '1px solid rgba(6, 182, 212, 0.5)',
                borderRadius: '0.5rem',
                boxShadow: '0 0 20px rgba(6, 182, 212, 0.5)',
                filter: effects.filters.avatar,
                transition: animations.transitions.slower,
            },
            violet: {
                border: '1px solid rgba(217, 70, 239, 0.5)',
                borderRadius: '0.5rem',
                boxShadow: '0 0 20px rgba(217, 70, 239, 0.5)',
                filter: effects.filters.avatar,
                transition: animations.transitions.slower,
            },
            red: {
                border: '1px solid rgba(239, 68, 68, 0.5)',
                borderRadius: '0.5rem',
                boxShadow: '0 0 20px rgba(239, 68, 68, 0.5)',
                filter: effects.filters.avatar,
                transition: animations.transitions.slower,
            },
            amber: {
                border: '1px solid rgba(245, 158, 11, 0.5)',
                borderRadius: '0.5rem',
                boxShadow: '0 0 20px rgba(245, 158, 11, 0.5)',
                filter: effects.filters.avatar,
                transition: animations.transitions.slower,
            },
            green: {
                border: '1px solid rgba(34, 197, 94, 0.5)',
                borderRadius: '0.5rem',
                boxShadow: '0 0 20px rgba(34, 197, 94, 0.5)',
                filter: effects.filters.avatar,
                transition: animations.transitions.slower,
            },
            rose: {
                border: '1px solid rgba(244, 63, 94, 0.5)',
                borderRadius: '0.5rem',
                boxShadow: '0 0 20px rgba(244, 63, 94, 0.5)',
                filter: effects.filters.avatar,
                transition: animations.transitions.slower,
            },
        };
        return colorMap[color];
    },
};
// MAIN THEME EXPORT
// ------------------------------------------------------------------
export const dylanTheme = {
    colors,
    glow,
    gradients,
    hologram,
    frames,
    animations,
    panels,
    backgrounds,
    typography,
    effects,
    layout,
    components,
};
// Default export
export default dylanTheme;
