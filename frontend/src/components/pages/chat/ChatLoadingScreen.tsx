'use client';

/**
 * ChatLoadingScreen component renders a loading screen for the chat interface.
 * It displays a skeleton UI with animated placeholders to indicate loading state.
 *
 * @returns {JSX.Element} The loading screen component.
 */
export default function ChatLoadingScreen() {
  return (
    <div className="flex h-screen w-screen">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 p-6">
          <div className="max-w-3xl mx-auto space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex gap-4">
                <div className="h-10 w-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1 h-24 bg-gray-200 rounded-lg"></div>
              </div>
            ))}
          </div>
        </div>
        <div className="p-4 border-t">
          <div className="max-w-3xl mx-auto">
            <div className="h-12 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
