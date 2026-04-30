'use client';

import ChatDialogForn from '@/components/form/ChatFormDialog';
import { Dialog, DialogTrigger } from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SidebarMenuButton, SidebarMenuItem } from '@/components/ui/sidebar';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Chat } from '@/frontend/types/chats';
import EllipsisHorizontalIcon from '@heroicons/react/24/solid/EllipsisHorizontalIcon';
import PencilIcon from '@heroicons/react/24/solid/PencilIcon';
import TrashIcon from '@heroicons/react/24/solid/TrashIcon';
import Image from 'next/image';
import Link from 'next/link';
import React from 'react';

export interface ChatNavigationItemProps extends React.PropsWithChildren {
  chat: Chat;
  slug: string;
  isDialogOpen: boolean;
  setIsDialogOpen: (open: boolean) => void;
  selectedChat: Chat | null;
  setSelectedChat: (chat: Chat | null) => void;
  handleDelete: (chatId: string) => void;
  prefix: string;
}

export default function ChatNavigationItem({
  chat,
  slug,
  isDialogOpen,
  setIsDialogOpen,
  selectedChat,
  setSelectedChat,
  handleDelete,
  prefix,
}: ChatNavigationItemProps) {
  return (
    <SidebarMenuItem
      className={`flex flex-row items-start justify-center px-4 py-2 min-h-12.5 ${
        chat.id === slug ? 'bg-primary/10 dark:bg-accent/50' : ''
      }`}
      key={`${prefix}-${chat.id}`}
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
        <SidebarMenuButton className="w-full text-left fit-content h-full wrap-break-word whitespace-normal py-1">
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
          <Tooltip>
            <TooltipTrigger asChild>
              <DropdownMenuTrigger
                className="hover:bg-accent ml-2 w-7.5 h-7.5 
                            flex justify-center items-center rounded-md cursor-pointer mt-1"
              >
                <EllipsisHorizontalIcon className="h-4 w-4" />
              </DropdownMenuTrigger>
            </TooltipTrigger>
            <TooltipContent className="dark:bg-accent bg-primary border-2 border-white shadow-sm">
              <p>Chat editieren</p>
            </TooltipContent>
          </Tooltip>

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
          <ChatDialogForn
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
}
