'use client';

import React, { useCallback } from 'react';
import { ChevronDown } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '../ui/collapsible';
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
} from '@/components/ui/sidebar';
import { HeartIcon } from '@heroicons/react/24/solid';
import {
  selectAppState,
  selectFavouriteChats,
  useAppSelector,
} from '@/frontend';
import { Chat } from '@/frontend/types';

import { useDeleteChat } from '@/frontend/queries/chats';
import { useParams, useRouter } from 'next/navigation';
import DeleteChatDialog from './chat/DeleteChatDialog';
import ChatNavigationItem from './chat/ChatNavigationItem';

/**
 * A React component that renders a collapsible sidebar navigation menu for managing
 * and interacting with favorite chats. It includes functionality for viewing, editing,
 * and deleting chats, as well as navigation to specific chat pages.
 *
 * @component
 * @returns {JSX.Element} The rendered FavouritesNavigation component.
 *
 * @remarks
 * - This component uses `useParams` to extract the current chat slug from the URL.
 * - It uses `useRouter` for navigation and page reloads.
 * - The `useAppSelector` hook is used to retrieve the list of favorite chats from the Redux store.
 * - The `useDeleteChat` hook is used to handle chat deletion.
 *
 * @example
 * ```tsx
 * <FavouritesNavigation />
 * ```
 *
 * @dependencies
 * - `Collapsible`, `CollapsibleTrigger`, `CollapsibleContent` from a collapsible UI library.
 * - `SidebarGroup`, `SidebarGroupLabel`, `SidebarGroupContent`, `SidebarMenu`, `SidebarMenuItem`, `SidebarMenuButton` for sidebar layout.
 * - `Dialog`, `DialogTrigger` for modal dialogs.
 * - `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem` for dropdown functionality.
 * - `TooltipProvider`, `Tooltip`, `TooltipTrigger`, `TooltipContent` for tooltips.
 * - `DeleteChatDialog` for confirming chat deletion.
 * - `ChatEntryForm` for editing chat details.
 *
 * @state
 * - `isDialogOpen` (`boolean`): Tracks whether the edit dialog is open.
 * - `selectedChat` (`Chat | null`): Stores the currently selected chat for editing.
 * - `chatToDelete` (`string | null`): Stores the ID of the chat to be deleted.
 * - `isDeleteDialogOpen` (`boolean`): Tracks whether the delete confirmation dialog is open.
 *
 * @methods
 * - `handleDelete(chatId: string)`: Prepares the component state for deleting a chat.
 * - `confirmDelete()`: Executes the chat deletion process and handles success or error states.
 *
 * @hooks
 * - `useParams`: Extracts the `slug` parameter from the URL.
 * - `useRouter`: Provides navigation and page reload functionality.
 * - `useAppSelector`: Selects the list of favorite chats from the Redux store.
 * - `useDeleteChat`: Custom hook for deleting a chat.
 */
export default function FavouritesNavigation() {
  const router = useRouter();
  const favouriteChats = useAppSelector(selectFavouriteChats);
  const appState = useAppSelector(selectAppState);

  const { slug } = useParams();

  const [isDialogOpen, setIsDialogOpen] = React.useState(false);
  const [selectedChat, setSelectedChat] = React.useState<Chat | null>(null);
  const [chatToDelete, setChatToDelete] = React.useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);

  const deleteChat = useDeleteChat(chatToDelete || '');

  /**
   * Handles the deletion of a chat by setting the chat ID to be deleted
   * and opening the delete confirmation dialog.
   *
   * @param chatId - The unique identifier of the chat to be deleted.
   */
  const handleDelete = useCallback((chatId: string) => {
    setChatToDelete(chatId);
    setIsDeleteDialogOpen(true);
  }, []);

  /**
   * Confirms the deletion of a chat and triggers the deleteChat mutation.
   *
   * On successful deletion:
   * - Redirects the user to the home page ('/').
   * - Reloads the browser window to ensure the application state is updated.
   *
   * On error:
   * - Logs the error to the console with a descriptive message.
   */
  const confirmDelete = () => {
    deleteChat.mutate(undefined, {
      onSuccess: () => {
        router.push('/');
        window.location.reload();
      },
      onError: error => {
        console.error('Failed to delete chat:', error);
      },
    });
  };

  return (
    <>
      <Collapsible defaultOpen className="group/collapsible">
        <SidebarGroup className="p-0">
          <SidebarGroupLabel asChild>
            <CollapsibleTrigger>
              {appState === 'idle' ? (
                <>
                  <div className="flex gap-2">
                    <HeartIcon className="h-4 w-4" />
                    <span className="text-md">Ihre favorisierten Chats</span>
                  </div>
                  <ChevronDown className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-180" />
                </>
              ) : (
                <div className="flex gap-2">
                  <HeartIcon className="h-4 w-4 animate-pulse" />
                  <div className="h-4 w-50 my-1 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
                </div>
              )}
            </CollapsibleTrigger>
          </SidebarGroupLabel>
          <CollapsibleContent asChild>
            <SidebarGroupContent>
              <SidebarMenu>
                {favouriteChats &&
                  favouriteChats.map((chat, index) => {
                    return (
                      <ChatNavigationItem
                        key={chat.id}
                        chat={chat}
                        slug={(slug as string) || ''}
                        isDialogOpen={isDialogOpen}
                        setIsDialogOpen={setIsDialogOpen}
                        selectedChat={selectedChat}
                        setSelectedChat={setSelectedChat}
                        handleDelete={handleDelete}
                        prefix={'favourite'}
                      />
                    );
                  })}
              </SidebarMenu>
            </SidebarGroupContent>
          </CollapsibleContent>
        </SidebarGroup>
      </Collapsible>
      <DeleteChatDialog
        confirmDelete={confirmDelete}
        isDeleteDialogOpen={isDeleteDialogOpen}
        setIsDeleteDialogOpen={setIsDeleteDialogOpen}
      />
    </>
  );
}
