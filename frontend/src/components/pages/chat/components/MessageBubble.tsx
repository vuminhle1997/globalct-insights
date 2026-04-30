'use client';

import Image from 'next/image';
import { marked } from 'marked';
import { cn } from '@/lib/utils';
import ThinkAnswerBlock from './ThinkAnswerBlock';
import { Message } from '@/frontend/types';
import { motion } from 'framer-motion';

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
    <motion.div
      ref={observerRef}
      className={cn(
        'flex justify-start gap-4 w-full mb-4',
        isUser && 'justify-end'
      )}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {!isUser && (
        <>
          {message.role === 'assistant' ? (
            <Image
              src={avatarSrc}
              alt="The avatar of the AI assistant chat partner"
              className="w-12 h-12 rounded-full bg-background object-cover"
              width={48}
              height={48}
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-background flex items-center justify-center">
              S
            </div>
          )}
        </>
      )}

      <div
        className={cn(
          'flex-1 rounded-lg shadow-sm p-4',
          isUser ? 'bg-background' : 'bg-background '
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
            <div className="flex-1 rounded-lg">
              <div className="py-0 dark:prose-invert dark:[&_strong]:text-white">
                <ThinkAnswerBlock response={message.text} />
              </div>
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <Image
          src={profilePicture ?? '/ai.jpeg'}
          alt="User Profile Picture"
          className="shrink-0 w-12 h-12 rounded-full bg-background object-cover"
          width={48}
          height={48}
        />
      )}
    </motion.div>
  );
}
