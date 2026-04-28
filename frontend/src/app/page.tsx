'use client';

import AuthProvider from '@/components/AuthProvider';
import DashboardLoadingSkeleton from '@/components/pages/index/DashboardLoadingSkeleton';
import SignInPage from '@/components/pages/index/SignInPage';
import WelcomeScreen from '@/components/pages/index/WelcomeScreen';
import { useEffect } from 'react';

/**
 * Home component that renders different screens based on the application state and authorization status.
 *
 * @returns {JSX.Element} The appropriate screen based on the current state:
 * - A loading screen if the application state is 'loading'.
 * - A sign-in page if the user is not authorized.
 * - A welcome screen if the user is authorized.
 */
export default function Home() {
  useEffect(() => {
    window.document.title = 'global CT Insights - Startseite';
  }, []);

  return (
    <AuthProvider
      fallback={<DashboardLoadingSkeleton />}
      errorFallback={<SignInPage />}
    >
      <WelcomeScreen />
    </AuthProvider>
  );
}
