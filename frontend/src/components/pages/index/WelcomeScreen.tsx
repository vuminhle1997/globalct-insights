'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogTrigger } from '@/components/ui/dialog';
import { Bars3Icon, PencilSquareIcon } from '@heroicons/react/24/solid';
import ChatEntryForm from '@/components/form/ChatEntryForm';
import { useSidebar } from '@/components/ui/sidebar';
import { useIsMobile } from '@/hooks/use-mobile';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

/**
 * The `WelcomeScreen` component renders the welcome screen for the Global CT Insights application.
 * It includes a title, a welcome message, and a button to create a new chat.
 *
 * @component
 * @returns {JSX.Element} The rendered welcome screen component.
 *
 * @example
 * // Usage example:
 * <WelcomeScreen />
 *
 * @remarks
 * - The component uses Tailwind CSS classes for styling.
 * - The chat entry form and suggestions section are currently commented out.
 *
 * @todo
 * - Implement the chat submission handling in the `handleSubmit` function.
 * - Uncomment and implement the suggestions section and chat entry form.
 */
export default function WelcomeScreen() {
  const isMobile = useIsMobile();
  const { open, toggleSidebar } = useSidebar();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  return (
    <main className="flex-1 overflow-hidden flex items-center justify-center">
      {(!open || isMobile) && (
        <Tooltip>
          <TooltipTrigger>
            <Button
              variant="outline"
              className="bg-primary dark:bg-accent hover:bg-primary/50 text-white top-4 left-4 absolute"
              onClick={toggleSidebar}
            >
              <Bars3Icon className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          {/* TODO: fix tooltip anchor */}
          <TooltipContent className="dark:bg-accent bg-primary border border-white shadow-sm">
            <p>Seitenleiste öffnen</p>
          </TooltipContent>
        </Tooltip>
      )}
      <div className="w-full max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-6 text-center animate-fade-in delay-200">
          Global CT Insights
        </h1>
        <p className="text-lg text-muted-foreground mb-8 text-center animate-fade-in delay-200">
          Willkommen bei Ihrem KI-Assistenten. Starten Sie einen neuen Chat oder
          stellen Sie eine Frage, um zu beginnen.
        </p>

        <div className="flex justify-center mb-8 animate-fade-in delay-300">
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                className="bg-primary dark:bg-accent text-white hover:bg-primary/10"
              >
                <PencilSquareIcon className="h-4 w-4 mr-2" />
                Neuen Chat erstellen
              </Button>
            </DialogTrigger>
            <ChatEntryForm onCreated={() => setIsCreateOpen(false)} />
          </Dialog>
        </div>
      </div>
    </main>
  );
}
