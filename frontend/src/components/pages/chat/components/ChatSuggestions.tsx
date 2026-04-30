'use client';

import { cn } from '@/lib/utils';

interface SuggestionItem {
  emoji: string;
  text: string;
}

const SUGGESTIONS: SuggestionItem[] = [
  { emoji: '👋', text: 'Hallo, wie heißen Sie?' },
  {
    emoji: '🛠️',
    text: 'Welche Werkzeuge stehen zur Verfügung, um mein Problem zu lösen?',
  },
  { emoji: '💡', text: 'Wie können Sie mir bei meiner Aufgabe helfen?' },
];

export interface ChatSuggestionsProps {
  /** Current message text – prevents overwriting an already-typed message */
  messageText: string;
  /** Callback to prefill the text-field with the chosen suggestion */
  onSelect: (text: string) => void;
}

/**
 * Displays the empty-chat welcome state with clickable suggestion prompts.
 */
export default function ChatSuggestions({
  messageText,
  onSelect,
}: ChatSuggestionsProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] space-y-8">
      <div className="text-center space-y-4">
        <h2 className="text-2xl font-semibold text-foreground">
          Willkommen im Chat!
        </h2>
        <p className="text-muted-foreground">
          Ich bin hier, um Ihnen zu helfen. Stelle mir eine Frage!
        </p>
      </div>
      <div className="space-y-4 w-full max-w-md">
        {SUGGESTIONS.map(({ emoji, text }) => (
          <button
            key={text}
            type="button"
            className={cn(
              'w-full text-left bg-background rounded-lg p-4 shadow-sm',
              'hover:shadow-md transition-shadow cursor-pointer'
            )}
            onClick={() => {
              if (!messageText) {
                onSelect(text);
              }
            }}
          >
            <p className="text-foreground">
              {emoji} &quot;{text}&quot;
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
