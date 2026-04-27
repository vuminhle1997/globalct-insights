'use client';

import React, { useCallback, useEffect } from 'react';
import {
  selectAuthorized,
  selectChats,
  selectShowCommands,
  setAppState,
  setFavouriteChats,
  setLLMModels,
  setProfilePicture,
  setShowCommands,
  setUser,
  useAppDispatch,
  useAppSelector,
} from '@/frontend';
import { SidebarProvider } from '@/components/ui/sidebar';
import { useGetProfilePicture } from '@/frontend/queries/avatar';
import { useGetFavourites } from '@/frontend/queries/favourites';
import { useAuth } from '@/frontend/queries';
import SideBarNavigation from '../navigations/SideBarNavigation';
import { getChatsByTitle } from '@/frontend/queries/chats';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/solid';
import { Chat } from '@/frontend/types';
import { v4 } from 'uuid';
import { useRouter } from 'next/navigation';
import { useGetModels } from '@/frontend/queries/models';

/**
 * LayoutProvider component is responsible for providing layout context and managing
 * application state based on user authorization and fetched data.
 *
 * @param {Object} props - The component props.
 * @param {React.ReactNode} props.children - The child components to be rendered within the layout.
 *
 * @returns {JSX.Element} The rendered layout component.
 *
 * @remarks
 * This component uses several hooks to fetch data and update the application state:
 * - `useAppDispatch` to dispatch actions to the Redux store.
 * - `useAppSelector` to select the authorization state from the Redux store.
 * - `useAuth` to fetch authentication data.
 * - `useGetProfilePicture` to fetch the user's profile picture.
 * - `useGetFavourites` to fetch favourite chats data.
 *
 * The component uses `useEffect` hooks to dispatch actions when the fetched data changes:
 * - Sets the profile picture when `profilePicture` changes.
 * - Sets the chat data when `data` changes.
 * - Sets the favourite chats when `favouriteChats` changes.
 * - Sets the user data and application state based on authentication data.
 *
 * If the user is authorized, the component renders the `SidebarProvider` with a sidebar
 * and the child components. Otherwise, it only renders the child components.
 */
export default function LayoutProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const isAuthorized = useAppSelector(selectAuthorized);
  const showCommands = useAppSelector(selectShowCommands);
  const chats = useAppSelector(selectChats);

  const { data: authData, isLoading, error } = useAuth();
  const { profilePicture } = useGetProfilePicture();
  const { data: favouriteChats } = useGetFavourites(50, 1);
  const { data: models } = useGetModels();

  const [value, setValue] = React.useState('');
  const [searchedChats, setSearchedChats] = React.useState<Chat[]>(chats || []);

  useEffect(() => {
    if (value.length > 0) {
      getChatsByTitle(value)
        .then(chats => {
          setSearchedChats(chats);
        })
        .catch(error => {
          console.error('Error searching chats:', error);
          setSearchedChats(chats || []);
        });
    } else {
      setSearchedChats(chats || []);
    }
  }, [value, chats]);

  /**
   * Toggles the visibility of the commands and resets the input value.
   *
   * This function uses the `useCallback` hook to memoize the callback,
   * ensuring it only changes when `dispatch` or `showCommands` dependencies change.
   *
   * @remarks
   * - Dispatches an action to update the `showCommands` state in the global store.
   * - Resets the local input value to an empty string.
   *
   * @dependencies
   * - `dispatch`: The Redux dispatch function to trigger state updates.
   * - `showCommands`: A boolean indicating the current visibility state of commands.
   */
  const handleShowCommand = useCallback(() => {
    dispatch(setShowCommands(!showCommands));
    setValue('');
  }, [dispatch, showCommands]);

  /**
   * Handles the click event for a chat item.
   * Clears the current input value and navigates to the chat page
   * corresponding to the selected chat's ID.
   *
   * @param chat - The selected chat object containing the chat ID.
   */
  const handleClick = (chat: Chat) => {
    setValue('');
    router.push(`/chat/${chat.id}`);
  };

  useEffect(() => {
    if (profilePicture) {
      dispatch(setProfilePicture(profilePicture));
    }
  }, [profilePicture, dispatch]);

  useEffect(() => {
    if (favouriteChats) {
      dispatch(
        setFavouriteChats(favouriteChats.items.map(favorite => favorite.chat))
      );
    }
  }, [favouriteChats, dispatch]);

  useEffect(() => {
    if (authData && !isLoading && !error) {
      dispatch(setUser(authData.user));
    } else if (error) {
      dispatch(setAppState('failed'));
    }
  }, [authData, isLoading, error, dispatch]);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        dispatch(setShowCommands(!showCommands));
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [dispatch, showCommands]);

  useEffect(() => {
    if (models) {
      dispatch(setLLMModels(models.filter(model => model.type === 'llm')));
    }
  }, [models, dispatch]);

  return isAuthorized ? (
    <SidebarProvider
      style={
        {
          '--sidebar-width': '18rem',
          '--sidebar-width-icon': '6rem',
        } as React.CSSProperties
      }
    >
      <div className="flex h-screen w-screen">
        <SideBarNavigation />
        {children}
      </div>
      {showCommands && (
        <CommandDialog open={showCommands} onOpenChange={handleShowCommand}>
          <CommandInput
            placeholder="Tippe, um ein Chat zu suchen ..."
            value={value}
            onValueChange={(value: string) => setValue(value)}
          />
          <CommandList>
            <CommandEmpty>Keine Chats gefunden.</CommandEmpty>
            <CommandGroup heading="Chathistorie">
              {searchedChats.map(chat => (
                <div
                  key={chat.id}
                  onClick={() => handleClick(chat)}
                  className=""
                >
                  <div className="flex items-center w-full gap-4">
                    <ChatBubbleLeftRightIcon className="h-6 w-6 text-primary" />
                    <CommandItem className="w-full" key={v4()}>
                      {chat.title}
                    </CommandItem>
                  </div>
                </div>
              ))}
            </CommandGroup>
          </CommandList>
        </CommandDialog>
      )}
    </SidebarProvider>
  ) : (
    <>{children}</>
  );
}
