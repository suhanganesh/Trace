/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        trace: {
          bg: '#f7f7f5',
          surface: '#ffffff',
          border: '#e4e4e7',
          text: '#18181b',
          muted: '#71717a',
          accent: '#0f766e',
          'accent-soft': '#ccfbf1',
          danger: '#b91c1c',
          warning: '#a16207',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      boxShadow: {
        trace: '0 1px 2px rgba(24, 24, 27, 0.04)',
      },
    },
  },
  plugins: [],
};
