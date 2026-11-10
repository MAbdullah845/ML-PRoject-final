import forms from '@tailwindcss/forms';
import aspectRatio from '@tailwindcss/aspect-ratio';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B1613',
        panel: '#0F1B17',
        'panel-raised': '#13241E',
        line: '#22352C',
        'line-soft': '#1A2A23',
        text: '#E9E6D9',
        'text-dim': '#7E9389',
        'text-faint': '#546358',
        gold: '#C9A15A',
        'gold-dim': '#8A7440',
        up: '#4FA184',
        'up-soft': 'rgba(79,161,132,0.16)',
        down: '#A6493A',
        'down-soft': 'rgba(166,73,58,0.16)',
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
    },
  },
  plugins: [forms, aspectRatio],
};
