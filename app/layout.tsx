import type { Metadata } from 'next';
import { ThemeProvider } from '@/components/ThemeProvider';
import './globals.css';

export const metadata: Metadata = {
  title: 'Tilemap Parser',
  description: 'A lightweight, production-ready parser for tilemap-editor JSON maps with runtime support for collision detection, camera systems, sprite animations, and particle effects.',
  keywords: ['tilemap', 'parser', 'game development', 'maps', 'collision'],
  authors: [{ name: 'FluffyBrudy' }],
  openGraph: {
    title: 'Tilemap Parser',
    description: 'A lightweight, production-ready parser for tilemap-editor JSON maps',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Tilemap Parser',
    description: 'A lightweight, production-ready parser for tilemap-editor JSON maps',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-background text-foreground">
        <ThemeProvider attribute="data-theme" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
