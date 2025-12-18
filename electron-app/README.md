# VersaTuner - Sci-fi Edition

A futuristic Electron application for Mazda ECU tuning with a comprehensive sci-fi theme system.

## Features

### Theme System

- **6 Color Variants**: Cyan, Violet, Red, Amber, Green, Rose
- **Dynamic Theme Switching**: Via menu bar and preferences
- **CSS Custom Properties**: Efficient theme management
- **Persistent Selection**: Theme preference saved to localStorage

### Visual Effects

- **Holographic Panels**: Glass morphism with backdrop blur
- **Neon Glow Effects**: Dynamic shadows and lighting
- **Scanline Overlay**: Retro CRT monitor effect
- **Noise Texture**: Subtle visual noise for depth
- **Smooth Animations**: Hardware-accelerated transitions

### UI Components

- **Custom Title Bar**: Frameless window with controls
- **Sidebar Navigation**: Organized section switching
- **Live Data Gauges**: Animated circular gauges
- **Holo Panels**: Themed content containers
- **Neon Buttons**: Interactive styled buttons

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd VersaTuner/electron-app

# Install dependencies
npm install

# Run the app
npm start
```

## Development

### Scripts

- `npm start` - Run the application
- `npm run dev` - Run in development mode with DevTools
- `npm run build` - Build distributable packages
- `npm test` - Run test suite

### File Structure

```text
electron-app/
├── main.js          # Main Electron process
├── preload.js       # Preload script for security
├── index.html       # Main HTML file
├── renderer.js      # Renderer process logic
├── theme.css        # Sci-fi theme definitions
├── styles.css       # Application styles
├── package.json     # Dependencies and scripts
└── test-app.js      # Test suite
```

## Theme Customization

### Adding New Colors

1. Update `theme.css` with new color variables
2. Add theme variant class (e.g., `.theme-purple`)
3. Update menu items in `main.js`
4. Add option to preferences selector

### Modifying Effects

- **Glow Intensity**: Adjust `--glow-*` variables
- **Panel Opacity**: Modify `--color-bg-panel`
- **Animation Speed**: Update `--transition-*` variables
- **Scanline Density**: Change background-size in `.scanlines`

## Security

- Context isolation enabled
- Node integration disabled in renderer
- Secure preload script with contextBridge
- Content Security Policy headers
- No remote code execution

## Performance

- CSS-based animations for 60fps
- Efficient theme switching via CSS classes
- Minimal JavaScript overhead
- Hardware-accelerated effects
- Optimized render loop

## Testing

Run the test suite to verify functionality:

```bash
node test-app.js
```

Tests include:

- File structure validation
- Theme CSS verification
- Main process checks
- Preload script validation
- Renderer process verification
- Dependency confirmation

## Browser Compatibility

Built on Electron, supports:

- Windows 10+
- macOS 10.14+
- Linux (Ubuntu 18.04+)

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit pull request

## Troubleshooting

### Theme Not Applying

- Check browser console for errors
- Verify theme.css is loaded
- Ensure contextBridge is working

### Performance Issues

- Disable scanline effect for older hardware
- Reduce animation complexity
- Check GPU acceleration

### Window Controls Not Working

- Verify preload.js is loaded
- Check contextBridge exposure
- Ensure main process IPC handlers are registered
