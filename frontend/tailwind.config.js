/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        theme: {
          primary: {
            DEFAULT: '#3b82f6',
            light: '#60a5fa',
            dark: '#2563eb',
          },
          secondary: {
            DEFAULT: '#6b7280',
            light: '#9ca3af',
            dark: '#4b5563',
          },
          bg: {
            primary: '#ffffff',
            secondary: '#f8fafc',
            tertiary: '#f1f5f9',
          },
          text: {
            primary: '#111827',
            secondary: '#6b7280',
            tertiary: '#9ca3af',
          },
          border: {
            DEFAULT: '#e5e7eb',
            light: '#f3f4f6',
            dark: '#d1d5db',
          },
          success: {
            DEFAULT: '#10b981',
            light: '#34d399',
            dark: '#059669',
          },
          warning: {
            DEFAULT: '#f59e0b',
            light: '#fbbf24',
            dark: '#d97706',
          },
          error: {
            DEFAULT: '#ef4444',
            light: '#f87171',
            dark: '#dc2626',
          },
          critical: {
            DEFAULT: '#dc2626',
            bg: '#fee2e2',
            border: '#fecaca',
          },
          high: {
            DEFAULT: '#ea580c',
            bg: '#fed7aa',
            border: '#fdba74',
          },
          medium: {
            DEFAULT: '#ca8a04',
            bg: '#fef3c7',
            border: '#fde68a',
          },
          low: {
            DEFAULT: '#16a34a',
            bg: '#dcfce7',
            border: '#bbf7d0',
          },
          info: {
            DEFAULT: '#0ea5e9',
            bg: '#e0f2fe',
            border: '#bae6fd',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Fira Code', 'ui-monospace', 'SFMono-Regular', 'Monaco', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-subtle': 'bounce 2s infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      maxWidth: {
        '8xl': '88rem',
        '9xl': '96rem',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};