'use client';

import { Input } from '@/components/ui/input';
import { Chat } from '@/frontend/types';
import { SearchIcon } from 'lucide-react';
import Image from 'next/image';
import React from 'react';
import { useForm } from 'react-hook-form';

export interface FormData {
  searchChat: string;
}

export interface UsersChatNavigationProps {
  existingChats: Chat[];
  useAsTemplate: (chat: Chat) => void;
}

/**
 * A React component that renders a user interface for navigating and searching through
 * existing chat templates. Users can filter chats by title and select a chat to use as a template.
 *
 * @param {UsersChatNavigationProps} props - The props for the component.
 * @param {Array} props.existingChats - An array of existing chat objects, where each object contains
 *                                       information about the chat such as `id`, `title`, `description`,
 *                                       and `avatar_path`.
 * @param {Function} props.useAsTemplate - A callback function that is triggered when a user selects
 *                                         a chat to use as a template. The selected chat object is passed
 *                                         as an argument to this function.
 *
 * @returns {JSX.Element} A React fragment containing the UI for searching and selecting chats.
 */
export default function UsersChatNavigation({
  existingChats,
  useAsTemplate: changeAsTemplate,
}: UsersChatNavigationProps) {
  const {
    register,
    watch,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      searchChat: '',
    },
  });

  const searchTerm = watch('searchChat');

  return (
    <React.Fragment>
      <div className="space-y-2">
        <div
          id="search-chat-parent"
          className="flex gap-2 flex-row justify-center items-center"
        >
          <SearchIcon className="h-4 w-4 text-muted-foreground mt-1" />
          <Input
            placeholder="Chat nach Titel suchen . . ."
            {...register('searchChat')}
          />
        </div>
        {existingChats
          .filter(chats =>
            chats.title.toLowerCase().includes(searchTerm.toLowerCase())
          )
          .map(existingChat => (
            <div
              key={existingChat.id}
              className="p-3 border rounded-lg hover:bg-accent cursor-pointer"
              onClick={() => changeAsTemplate(existingChat)}
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
