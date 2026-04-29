'use client';
import { marked } from 'marked';
import { parseAgentResponse } from '@/lib/utils';
import React from 'react';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { ChevronDown } from 'lucide-react';

export interface ThinkAnswerBlockProps {
  response: string;
}

/**
 * Renders a block displaying the agent's thought process and final answer.
 *
 * This component takes a response string, parses it into separate blocks (e.g., "Thought" and "Answer"),
 * and displays each block with distinct styling. "Thought" blocks are highlighted with a yellow background,
 * while "Answer" blocks use a white or dark background. Markdown content is rendered as HTML.
 *
 * @param props - The properties for the ThinkAnswerBlock component.
 * @param props.response - The agent's response string to be parsed and displayed.
 * @returns A React element displaying the parsed thought and answer blocks.
 */
function ThinkAnswerBlockInner(props: ThinkAnswerBlockProps) {
  const { response } = props;
  // Memoize parsing so we don't redo work or change references unless response changes
  const parsed = React.useMemo(() => parseAgentResponse(response), [response]);

  const hasReasoningBlocks = React.useMemo(
    () => parsed.some(b => b.type === 'Thought' || b.type === 'Observation'),
    [parsed]
  );

  const [showTrajectories, setShowTrajectories] = React.useState(false);

  const handleToggle = () => {
    setShowTrajectories(!showTrajectories);
  };

  return (
    <div className="space-y-4 my-4">
      {hasReasoningBlocks && (
        <Button
          type="button"
          variant="ghost"
          onClick={handleToggle}
          className="w-full justify-between my-2 px-2 py-1 h-auto"
          aria-expanded={showTrajectories}
          aria-label={
            showTrajectories
              ? 'Gedankenprozess verbergen'
              : 'Gedankenprozess anzeigen'
          }
        >
          <Label className="cursor-pointer">Gedankenprozess</Label>
          <ChevronDown
            className={`ml-2 h-4 w-4 transition-transform duration-200 ${
              showTrajectories ? 'rotate-180' : ''
            }`}
          />
        </Button>
      )}

      {/* When collapsed, we only show Answer blocks; when expanded we show all */}
      {(showTrajectories
        ? parsed
        : parsed.filter(b => b.type === 'Answer')
      ).map((block, index) => {
        if (block.type === 'Thought') {
          return (
            <div
              key={`thought-${index}`}
              className="opacity-100 transition-opacity duration-300"
            >
              <div className="bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800 dark:bg-yellow-900 dark:border-yellow-500 dark:text-yellow-100 p-4 rounded">
                <p className="font-semibold mb-1">🧠 Gedanke</p>
                <div
                  className="prose prose-sm sm:prose dark:prose-invert whitespace-pre-line max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: marked(block.content),
                  }}
                />
              </div>
            </div>
          );
        }
        if (block.type === 'Observation') {
          return (
            <div
              key={`observation-${index}`}
              className="opacity-100 transition-opacity duration-300"
            >
              <div className="bg-blue-50 border-l-4 border-blue-400 text-blue-800 dark:bg-blue-900 dark:border-blue-500 dark:text-blue-100 p-4 rounded">
                <p className="font-semibold text-blue-700 dark:text-blue-300 mb-1">
                  🔎 Beobachtung
                </p>
                <div
                  className="prose prose-sm sm:prose dark:prose-invert max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: marked(block.content),
                  }}
                />
              </div>
            </div>
          );
        }
        if (block.type === 'Answer') {
          return (
            <div
              key={`answer-${index}`}
              className="transition-all duration-300"
            >
              <div className="bg-white border border-gray-200 text-gray-900 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100 p-4 rounded shadow">
                <p className="font-semibold text-green-700 dark:text-green-300 mb-1">
                  ✅ Antwort
                </p>
                <div
                  className="prose prose-sm sm:prose dark:prose-invert max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: marked(block.content),
                  }}
                />
              </div>
            </div>
          );
        }
        return null;
      })}
    </div>
  );
}

// Prevent unnecessary re-renders: only re-render if response string actually changes
const ThinkAnswerBlock = React.memo(ThinkAnswerBlockInner, (prev, next) => {
  return prev.response === next.response;
});

export default ThinkAnswerBlock;
