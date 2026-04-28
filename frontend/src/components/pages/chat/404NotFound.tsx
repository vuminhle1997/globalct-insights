'use client';

import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import React from 'react';

/**
 * A React functional component that displays a "Chat not found" screen.
 * This component is used when a user tries to access a chat that does not exist.
 *
 * @returns {JSX.Element} The rendered component.
 *
 * @component
 * @example
 * return (
 *   <UserChatNotFoundScreen />
 * )
 *
 * @remarks
 * This component uses Tailwind CSS for styling and Next.js router for navigation.
 *
 * @see {@link https://nextjs.org/docs/api-reference/next/router} for more information about Next.js router.
 */
export const UserChatNotFoundScreen = () => {
  const router = useRouter();
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] space-y-8">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-semibold text-gray-800">
          Chat nicht gefunden
        </h2>
        <p className="text-gray-600">
          Der angeforderte Chat konnte nicht gefunden werden.
        </p>
        <Button
          onClick={() => {
            router.push('/');
          }}
          className="bg-primary text-white"
        >
          Zurück zur Hauptseite
        </Button>
      </div>
    </div>
  );
};

/**
 * ChatNotFoundScreen component renders a 404 error screen for a chat page.
 * It displays a message indicating that the requested chat could not be found
 * and provides a button to navigate back to the homepage.
 *
 * @returns {JSX.Element} The rendered 404 error screen for the chat page.
 */
export default function ChatNotFoundScreen() {
  const router = useRouter();
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-4xl font-bold mb-4">Chat nicht gefunden</h1>
      <p className="text-gray-600 mb-8">
        Der angeforderte Chat konnte nicht gefunden werden.
      </p>
      <Button
        onClick={() => router.push('/')}
        className="bg-primary text-white"
      >
        Zurück zur Startseite
      </Button>
    </div>
  );
}
