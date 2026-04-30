'use client';

import { Chat, Favourite } from '@/frontend/types';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { v4 } from 'uuid';
import { Message } from '@/frontend/types';
import { getMessages } from '@/frontend/queries/messages';
import { useInView } from 'react-intersection-observer';
import { useInfiniteQuery, UseMutationResult } from '@tanstack/react-query';
import { useSidebar } from '@/components/ui/sidebar';
import { Bars3Icon } from '@heroicons/react/24/solid';
import Image from 'next/image';
import { useIsMobile } from '@/hooks/use-mobile';
import ChatSettingsDialog, {
  ChatSettingsDialogProps,
} from './components/ChatSettingsDialog';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import ThinkAnswerBlock from './components/ThinkAnswerBlock';
import ReasoningIndicator from './components/ReasoningIndicator';
import MessageBubble from './components/MessageBubble';
import ChatSuggestions from './components/ChatSuggestions';

export interface ChatContainerProps {
  chatContainerRef: React.RefObject<HTMLDivElement | null>;
  chat: Chat;
  messageText: string;
  reset: (message: { message: string }) => void;
  profilePicture?: string | null;
  pendingMessage: string | null;
  isSettingsDialogOpen: boolean;
  setIsSettingsDialogOpen: React.Dispatch<React.SetStateAction<boolean>>;
  slug: string;
  setFavouriteAlert: React.Dispatch<
    React.SetStateAction<{
      show: boolean;
      success: boolean;
    }>
  >;
  postFavourite: UseMutationResult<Favourite, Error, string, unknown>;
  deleteFavourite: UseMutationResult<Favourite, Error, string, unknown>;
  setSelectedChat: React.Dispatch<React.SetStateAction<Chat | null>>;
  setIsDialogOpen: React.Dispatch<React.SetStateAction<boolean>>;
  handleDelete: () => void;

  response: string;
  isStreaming: boolean;
  scrollToBottom: () => void;
}

/**
 * ChatContainer component is responsible for rendering the chat interface,
 * including the chat messages, user interactions, and chat settings. It
 * handles fetching messages, managing the chat state, and rendering the
 * appropriate UI elements based on the chat's current state.
 *
 * @param {ChatContainerProps} props - The properties passed to the ChatContainer component.
 * @param {React.RefObject<HTMLDivElement>} props.chatContainerRef - A reference to the chat container DOM element.
 * @param {Chat} props.chat - The current chat object containing chat details and messages.
 * @param {string} props.messageText - The current text of the user's message input.
 * @param {() => void} props.reset - A function to reset the chat input with a predefined message.
 * @param {string} props.profilePicture - The URL of the user's profile picture.
 * @param {string} props.pendingMessage - The message currently being typed by the user.
 * @param {(id: string) => void} props.deleteFavourite - A function to delete a favorite chat.
 * @param {(id: string) => void} props.handleDelete - A function to handle the deletion of a chat.
 * @param {boolean} props.isSettingsDialogOpen - A flag indicating whether the chat settings dialog is open.
 * @param {(id: string) => void} props.postFavourite - A function to mark a chat as favorite.
 * @param {(alert: string) => void} props.setFavouriteAlert - A function to set an alert for favorite actions.
 * @param {(isOpen: boolean) => void} props.setIsDialogOpen - A function to toggle the dialog's open state.
 * @param {(isOpen: boolean) => void} props.setIsSettingsDialogOpen - A function to toggle the settings dialog's open state.
 * @param {(chat: Chat) => void} props.setSelectedChat - A function to set the currently selected chat.
 * @param {string} props.slug - A unique identifier for the chat.
 * @param {boolean} props.isStreaming - A flag indicating whether the assistant is currently streaming a response.
 * @param {string} props.response - The assistant's response text.
 * @param {() => void} props.scrollToBottom - A function to scroll the chat container to the bottom.
 *
 * @returns {JSX.Element} The rendered ChatContainer component.
 */
export default function ChatContainer({
  chatContainerRef,
  chat,
  messageText,
  reset,
  profilePicture,
  pendingMessage,
  deleteFavourite,
  handleDelete,
  isSettingsDialogOpen,
  postFavourite,
  setFavouriteAlert,
  setIsDialogOpen,
  setIsSettingsDialogOpen,
  setSelectedChat,
  slug,
  isStreaming,
  response,
  scrollToBottom,
}: ChatContainerProps) {
  const isMobile = useIsMobile();
  const { ref, inView } = useInView();
  const { open, toggleSidebar } = useSidebar();

  const [submittedMessages, setSubmittedMessages] = useState<Message[]>([]);

  // Track streaming transition and last processed pending message to avoid duplicates
  const lastProcessedPendingRef = useRef<string | null>(null);
  const prevIsStreamingRef = useRef<boolean>(isStreaming);

  const {
    data: messagesFetched,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: ['messages', chat.id],
    queryFn: ({ pageParam = 1 }) =>
      getMessages({ size: 10, page: pageParam, chatId: chat.id }),
    getNextPageParam: lastPage => {
      if (lastPage.page >= lastPage.pages) return undefined;
      return lastPage.page + 1;
    },
    initialPageParam: 1,
    enabled: !!chat.id,
  });

  /**
   * Toggles the state of the sidebar by invoking the `toggleSidebar` function.
   * This function is memoized using `useCallback` to prevent unnecessary re-renders.
   */
  const handleSideBarToggle = useCallback(() => {
    toggleSidebar();
  }, [toggleSidebar]);

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, fetchNextPage]);

  useEffect(() => {
    if (messagesFetched && chatContainerRef.current) {
      // Only scroll to bottom if we're on the first page (most recent messages)
      if (messagesFetched.pages.length === 1) {
        chatContainerRef.current.scrollTop =
          chatContainerRef.current.scrollHeight;
      }
    }
  }, [messagesFetched, chatContainerRef]);

  // Add submitted messages only once when streaming finishes (transition true -> false)
  useEffect(() => {
    const wasStreaming = prevIsStreamingRef.current;

    if (wasStreaming && !isStreaming && pendingMessage) {
      // Only process if this pending message hasn't been handled yet
      if (lastProcessedPendingRef.current !== pendingMessage) {
        const userMessage: Message = {
          id: v4(),
          role: 'user',
          text: pendingMessage,
          created_at: new Date().toISOString(),
          block_type: 'text',
        };
        const assistantMessage: Message = {
          id: v4(),
          role: 'assistant',
          text: response,
          created_at: new Date().toISOString(),
          block_type: 'text',
        };
        setSubmittedMessages(prev => [assistantMessage, userMessage, ...prev]);
        lastProcessedPendingRef.current = pendingMessage;
        setTimeout(() => {
          scrollToBottom();
        }, 750);
      }
    }

    // Update previous streaming state for next render
    prevIsStreamingRef.current = isStreaming;
  }, [isStreaming, pendingMessage, response, scrollToBottom]);

  const avatarSrc = chat.avatar_path
    ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/uploads/avatars/${chat.avatar_path.split('/').pop()}`
    : '/ai.jpeg';

  const chatSettingsProps: ChatSettingsDialogProps = {
    chat: chat!,
    deleteFavourite,
    handleDelete,
    isSettingsDialogOpen,
    postFavourite,
    setFavouriteAlert,
    setIsDialogOpen,
    setIsSettingsDialogOpen,
    setSelectedChat,
    slug,
  };

  return (
    <div ref={chatContainerRef} className="flex-1 overflow-y-auto">
      <div className="py-2 px-4 bg-background sticky top-0 left-0 w-full z-10 border-b">
        <div className="flex justify-between items-center">
          {(!open || isMobile) && (
            <Tooltip>
              <TooltipTrigger
                className="bg-primary dark:bg-background hover:bg-primary/50 border border-white p-4 rounded-sm top-4 left-4"
                onClick={handleSideBarToggle}
              >
                <Bars3Icon className="h-4 w-4 text-white" />
              </TooltipTrigger>
              <TooltipContent className="dark:bg-accent bg-primary border border-white shadow-sm">
                <p className="text-m">Seitenleiste öffnen</p>
              </TooltipContent>
            </Tooltip>
          )}
          <h1 className="lg:text-2xl text-xl" aria-label={chat.title}>
            {chat.title}
          </h1>
          <ChatSettingsDialog {...chatSettingsProps} />
        </div>
      </div>

      {(!chat.messages || chat.messages.length === 0) && !isStreaming && (
        <ChatSuggestions
          messageText={messageText}
          onSelect={text => reset({ message: text })}
        />
      )}

      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6 flex flex-col-reverse">
        {/* Reasoning indicator while streaming */}
        {isStreaming && <ReasoningIndicator />}

        {/* Live assistant response */}
        {isStreaming && response.length > 0 && (
          <div className="flex space-x-4 my-4">
            <Image
              src={avatarSrc}
              alt="The AI assistant's avatar typing indicator"
              className="flex-shrink-0 w-12 h-12 rounded-full bg-background object-cover"
              width={40}
              height={40}
            />
            <div className="rounded-lg shadow-sm p-4 bg-background dark:prose-invert dark:[&_strong]:text-white py-0">
              <div className="text-foreground">
                <ThinkAnswerBlock response={response} />
              </div>
            </div>
          </div>
        )}

        {/* Pending user message while streaming */}
        {isStreaming && pendingMessage && (
          <div className="flex space-x-4 justify-end my-4">
            <div className="bg-background rounded-lg shadow-sm p-4">
              <div
                dangerouslySetInnerHTML={{
                  __html: pendingMessage.replaceAll('\n', '<br />'),
                }}
              />
            </div>
            <Image
              src={profilePicture ?? '/ai.jpeg'}
              alt="User Profile Picture"
              className="flex-shrink-0 w-12 h-12 rounded-full bg-background object-cover"
              width={40}
              height={40}
            />
          </div>
        )}

        {/* Optimistically added messages (submitted this session) */}
        {submittedMessages.map(message => (
          <MessageBubble
            key={message.id}
            message={message}
            avatarSrc={avatarSrc}
            profilePicture={profilePicture}
          />
        ))}

        {/* Paginated historical messages */}
        {messagesFetched && messagesFetched.pages[0].items.length > 0 && (
          <>
            {messagesFetched.pages.map(page =>
              page.items.map((message, index) => {
                const isLastItem = page.items.length === index + 1;
                return (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    avatarSrc={avatarSrc}
                    profilePicture={profilePicture}
                    observerRef={isLastItem ? ref : undefined}
                  />
                );
              })
            )}
          </>
        )}
      </div>
    </div>
  );
}
