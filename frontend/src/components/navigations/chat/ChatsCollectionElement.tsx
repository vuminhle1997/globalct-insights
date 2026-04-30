'use client';

import React from 'react';
import { Chat } from '@/frontend/types';
import { getRelativeDate } from '@/frontend/utils/date';
import ChatNavigationItem from './ChatNavigationItem';

export interface ChatsCollectionElementProps {
  date: string;
  chats: Chat[];
  currentChatId?: string;
  handleDelete: (chatId: string) => void;
}

/**
 * ChatsCollectionElement component renders a collection of chat items grouped by date.
 * Each chat item includes options to edit or delete the chat.
 *
 * @param {ChatsCollectionElementProps} props - The properties for the component.
 * @param {string} props.date - The date for the chat collection.
 * @param {Chat[]} props.chats - The list of chat items.
 * @param {string} props.currentChatId - The ID of the currently active chat.
 * @param {function} props.handleDelete - The function to handle the deletion of a chat.
 *
 * @returns {JSX.Element} The rendered ChatsCollectionElement component.
 */
export default function ChatsCollectionElement({
  date,
  chats,
  currentChatId,
  handleDelete,
}: ChatsCollectionElementProps) {
  const [isDialogOpen, setIsDialogOpen] = React.useState(false);
  const [selectedChat, setSelectedChat] = React.useState<Chat | null>(null);

  return (
    <div key={date}>
      <div className="date-separator font-bold text-center py-4">
        {getRelativeDate(date)}
      </div>
      {chats.map(chat => (
        <ChatNavigationItem
          key={chat.id}
          chat={chat}
          slug={currentChatId || ''}
          isDialogOpen={isDialogOpen}
          setIsDialogOpen={setIsDialogOpen}
          selectedChat={selectedChat}
          setSelectedChat={setSelectedChat}
          handleDelete={handleDelete}
          prefix={date}
        />
      ))}
    </div>
  );
}
