'use client';

import Image from 'next/image';
import { marked } from 'marked';
import { cn } from '@/lib/utils';
import ThinkAnswerBlock from './ThinkAnswerBlock';
import { Message } from '@/frontend/types';

export interface MessageBubbleProps {
  message: Message;
  avatarSrc: string;
  profilePicture?: string | null;
  /** Ref attached to the outermost element – used for infinite-scroll observation */
  observerRef?: React.Ref<HTMLDivElement>;
}

/**
 * Renders a single chat message bubble for either the user or the assistant.
 *
 * @param props.message       - The message object to display.
 * @param props.avatarSrc     - URL of the AI assistant avatar.
 * @param props.profilePicture - URL of the user's profile picture.
 * @param props.observerRef   - Optional ref for the intersection observer sentinel.
 */
export default function MessageBubble({
  message,
  avatarSrc,
  profilePicture,
  observerRef,
}: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      ref={observerRef}
      className={cn(
        'flex items-start gap-4 w-full mb-4',
        isUser && 'justify-end'
      )}
    >
      {!isUser && (
        <>
          {message.role === 'assistant' ? (
            <Image
              src={avatarSrc}
              alt="The avatar of the AI assistant chat partner"
              className="flex-shrink-0 w-12 h-12 rounded-full bg-background object-cover"
              width={48}
              height={48}
            />
          ) : (
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-background flex items-center justify-center">
              S
            </div>
          )}
        </>
      )}

      <div
        className={cn(
          'flex-1 rounded-lg shadow-sm p-4',
          isUser
            ? 'bg-background'
            : 'bg-background prose py-0 dark:prose-invert dark:[&_strong]:text-white'
        )}
      >
        <div className={cn(!isUser && 'text-foreground')}>
          {isUser ? (
            <div
              dangerouslySetInnerHTML={{
                __html: marked(message.text.replaceAll('\n', '<br />')),
              }}
            />
          ) : (
            <ThinkAnswerBlock response={message.text} />
          )}
        </div>
      </div>

      {isUser && (
        <Image
          src={profilePicture ?? '/ai.jpeg'}
          alt="User Profile Picture"
          className="flex-shrink-0 w-12 h-12 rounded-full bg-background object-cover"
          width={48}
          height={48}
        />
      )}
    </div>
  );
}
