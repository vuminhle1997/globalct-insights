'use client';

import React from 'react';
import SignInPage from './pages/index/SignInPage';
import { selectAppState, selectAuthorized, useAppSelector } from '@/frontend/';

/**
 * A React component that provides authentication-based rendering logic.
 * It conditionally renders different components or elements based on the
 * authentication state, application state, and provided fallback options.
 *
 * @param children - The main content to render when the user is authenticated.
 * @param fallback - Optional React node to display while the application is loading.
 * @param errorFallback - Optional React node to display when the application is in a failed state.
 *
 * @returns A React element that renders one of the following based on the state:
 * - `fallback` if the application is loading.
 * - `errorFallback` if the application is in a failed state and loading.
 * - `<SignInPage />` if the user is not authenticated and the application is not loading.
 * - `children` if the user is authenticated.
 */
export default function AuthProvider({
  children,
  errorFallback,
  fallback,
}: {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  errorFallback?: React.ReactNode;
}) {
  const isAuth = useAppSelector(selectAuthorized);
  const appState = useAppSelector(selectAppState);
  const isLoading = appState === 'loading';
  const isFailing = appState === 'failed';

  if (fallback && isLoading) {
    return <>{fallback}</>;
  }

  if (errorFallback && !isFailing && isLoading) {
    return <>{errorFallback}</>;
  }

  if (!isAuth && !isLoading) {
    return <SignInPage />;
  }

  return <>{children}</>;
}
