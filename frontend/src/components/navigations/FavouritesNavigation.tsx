'use client';

import React, { useCallback } from 'react';
import { ChevronDown } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '../ui/collapsible';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar';
import {
  EllipsisHorizontalIcon,
  HeartIcon,
  PencilIcon,
  TrashIcon,
} from '@heroicons/react/24/solid';
import {
  selectAppState,
  selectFavouriteChats,
  useAppSelector,
} from '@/frontend';
import Link from 'next/link';
import { Chat } from '@/frontend/types';
import { Dialog, DialogTrigger } from '../ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';
import ChatEntryForm from '../form/ChatEntryForm';
import { useDeleteChat } from '@/frontend/queries/chats';
import { useParams, useRouter } from 'next/navigation';
import DeleteChatDialog from './chat/DeleteChatDialog';
import Image from 'next/image';

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
                // show loading state with tailwind skeleton
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
                      <SidebarMenuItem
                        className={`flex flex-row items-start justify-center px-4 py-2 min-h-[50px] ${
                          chat.id === slug
                            ? 'bg-primary/10 dark:bg-accent/50'
                            : ''
                        }`}
                        key={`favourite-${index}`}
                      >
                        <Link
                          href={`/chat/${chat.id}`}
                          className="flex-1 flex justify-center items-center"
                        >
                          <Image
                            src={`${
                              process.env.NEXT_PUBLIC_BACKEND_URL
                            }/uploads/avatars/${chat.avatar_path.split('/').pop()}`}
                            alt={`Avatar of ${chat.title}`}
                            className="h-10 w-10 rounded-full mr-2 border-2 dark:border-0 border-primary"
                            width={40}
                            height={40}
                          />
                          <SidebarMenuButton className="w-full text-left fit-content h-full break-words whitespace-normal py-1">
                            {chat.title}
                          </SidebarMenuButton>
                        </Link>
                        <Dialog
                          open={isDialogOpen && selectedChat?.id === chat.id}
                          onOpenChange={open => {
                            setIsDialogOpen(open);
                            if (!open) setSelectedChat(null);
                          }}
                        >
                          <DropdownMenu>
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <DropdownMenuTrigger
                                    className="hover:bg-accent ml-2 w-[30px] h-[30px] 
                            flex justify-center items-center rounded-md cursor-pointer mt-1"
                                  >
                                    <EllipsisHorizontalIcon className="h-4 w-4" />
                                  </DropdownMenuTrigger>
                                </TooltipTrigger>
                                <TooltipContent className="dark:bg-accent bg-primary border-2 border-white shadow-sm">
                                  <p>Chat editieren</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                            <DropdownMenuContent>
                              <DialogTrigger asChild>
                                <DropdownMenuItem
                                  onSelect={() => {
                                    setSelectedChat(chat);
                                    setIsDialogOpen(true);
                                  }}
                                >
                                  <PencilIcon className="h-4 w-4" /> Editieren
                                </DropdownMenuItem>
                              </DialogTrigger>
                              <DropdownMenuItem
                                className="text-destructive"
                                onSelect={() => handleDelete(chat.id)}
                              >
                                <TrashIcon className="h-4 w-4" /> Löschen
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                          {selectedChat && (
                            <ChatEntryForm
                              chat={selectedChat}
                              onSuccess={() => {
                                setIsDialogOpen(false);
                                setSelectedChat(null);
                                window.location.reload();
                              }}
                            />
                          )}
                        </Dialog>
                      </SidebarMenuItem>
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
