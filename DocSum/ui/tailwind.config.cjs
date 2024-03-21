const config = {
  content: ['./src/**/*.{html,js,svelte,ts}', './node_modules/flowbite-svelte/**/*.{html,js,svelte,ts}'],

  plugins: [require('flowbite/plugin')],

  darkMode: 'class',

  theme: {
    extend: {
      colors: {
        // flowbite-svelte
        primary: {
          50: '#f2f8ff',
          100: '#eef5ff',
          200: '#deecff',
          300: '#cce2ff',
          400: '#add0ff',
          500: '#5da2fe',
          600: '#2f81ef',
          700: '#2780eb',
          800: '#226fcc',
          900: '#1b5aa5'
        }
      }
    }
  }
};

module.exports = config;