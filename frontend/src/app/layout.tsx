import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Agentic Ethical Hacker',
  description: 'AI-powered vulnerability analysis system inspired by RoboDuck',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-theme-bg-secondary min-h-screen`}>
        {children}
      </body>
    </html>
  );
}