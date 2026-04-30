'use client';

import { SidebarGroup, SidebarGroupContent, SidebarMenu } from '../ui/sidebar';
import { Chat } from '@/frontend/types';
import { useEffect } from 'react';
import { getChats, useDeleteChat } from '@/frontend/queries/chats';
import { useRouter, usePathname } from 'next/navigation';
import { useAppSelector, useAppDispatch } from '@/frontend/store/hooks/hooks';
import {
  selectAppState,
  setChats,
  selectChats,
  setAppState,
} from '@/frontend/store/reducer/app_reducer';
import { groupChatsByDate } from '@/frontend/utils/sort';
import DeleteChatDialog from './chat/DeleteChatDialog';
import ChatsCollectionElement from './chat/ChatsCollectionElement';
import { useInView } from 'react-intersection-observer';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useState } from 'react';

/**
 * ChatsNavigation component handles the display and management of chat navigation.
 * It allows users to view, sort, and delete chats.
 *
 * @component
 * @returns {JSX.Element} The rendered ChatsNavigation component.
 */
export default function ChatsNavigation() {
  const dispatch = useAppDispatch();
  const chats = useAppSelector(selectChats) || [];
  const appState = useAppSelector(selectAppState);

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<string | null>(null);

  const { ref, inView } = useInView({
    threshold: 0.1,
  });

  const router = useRouter();
  const pathname = usePathname();
  const currentChatId = pathname.split('/').pop(); // Get the last segment of the URL which is the chat ID

  const deleteChat = useDeleteChat(chatToDelete || '');

  const { fetchNextPage, hasNextPage, isFetchingNextPage, status } =
    useInfiniteQuery({
      queryKey: ['chats'],
      queryFn: ({ pageParam = 1 }) => getChats(10, pageParam),
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      getNextPageParam: (lastPage, _) => {
        if (lastPage.page >= lastPage.pages) return undefined;
        return lastPage.page + 1;
      },
      initialPageParam: 1,
    });

  /**
   * Handles the deletion of a chat by setting the chat ID to be deleted
   * and opening the delete confirmation dialog.
   *
   * @param chatId - The ID of the chat to be deleted.
   */
  const handleDelete = (chatId: string) => {
    setChatToDelete(chatId);
    setIsDeleteDialogOpen(true);
  };

  /**
   * Confirms the deletion of a chat and performs the delete operation.
   */
  const confirmDelete = () => {
    deleteChat.mutate(undefined, {
      onSuccess: () => {
        // Remove deleted chat from redux state
        const remaining = chats.filter(c => c.id !== chatToDelete);
        dispatch(setChats(remaining));
        router.push('/');
        setIsDeleteDialogOpen(false);
        setChatToDelete(null);
      },
      onError: error => {
        console.error('Failed to delete chat:', error);
      },
    });
  };

  // Effect hook to fetch chats when the component mounts
  useEffect(() => {
    if (appState === 'loading') {
      fetchNextPage().then(result => {
        const newChats = result?.data?.pages.flatMap(page => page.items) || [];
        dispatch(setChats(newChats));
        dispatch(setAppState('idle'));
      });
    }
  }, [appState, fetchNextPage, dispatch]);

  // Effect hook to fetch next page when the load more element comes into view
  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage().then(result => {
        const newChats = result?.data?.pages.flatMap(page => page.items) || [];
        dispatch(setChats(newChats));
      });
    }
  }, [inView, hasNextPage, fetchNextPage, isFetchingNextPage, dispatch]);

  const sortedChats: Chat[] = chats;
  const groupedChats = groupChatsByDate(sortedChats as Chat[]);
  const isLoading = appState === 'loading' || status === 'pending';

  return (
    <SidebarGroup className="p-0">
      <SidebarGroupContent>
        <SidebarMenu>
          {isLoading && !chats.length && (
            <div className="space-y-3 p-4">
              {[...Array(7)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <div
                    className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700"
                    style={{ width: `100%` }}
                  />
                </div>
              ))}
            </div>
          )}

          {!isLoading &&
            Object.entries(groupedChats).map(([date, chats]) => (
              <ChatsCollectionElement
                key={date}
                date={date}
                chats={chats}
                currentChatId={currentChatId}
                handleDelete={handleDelete}
              />
            ))}

          {/* Load more indicator observed by intersection observer */}
          <div
            ref={ref}
            className="py-4 text-center text-sm text-muted-foreground"
          >
            {isFetchingNextPage ? (
              <div className="flex items-center justify-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
                <span>Lädt mehr Chats...</span>
              </div>
            ) : hasNextPage ? (
              <div className="flex items-center justify-center gap-2">
                <span>Nach unten scrollen für mehr</span>
                <svg
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </div>
            ) : chats.length > 0 ? (
              <span className="text-sm text-muted-foreground">
                Keine weiteren Chats verfügbar 😢
              </span>
            ) : null}
          </div>

          <DeleteChatDialog
            confirmDelete={confirmDelete}
            isDeleteDialogOpen={isDeleteDialogOpen}
            setIsDeleteDialogOpen={setIsDeleteDialogOpen}
          />
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
