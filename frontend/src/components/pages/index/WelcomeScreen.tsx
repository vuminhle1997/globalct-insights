'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogTrigger } from '@/components/ui/dialog';
import { Bars3Icon, PencilSquareIcon } from '@heroicons/react/24/solid';
import ChatDialogForm from '@/components/form/ChatFormDialog';
import { useSidebar } from '@/components/ui/sidebar';
import { useIsMobile } from '@/hooks/use-mobile';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { motion } from 'framer-motion';
import Logo from '@/static/globalLogo.png';
import Image from 'next/image';
import { WaveBackground } from '@/components/ui/wave-animation';

export default function WelcomeScreen() {
  const isMobile = useIsMobile();
  const { open, toggleSidebar } = useSidebar();
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  return (
    <main className="flex-1 overflow-hidden flex items-center justify-center">
      {(!open || isMobile) && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              aria-label="Seitenleiste öffnen"
              variant="outline"
              className="bg-primary dark:bg-accent hover:bg-primary/50 text-white top-4 left-4 absolute"
              onClick={toggleSidebar}
            >
              <Bars3Icon className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent className="dark:bg-accent bg-primary border border-white shadow-sm">
            <p>Seitenleiste öffnen</p>
          </TooltipContent>
        </Tooltip>
      )}
      <div className="w-full max-w-3xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Image
            src={Logo.src}
            alt="Global CT Insights Logo"
            className="w-100 h-32 mx-auto mb-12 animate-fade-in delay-100"
            width={480}
            height={120}
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h1 className="text-4xl font-bold mb-6 text-center animate-fade-in delay-200">
            Global CT Insights
          </h1>
          <p className="text-lg text-muted-foreground mb-8 text-center animate-fade-in delay-200">
            Willkommen bei Ihrem KI-Assistenten. Erstellen Sie Ihren ersten
            Chat, um loszulegen!
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="flex justify-center"
        >
          <div className="flex justify-center mb-8 animate-fade-in delay-300">
            <TooltipProvider>
              <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <DialogTrigger asChild>
                      <Button
                        variant="outline"
                        className="bg-primary dark:bg-accent text-white hover:bg-primary/10"
                      >
                        <PencilSquareIcon className="h-4 w-4 mr-2" />
                        Neuen Chat erstellen
                      </Button>
                    </DialogTrigger>
                  </TooltipTrigger>
                  <TooltipContent className="dark:bg-accent bg-primary border border-white shadow-sm">
                    <p>
                      Neuen Chat erstellen mit vordefinierten <br />{' '}
                      Einstellungen für interaktive Gespräche
                    </p>
                  </TooltipContent>
                </Tooltip>
                <ChatDialogForm onCreated={() => setIsCreateOpen(false)} />
              </Dialog>
            </TooltipProvider>
          </div>
        </motion.div>
      </div>
      <motion.div
        className="absolute inset-0 -z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
      >
        <WaveBackground />
      </motion.div>
    </main>
  );
}
