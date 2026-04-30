'use client';

import { Button } from '@/components/ui/button';
import { DialogHeader } from '@/components/ui/dialog';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  TooltipProvider,
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from '@/components/ui/tooltip';
import { Chat, Favourite } from '@/frontend/types';
import { UseMutationResult } from '@tanstack/react-query';
import { Settings, HeartIcon, PencilIcon, TrashIcon } from 'lucide-react';
import React from 'react';

export interface ChatSettingsDialogProps {
  isSettingsDialogOpen: boolean;
  setIsSettingsDialogOpen: React.Dispatch<React.SetStateAction<boolean>>;
  chat: Chat;
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
}

/**
 * ChatSettingsDialog component provides a dialog for chat settings, including options to
 * add/remove the chat from favourites, edit the chat, and delete the chat.
 *
 * @param {Object} props - The properties object.
 * @param {boolean} props.isSettingsDialogOpen - Indicates if the settings dialog is open.
 * @param {Function} props.setIsSettingsDialogOpen - Function to set the state of the settings dialog.
 * @param {Object} props.chat - The chat object containing chat details.
 * @param {string} props.slug - The unique identifier for the chat.
 * @param {Function} props.setFavouriteAlert - Function to set the favourite alert state.
 * @param {Object} props.postFavourite - Mutation function to add the chat to favourites.
 * @param {Object} props.deleteFavourite - Mutation function to remove the chat from favourites.
 * @param {Function} props.setSelectedChat - Function to set the selected chat for editing.
 * @param {Function} props.setIsDialogOpen - Function to set the state of the edit dialog.
 * @param {Function} props.handleDelete - Function to handle the deletion of the chat.
 * @returns {JSX.Element} The rendered ChatSettingsDialog component.
 */
export default function ChatSettingsDialog({
  isSettingsDialogOpen,
  setIsSettingsDialogOpen,
  chat,
  slug,
  setFavouriteAlert,
  postFavourite,
  deleteFavourite,
  setSelectedChat,
  setIsDialogOpen,
  handleDelete,
}: ChatSettingsDialogProps) {
  return (
    <Dialog open={isSettingsDialogOpen} onOpenChange={setIsSettingsDialogOpen}>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="bg-primary dark:bg-background dark:border
                    text-primary-foreground hover:bg-primary/50 p-4 rounded-sm border-white border dark:border-white"
              >
                <Settings className="h-4 w-4" />
              </Button>
            </DialogTrigger>
          </TooltipTrigger>
          <TooltipContent className="dark:bg-accent border border-white bg-primary shadow-sm">
            <p>Chat-Einstellungen</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Chat Einstellungen</DialogTitle>
        </DialogHeader>
        <div className="mt-4 space-y-4">
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={() => {
              if (chat.favourite) {
                deleteFavourite.mutate(slug, {
                  onSuccess: () => {
                    setFavouriteAlert({
                      show: true,
                      success: true,
                    });
                    setTimeout(() => {
                      window.location.reload();
                    }, 1500);
                  },
                  onError: (error: Error) => {
                    console.error(
                      'Failed to remove chat from favourites:',
                      error
                    );
                    setFavouriteAlert({
                      show: true,
                      success: false,
                    });
                  },
                });
              } else {
                postFavourite.mutate(slug, {
                  onSuccess: () => {
                    setFavouriteAlert({
                      show: true,
                      success: true,
                    });
                    setTimeout(() => {
                      window.location.reload();
                    }, 1500);
                  },
                  onError: (error: Error) => {
                    console.error('Failed to favourite chat:', error);
                    setFavouriteAlert({
                      show: true,
                      success: false,
                    });
                  },
                });
              }
            }}
          >
            <HeartIcon className="h-4 w-4 mr-2" />
            {chat.favourite
              ? 'Aus Favoriten entfernen'
              : 'Zu Favoriten hinzufügen'}
          </Button>

          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={() => {
              setSelectedChat(chat);
              setIsDialogOpen(true);
            }}
          >
            <PencilIcon className="h-4 w-4 mr-2" />
            Chat bearbeiten
          </Button>
          <Button
            variant="destructive"
            className="w-full justify-start"
            onClick={handleDelete}
          >
            <TrashIcon className="h-4 w-4 mr-2" />
            Chat löschen
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
