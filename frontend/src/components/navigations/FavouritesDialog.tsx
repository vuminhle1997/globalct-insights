'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { HeartIcon } from '@heroicons/react/24/solid';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import { selectFavouriteChats, useAppSelector } from '@/frontend';

/**
 * FavouritesDialog component renders a button that triggers a dialog displaying a list of favourite chats.
 *
 * The component uses the following hooks and components:
 * - `useAppSelector` to select favourite chats from the Redux store.
 * - `TooltipProvider`, `Tooltip`, `TooltipTrigger`, and `TooltipContent` from a tooltip library to provide a tooltip for the button.
 * - `Dialog`, `DialogTrigger`, `DialogContent`, `DialogHeader`, and `DialogTitle` from a dialog library to create a modal dialog.
 * - `Button` component to create a button with specific styles.
 * - `HeartIcon` component to display a heart icon.
 * - `Link` component to create navigable links to individual chat pages.
 *
 * The dialog displays a list of favourite chats with their title and last interaction date.
 * If there are no favourite chats, a message indicating no favourite chats are available is displayed.
 *
 * @returns {JSX.Element} The rendered FavouritesDialog component.
 */
const FavouritesDialog = () => {
  const favouriteChats = useAppSelector(selectFavouriteChats);
  return (
    <div className="absolute top-4 right-4 z-50">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Dialog>
              <DialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-15 w-15 rounded-full bg-primary/10 hover:bg-primary/20"
                >
                  <HeartIcon className="h-10 w-10 text-primary text-4xl" />
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-106.25">
                <DialogHeader>
                  <DialogTitle>Favorisierte Chats</DialogTitle>
                </DialogHeader>
                <div className="mt-4 space-y-2">
                  {favouriteChats?.map(favorite => (
                    <Link
                      key={favorite.id}
                      href={`/chat/${favorite.id}`}
                      className="block p-3 border rounded-lg hover:bg-accent cursor-pointer"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center">
                          <HeartIcon className="h-8 w-8 text-primary" />
                        </div>
                        <div>
                          <h4 className="font-medium">{favorite.title}</h4>
                          <p className="text-sm text-muted-foreground">
                            {format(
                              new Date(favorite.last_interacted_at),
                              'dd.MM.yyyy',
                              { locale: de }
                            )}
                          </p>
                        </div>
                      </div>
                    </Link>
                  ))}
                  {(!favouriteChats || favouriteChats.length === 0) && (
                    <p className="text-center text-muted-foreground py-4">
                      Keine favorisierten Chats vorhanden
                    </p>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </TooltipTrigger>
          <TooltipContent className="dark:bg-accent bg-primary border-2 border-white shadow-sm">
            <p>Favorisierte Chats</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
};

export default FavouritesDialog;
