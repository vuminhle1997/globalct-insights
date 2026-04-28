'use client';

import { Chat } from '@/frontend/types';
import Image from 'next/image';
import React from 'react';

export interface FavouritesChatNavigationProps {
  favouriteChats: Chat[];
  useAsTemplate: (chat: Chat) => void;
}

/**
 * A React component that renders a list of favorite chats with the ability to use them as templates.
 *
 * @component
 * @param {FavouritesChatNavigationProps} props - The props for the component.
 * @param {Array<{ id: string; title: string; description?: string }>} props.favouriteChats -
 * An array of favorite chat objects, each containing an `id`, `title`, and optional `description`.
 * @param {(chat: { id: string; title: string; description?: string }) => void} props.useAsTemplate -
 * A callback function that is triggered when a favorite chat is clicked, passing the selected chat as an argument.
 *
 * @returns {JSX.Element} A React fragment containing a styled list of favorite chats.
 *
 * @example
 * ```tsx
 * const favouriteChats = [
 *   { id: '1', title: 'Chat 1', description: 'Description for Chat 1' },
 *   { id: '2', title: 'Chat 2' },
 * ];
 *
 * const handleUseAsTemplate = (chat) => {
 *   console.log('Using chat as template:', chat);
 * };
 *
 * <FavouritesChatNavigation
 *   favouriteChats={favouriteChats}
 *   useAsTemplate={handleUseAsTemplate}
 * />
 * ```
 */
export default function FavouritesChatNavigation({
  favouriteChats,
  useAsTemplate: changeTemplate,
}: FavouritesChatNavigationProps) {
  return (
    <React.Fragment>
      <div className="space-y-2">
        {favouriteChats.map(existingChat => (
          <div
            key={existingChat.id}
            className="p-3 border rounded-lg hover:bg-accent cursor-pointer"
            onClick={() => changeTemplate(existingChat)}
          >
            <div className="grid grid-cols-4">
              <div className="col-span-1 content-center">
                <Image
                  src={`${
                    process.env.NEXT_PUBLIC_BACKEND_URL
                  }/uploads/avatars/${existingChat.avatar_path.split('/').pop()}`}
                  width={50}
                  height={50}
                  className="rounded-full"
                  alt={`Avatar of ${existingChat.title}`}
                />
              </div>
              <div className="col-span-3">
                <h4 className="font-medium">{existingChat.title}</h4>
                {existingChat.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {existingChat.description}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </React.Fragment>
  );
}
