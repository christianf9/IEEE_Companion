/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'media', // This will respect the user's system preferences
  content: [
    './src/pages/**/*.{js,jsx}',
    './src/components/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#3B82F6',
          DEFAULT: '#1D4ED8',
          dark: '#1E40AF',
        },
        secondary: {
          light: '#F97316',
          DEFAULT: '#EA580C',
          dark: '#C2410C',
        },
      },
    },
  },
  plugins: [],
};