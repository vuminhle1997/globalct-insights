'use client';

import React, { useRef, useEffect } from 'react';
import { Dialog } from '@/components/ui/dialog';
import {
  useGetChat,
  useDeleteFile,
  usePostFile,
  useDeleteChat,
  useChatStream,
} from '@/frontend/queries/chats';
import { Message, Chat } from '@/frontend/types';
import { useRouter } from 'next/navigation';
import {
  selectProfilePicture,
  selectAppState,
  selectChats,
  setChats,
} from '@/frontend/store/reducer/app_reducer';
import { useAppDispatch, useAppSelector } from '@/frontend/store/hooks/hooks';
import { useForm } from 'react-hook-form';
import {
  usePostFavourite,
  useDeleteFavourite,
} from '@/frontend/queries/favourites';
import ChatDialogForn from '@/components/form/ChatFormDialog';
import PendingMessageLoader from '@/components/form/PendingMessageLoader';
import ChatNotFoundScreen, {
  UserChatNotFoundScreen,
} from '@/components/pages/chat/404NotFound';
import ChatAlertDialog from '@/components/pages/chat/components/ChatAlertDialog';
import ChatContainer, {
  ChatContainerProps,
} from '@/components/pages/chat/ChatContainer';
import ChatTextFieldArea, {
  ChatTextFieldAreaProps,
} from '@/components/pages/chat/ChatTextFieldArea';
import { ChatFormData } from '@/frontend/types';
import ChatFileManager, {
  ChatFileManagerProps,
} from '@/components/pages/chat/components/ChatFileManager';
import ChatFavouriteAlertDialog, {
  ChatFavouriteAlertDialogProps,
} from '@/components/pages/chat/components/ChatFavouriteAlertDialog';
import ChatDeleteAlertDialog, {
  ChatDeleteAlertDialogProps,
} from '@/components/pages/chat/components/ChatDeleteAlertDialog';
import ChatEditAlertDialog, {
  ChatEditAlertDialogProps,
} from '@/components/pages/chat/components/ChatEditAlertDialog';
import AuthProvider from '@/components/AuthProvider';
import _ from 'lodash';
import DashboardLoadingSkeleton from '@/components/pages/index/DashboardLoadingSkeleton';

/**
 * Component that renders a chat page for a specific chat identified by a slug.
 *
 * This component handles:
 * - Chat message display and scrolling
 * - File uploads and management
 * - Message sending and streaming responses
 * - Chat deletion and editing
 * - Favorite status management
 * - Various dialog states for different actions
 *
 * @param {Object} props - Component props
 * @param {Promise<{slug: string}>} props.params - Object containing the chat slug from URL params
 *
 * @returns {JSX.Element} A complete chat interface with messages, input area, and various dialogs
 *
 * @example
 * <SlugChatPage params={Promise.resolve({slug: "chat-123"})} />
 *
 * @remarks
 * The component uses several custom hooks for data fetching and state management:
 * - useGetChat - Fetches chat data
 * - useChatStream - Handles message streaming
 * - useDeleteFile/usePostFile - Manages file operations
 * - useDeleteChat - Handles chat deletion
 * - usePostFavourite/useDeleteFavourite - Manages favorite status
 */
export default function SlugChatPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = React.use(params);
  const router = useRouter();
  const dispatch = useAppDispatch();
  const chats = useAppSelector(selectChats);
  const queryParams =
    useAppSelector(state => state.app.query_params)[slug] || {};

  const appState = useAppSelector(selectAppState);
  const profilePicture = useAppSelector(selectProfilePicture);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const [selectedChat, setSelectedChat] = React.useState<Chat | null>(null);
  const [messages, setMessages] = React.useState<Message[]>([]);

  const [isDialogOpen, setIsDialogOpen] = React.useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
  const [isCreateChatDialogOpen, setIsCreateChatDialogOpen] =
    React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isFileDialogOpen, setIsFileDialogOpen] = React.useState(false);
  const [isSettingsDialogOpen, setIsSettingsDialogOpen] = React.useState(false);
  const [isTyping, setIsTyping] = React.useState(false);
  const [isUploading, setIsUploading] = React.useState(false);
  const [pendingMessage, setPendingMessage] = React.useState<string | null>(
    null
  );
  const [alert, setAlert] = React.useState<{
    show: boolean;
    type: 'success' | 'error';
    title: string;
    description: string;
  } | null>(null);

  const [favouriteAlert, setFavouriteAlert] = React.useState<{
    show: boolean;
    success: boolean;
  }>({ show: false, success: false });

  const { data: chat, refetch: refetchChat } = useGetChat(slug);
  const [response, isStreaming, sendMessageStream] = useChatStream(slug);

  const deleteFileMutation = useDeleteFile(slug);
  const uploadFileMutation = usePostFile(slug);
  const deleteChat = useDeleteChat(slug);
  const postFavourite = usePostFavourite();
  const deleteFavourite = useDeleteFavourite();

  const {
    register,
    handleSubmit: handleFormSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ChatFormData>({
    defaultValues: {
      message: '',
    },
  });

  /**
   * Handles the deletion of a file by its ID.
   *
   * This function performs the following steps:
   * 1. Calls the `deleteFileMutation.mutateAsync` method to delete the file.
   * 2. Refetches the chat data using `refetchChat` to update the UI.
   * 3. Displays a success alert if the file is deleted successfully.
   * 4. Displays an error alert if the deletion fails.
   *
   * @param fileId - The unique identifier of the file to be deleted.
   *
   * @throws Will log an error to the console and display an error alert if the deletion fails.
   */
  const handleDeleteFile = async (fileId: string) => {
    try {
      await deleteFileMutation.mutateAsync(fileId);
      await refetchChat();
      setAlert({
        show: true,
        type: 'success',
        title: 'Erfolgreich gelöscht',
        description: 'Die Datei wurde erfolgreich gelöscht',
      });
      setTimeout(() => setAlert(null), 5000);
    } catch (error) {
      console.error('Error deleting file:', error);
      setAlert({
        show: true,
        type: 'error',
        title: 'Fehler beim Löschen',
        description:
          'Die Datei konnte nicht gelöscht werden. Bitte versuchen Sie es erneut.',
      });
      setTimeout(() => setAlert(null), 5000);
    }
  };

  /**
   * Handles the click event for triggering the file input element.
   * This function programmatically clicks the file input element referenced
   * by `fileInputRef` to open the file selection dialog.
   */
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  /**
   * Handles the file input change event, validates the file type, and uploads the file.
   *
   * @param event - The change event triggered by the file input element.
   *
   * The function performs the following steps:
   * 1. Retrieves the selected file from the input element.
   * 2. Validates the file type against a list of allowed MIME types:
   *    - PDF
   *    - CSV
   *    - Excel (both `.xls` and `.xlsx`)
   *    - Plain text
   *    - SQL files
   * 3. If the file type is invalid, it displays an error alert and resets the input value.
   * 4. If the file type is valid, it uploads the file using the `uploadFileMutation` function.
   * 5. After a successful upload, it refetches the chat data and displays a success alert.
   * 6. Handles errors during the upload process by displaying an error alert.
   * 7. Ensures the `isUploading` state is properly managed during the upload process.
   *
   * @throws Will display an error alert if the file upload fails.
   */
  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const allowedTypes = [
      'application/pdf',
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
      'application/x-sql',
      'application/sql',
    ];

    if (file.name.length < 0 && !allowedTypes.includes(file.type)) {
      setAlert({
        show: true,
        type: 'error',
        title: 'Ungültiger Dateityp',
        description:
          'Bitte laden Sie nur PDF, CSV, Excel, SQL- oder TXT-Dateien hoch',
      });
      setTimeout(() => setAlert(null), 5000);
      event.target.value = '';
      return;
    }

    try {
      setIsUploading(true);
      const formData = new FormData();

      if (file.type.length < 1 && file.name.toLowerCase().endsWith('.sql')) {
        const sqlFile = new File([file], file.name, {
          type: 'application/sql',
        });
        formData.set('file', sqlFile);
      } else {
        formData.set('file', file);
      }
      await uploadFileMutation.mutateAsync(formData);

      await refetchChat();
      event.target.value = '';
      setAlert({
        show: true,
        type: 'success',
        title: 'Erfolgreich hochgeladen',
        description: 'Die Datei wurde erfolgreich hochgeladen',
      });
      setTimeout(() => setAlert(null), 5000);
    } catch (error) {
      console.error('Error uploading file:', error);
      setAlert({
        show: true,
        type: 'error',
        title: 'Fehler beim Hochladen',
        description:
          'Die Datei konnte nicht hochgeladen werden. Bitte versuchen Sie es erneut.',
      });
      setTimeout(() => setAlert(null), 5000);
    } finally {
      setIsUploading(false);
    }
  };

  /**
   * Scrolls the chat container to the bottom.
   * This function checks if the `chatContainerRef` is defined and sets its
   * `scrollTop` property to its `scrollHeight`, effectively scrolling
   * the container to its lowest point.
   */
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  };

  /**
   * Handles the submission of a chat message.
   *
   * @param data - The chat form data containing the message to be sent
   * @throws {Error} When there is an error sending the message
   *
   * This function:
   * - Sets submission and typing states
   * - Creates and adds user message to messages list
   * - Sends message through stream mutation
   * - Creates and adds assistant response to messages list
   * - Resets the form
   * - Updates chat interaction timestamp
   * - Re-sorts chats by last interaction
   * - Handles cleanup of states after completion
   */
  const handleSubmit = async (data: ChatFormData) => {
    try {
      setIsSubmitting(true);
      setPendingMessage(data.message);
      setIsTyping(true);
      scrollToBottom();
      const userMessage: Message = {
        role: 'user',
        text: data.message,
        block_type: 'text',
        created_at: new Date().toDateString(),
      };
      setMessages([...messages, userMessage]);
      await sendMessageStream.mutateAsync({
        text: data.message,
        query_params: queryParams,
      });

      const newMessage: Message = {
        role: 'assistant',
        text: response,
        block_type: 'text',
        created_at: new Date().toDateString(),
      };

      setMessages(prevMessages => [...prevMessages, newMessage]);
      reset(); // Clear the form after sending

      const updatedChats = _.cloneDeep(chats);
      const chatToUpdate = _.find(updatedChats, { id: slug });

      if (chatToUpdate) {
        chatToUpdate.last_interacted_at = new Date().toISOString();
        const sortedChats = _.orderBy(
          updatedChats,
          ['last_interacted_at'],
          ['desc']
        );
        dispatch(setChats(sortedChats));
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsSubmitting(false);
      setIsTyping(false);
      scrollToBottom();
    }
  };

  /**
   * Opens the delete confirmation dialog by setting the isDeleteDialogOpen state to true.
   * @function handleDelete
   * @returns {void}
   */
  const handleDelete = () => {
    setIsDeleteDialogOpen(true);
  };

  /**
   * Initiates the deletion of the current chat session.
   * Makes a mutation request to delete the chat and handles the response.
   * On successful deletion, redirects to the home page and refreshes the window.
   * On error, logs the failure message to the console.
   *
   * @remarks
   * This function uses the deleteChat mutation from a query client and the Next.js router for navigation.
   *
   * @throws {Error} Logs any errors that occur during the deletion process
   */
  const confirmDelete = () => {
    deleteChat.mutate(undefined, {
      onSuccess: () => {
        router.push('/');
      },
      onError: (error: Error) => {
        console.error('Failed to delete chat:', error);
      },
    });
  };

  useEffect(() => {
    if (chat) {
      window.document.title = `global CT Insights - ${chat?.title}`;
    } else {
      window.document.title = `global CT Insights - Lädt Chat . . .`;
    }
  }, [chat]);

  useEffect(() => {
    if (isStreaming) {
      if (response.length < 1) {
        window.document.title = `🤔 agentic RAG denkt ...`;
      } else {
        window.document.title = `🤖 agentic RAG chattet ...`;
      }
    }
  }, [isStreaming, response, dispatch]);

  useEffect(() => {
    scrollToBottom();
  }, [chat?.messages, pendingMessage, isTyping]);

  const messageText = watch('message');

  const chatProps: ChatContainerProps = {
    reset,
    chat: chat!,
    chatContainerRef,
    messageText,
    pendingMessage,
    profilePicture,
    deleteFavourite,
    handleDelete,
    isSettingsDialogOpen,
    postFavourite,
    setFavouriteAlert,
    setIsDialogOpen,
    setIsSettingsDialogOpen,
    setSelectedChat,
    slug,
    response,
    isStreaming: isStreaming,
    scrollToBottom,
  };

  const chatTextFieldAreaProps: ChatTextFieldAreaProps = {
    deleteFileMutation,
    errors,
    register,
    fileInputRef,
    handleFileChange,
    handleUploadClick,
    handleFormSubmit,
    isSubmitting,
    isTyping,
    messageText,
    setIsFileDialogOpen,
    handleSubmit,
    isUploading,
    uploadFileMutation,
  };

  const fileManagerProps: ChatFileManagerProps = {
    chat: chat!,
    setIsFileDialogOpen,
    isFileDialogOpen,
    handleDeleteFile,
    deleteFileMutation,
  };

  const favouriteAlertProps: ChatFavouriteAlertDialogProps = {
    favouriteAlert,
    setFavouriteAlert,
  };

  const chatEditAlertProps: ChatEditAlertDialogProps = {
    isDialogOpen,
    refetchChat,
    selectedChat,
    setIsDialogOpen,
  };

  const chatDeleteDialogProps: ChatDeleteAlertDialogProps = {
    confirmDelete,
    isDeleteDialogOpen,
    setIsDeleteDialogOpen,
  };

  return (
    <AuthProvider
      fallback={<DashboardLoadingSkeleton />}
      errorFallback={<ChatNotFoundScreen />}
    >
      {appState === 'idle' && (
        <main className="flex flex-col h-screen w-screen bg-gray-50 dark:bg-accent">
          {alert && <ChatAlertDialog {...alert} />}

          {(isUploading || deleteFileMutation.isPending) && (
            <PendingMessageLoader
              message={
                isUploading
                  ? 'Datei wird hochgeladen...'
                  : 'Datei wird gelöscht...'
              }
            />
          )}
          {!chat ? (
            <UserChatNotFoundScreen />
          ) : (
            <>
              {/* Chat Messages Container */}
              <ChatContainer {...chatProps} />

              {/* Input Area */}
              <ChatTextFieldArea {...chatTextFieldAreaProps} />

              {/* File Management Dialog */}
              <ChatFileManager {...fileManagerProps} />

              {/* Favourite Alert Dialog */}
              <ChatFavouriteAlertDialog {...favouriteAlertProps} />

              {/* Edit Chat Dialog */}
              <ChatEditAlertDialog {...chatEditAlertProps} />

              {/* Delete Confirmation Dialog */}
              <ChatDeleteAlertDialog {...chatDeleteDialogProps} />

              {/* Create Chat Dialog */}
              <Dialog
                open={isCreateChatDialogOpen}
                onOpenChange={setIsCreateChatDialogOpen}
              >
                <ChatDialogForn
                  mode="create"
                  onSuccess={() => {
                    setIsCreateChatDialogOpen(false);
                    router.push('/');
                  }}
                />
              </Dialog>
            </>
          )}
        </main>
      )}
    </AuthProvider>
  );
}
