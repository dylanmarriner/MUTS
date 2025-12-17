# UI Theme System

## Theme Structure
- `src/theme/`
  - `theme.ts` - Base theme definition
  - `components/` - Themed component overrides
  - `palette/` - Color definitions

## Extending Themes
1. Create new palette in `palette/newTheme.ts`
```ts
export const newTheme = {
  primary: '#3a86ff',
  secondary: '#8338ec',
  error: '#ff006e',
};
```

2. Import in `theme.ts`
```ts
import { newTheme } from './palette/newTheme';

export const themeExtensions = {
  newTheme,
};
```

3. Apply in component
```tsx
import { useTheme } from '@mui/material';

const MyComponent = () => {
  const theme = useTheme();
  return (
    <div style={{ color: theme.palette.primary.main }}>
      Themed Component
    </div>
  );
};
```
