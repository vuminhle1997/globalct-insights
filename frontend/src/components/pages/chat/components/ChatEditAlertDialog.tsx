'use client';

import ChatDialogForm from '@/components/form/ChatFormDialog';
import { DialogHeader } from '@/components/ui/dialog';
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog';
import React from 'react';
import { Chat } from '@/frontend/types';
import { useRouter } from 'next/navigation';

export interface ChatEditAlertDialogProps {
  isDialogOpen: boolean;
  setIsDialogOpen: React.Dispatch<React.SetStateAction<boolean>>;
  selectedChat: Chat | null;
  refetchChat: () => void;
}

/**
 * ChatEditAlertDialog component renders a dialog for editing a chat entry.
 *
 * @param {boolean} isDialogOpen - Indicates whether the dialog is open.
 * @param {() => void} refetchChat - Function to refetch the chat data after a successful update.
 * @param {Chat} selectedChat - The chat entry that is being edited.
 * @param {(isOpen: boolean) => void} setIsDialogOpen - Function to set the dialog open state.
 *
 * @returns {JSX.Element} The rendered ChatEditAlertDialog component.
 */
export default function ChatEditAlertDialog({
  isDialogOpen,
  refetchChat,
  selectedChat,
  setIsDialogOpen,
}: ChatEditAlertDialogProps) {
  const router = useRouter();
  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogContent className="sm:max-w-[800px]">
        <DialogHeader>
          <DialogTitle>Chat bearbeiten</DialogTitle>
        </DialogHeader>
        <ChatDialogForm
          chat={selectedChat || undefined}
          mode="update"
          onUpdated={chat => {
            setIsDialogOpen(false);
            refetchChat();
            router.push(`/chat/${chat.id}`);
          }}
          onSuccess={() => {
            setIsDialogOpen(false);
            refetchChat();
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
