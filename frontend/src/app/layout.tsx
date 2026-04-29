import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import AppProvider from '@/components/provider/AppProvider';
import { ThemeProvider } from '@/components/theme-provider';
import { cn } from '@/lib/utils';
import CookieConsentBanner from '@/components/ui/cookie-consent';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

/**
 * RootLayout component that sets up the basic HTML structure for the application.
 *
 * @param {Readonly<{ children: React.ReactNode }>} props - The props object containing children.
 * @param {React.ReactNode} props.children - The child components to be rendered within the layout.
 *
 * @returns {JSX.Element} The root layout component.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de-DE" suppressHydrationWarning>
      <body
        className={cn(
          `${geistSans.variable} ${geistMono.variable} antialiased`
        )}
      >
        <AppProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {children}
          </ThemeProvider>
        </AppProvider>
        <CookieConsentBanner />
      </body>
    </html>
  );
}
