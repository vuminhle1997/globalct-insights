'use client';

import React, { useCallback, useState } from 'react';
import {
  MagnifyingGlassCircleIcon,
  PencilIcon,
  XMarkIcon,
} from '@heroicons/react/24/solid';
import { Dialog, DialogTrigger } from '@/components/ui/dialog';
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  useSidebar,
} from '@/components/ui/sidebar';
import FooterNavigation from './FooterNavigation';
import ChatEntryForm from '../form/ChatEntryForm';
import ChatsNavigation from './ChatsNavigation';
import {
  selectAppState,
  selectShowCommands,
  setShowCommands,
  useAppDispatch,
  useAppSelector,
} from '@/frontend';
import { Tooltip, TooltipProvider } from '@radix-ui/react-tooltip';
import { TooltipContent, TooltipTrigger } from '../ui/tooltip';
import FavouritesNavigation from './FavouritesNavigation';

/**
 * SideBarNavigation component renders the sidebar navigation for the application.
 * It includes a header with a logo and a search bar, content with a button to create a new chat,
 * and a footer navigation.
 *
 * @returns {JSX.Element} The rendered sidebar navigation component.
 */
export default function SideBarNavigation() {
  const appState = useAppSelector(selectAppState);
  const dispatch = useAppDispatch();
  const showCommands = useAppSelector(selectShowCommands);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const { toggleSidebar } = useSidebar();

  /**
   * Toggles the visibility of the command dialog by dispatching an action
   * to update the `showCommands` state.
   *
   * @remarks
   * This function uses the `useCallback` hook to memoize the callback,
   * ensuring it only changes when `showCommands` or `dispatch` changes.
   *
   * @dependencies
   * - `showCommands`: The current state of the command dialog visibility.
   * - `dispatch`: The Redux dispatch function to trigger state updates.
   */
  const handleShowCommandDialog = useCallback(() => {
    dispatch(setShowCommands(!showCommands));
  }, [showCommands, dispatch]);

  /**
   * Toggles the state of the sidebar.
   * This function is memoized using `useCallback` to prevent unnecessary re-renders.
   * It depends on the `toggleSidebar` function provided as a dependency.
   */
  const handleSideBarToggle = useCallback(() => {
    toggleSidebar();
  }, [toggleSidebar]);

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex justify-between">
          <div className="toggle-menu">
            {' '}
            {appState === 'idle' ? (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger
                    className="bg-primary dark:bg-background hover:bg-primary/50 p-3 rounded-sm dark:border-white border border-white"
                    onClick={() => handleSideBarToggle()}
                  >
                    <XMarkIcon className="h-4 w-4 text-white" />
                  </TooltipTrigger>
                  <TooltipContent className="dark:bg-accent bg-primary border-2 border-white shadow-sm">
                    <p>Seitenleiste minimieren</p>
                    <div className="flex items-center justify-center text-center"></div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ) : (
              <div className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700 w-8"></div>
            )}
          </div>
          <div className="right-0 flex items-center justify-center">
            {appState === 'idle' ? (
              <React.Fragment>
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                  <DialogTrigger className="mx-4 bg-primary dark:bg-background hover:bg-primary/50 p-3 rounded-sm dark:border-white border border-white">
                    <PencilIcon className="w-4 text-white" />
                  </DialogTrigger>
                  <ChatEntryForm onCreated={() => setIsCreateOpen(false)} />
                </Dialog>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger
                      onClick={handleShowCommandDialog}
                      className="bg-primary dark:bg-background hover:bg-primary/50 p-3 rounded-sm dark:border-white border border-white"
                    >
                      <MagnifyingGlassCircleIcon className="h-4 w-4 text-white" />
                    </TooltipTrigger>
                    <TooltipContent className="dark:bg-accent bg-primary border-2 border-white shadow-sm">
                      <p>Bisherigen Chat suchen.</p>
                      <div className="flex items-center justify-center text-center">
                        <p>
                          Drücke <br /> ⌘+K (macOS) <br /> Strg+K
                          (Windows/Linux) <br />
                          um die Suche zu öffnen.
                        </p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </React.Fragment>
            ) : (
              <React.Fragment>
                <div className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700 w-8 mr-2"></div>
                <div className="h-8 animate-pulse rounded bg-gray-200 dark:bg-gray-700 w-8"></div>
              </React.Fragment>
            )}
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <FavouritesNavigation />
        <ChatsNavigation />
      </SidebarContent>

      <FooterNavigation />
    </Sidebar>
  );
}
