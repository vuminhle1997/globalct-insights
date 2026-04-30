'use client';

import WelcomeScreen from '@/components/pages/index/WelcomeScreen';
import AuthProvider from '@/components/AuthProvider';
import ChatLoadingScreen from '@/components/pages/chat/ChatLoadingScreen';

/**
 * ChatPage component that handles the authentication state and routing.
 *
 * This component uses the `useAuth` hook to determine the loading state and any authentication errors.
 * Depending on the state, it either:
 * - Renders a loading skeleton while authentication is in progress.
 * - Redirects to the home page if there is an authentication error.
 * - Renders the welcome screen if authentication is successful.
 *
 * @returns {JSX.Element} The appropriate component based on the authentication state.
 */
export default function ChatPage() {
  return (
    <AuthProvider fallback={<ChatLoadingScreen />}>
      <WelcomeScreen />
    </AuthProvider>
  );
}
