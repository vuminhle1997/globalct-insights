'use client';

import { Loader2 } from 'lucide-react';

/**
 * A functional component that displays a pending message loader overlay.
 *
 * @param {Object} props - The component props.
 * @param {string} props.message - The message to display while loading.
 *
 * @returns {JSX.Element} The JSX element representing the pending message loader.
 */
const PendingMessageLoader = ({ message }: { message: string }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-background p-4 rounded-lg flex items-center space-x-3">
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
      <span className="text-gray-800">{message}</span>
    </div>
  </div>
);

export default PendingMessageLoader;
