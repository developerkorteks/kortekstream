/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../**/templates/*.html", "../**/templates/**/*.html"],
  darkMode: 'class', // Menggunakan class untuk dark mode, bukan media query
  theme: {
    extend: {
      colors: {
        // Warna utama untuk light mode
        primary: {
          light: '#ffd700', // gold
          DEFAULT: '#daa520', // goldenrod
          dark: '#b8860b', // darkgoldenrod
        },
        secondary: {
          light: '#ffffff',
          DEFAULT: '#f8f9fa',
          dark: '#e9ecef',
        },
        
        // Dark mode colors
        darkPrimary: {
          light: '#f87171', // red-400
          DEFAULT: '#dc2626', // red-600
          dark: '#b91c1c', // red-700
        },
        darkSecondary: {
          light: '#1a1a1a', // Hitam dengan gradasi
          DEFAULT: '#121212',
          dark: '#000000',
        },
      },
    },
  },
  // Safelist untuk memastikan kelas-kelas kustom tidak di-purge
  safelist: [
    'light-bg',
    'light-text',
    'light-border',
    'dark:light-bg',
    'dark:light-text',
    'dark:light-border',
    'dark:hidden',
    'dark:inline',
    'dark:bg-black/20',
    'dark:bg-black/30',
    'dark:bg-black/40',
    'dark:border-white/10',
    'dark:text-white',
    'dark:hover:bg-white/20'
  ],
  plugins: [],
};