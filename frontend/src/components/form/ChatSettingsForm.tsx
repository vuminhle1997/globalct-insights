'use client';

import {
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';

import { Slider } from '../ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import { Button } from '../ui/button';
import { placeholderForContext } from './templates';
import {
  FieldErrors,
  UseFormGetValues,
  UseFormHandleSubmit,
  UseFormRegister,
  UseFormSetValue,
  UseFormWatch,
} from 'react-hook-form';
import { Chat } from '@/frontend/types';
import { RefObject } from 'react';
import { selectLLMModels, useAppSelector } from '@/frontend';

type FormData = {
  title: string;
  description: string;
  context: string;
  avatar?: FileList;
  temperature: number;
  model: string;
  model_provider: string;
};

export interface ChatSettingsFormProps {
  handleSubmit: UseFormHandleSubmit<FormData, undefined>;
  onSubmit: (data: FormData) => Promise<void>;
  register: UseFormRegister<FormData>;
  watch: UseFormWatch<FormData>;
  setValue: UseFormSetValue<FormData>;
  errors: FieldErrors<FormData>;
  chat?: Chat | null;
  handleAvatarClick: () => void;
  fileInputRef: RefObject<HTMLInputElement | null>;
  avatarPreview: string | null;
  mode: 'create' | 'update';
  setAvatarPreview: React.Dispatch<React.SetStateAction<string | null>>;
  isCreating: boolean;
  isUpdating: boolean;
  getValues: UseFormGetValues<FormData>;
}

/**
 * A React component for rendering a chat settings form. This form allows users to create or edit chat configurations,
 * including uploading an avatar, setting a title, description, context, selecting a language model, and adjusting the temperature.
 *
 * @param {Object} props - The properties passed to the component.
 * @param {Function} props.handleSubmit - The function to handle form submission, typically provided by `react-hook-form`.
 * @param {Function} props.handleAvatarClick - The function to handle avatar click events.
 * @param {Function} props.onSubmit - The function to execute when the form is submitted.
 * @param {Function} props.register - The `react-hook-form` register function for managing form inputs.
 * @param {Function} props.watch - The `react-hook-form` watch function to observe form values.
 * @param {Function} props.setValue - The `react-hook-form` setValue function to programmatically set form values.
 * @param {Object} props.errors - The object containing validation errors for form fields.
 * @param {Object} props.chat - The chat object containing existing chat settings (used in edit mode).
 * @param {React.RefObject<HTMLInputElement>} props.fileInputRef - A reference to the hidden file input element for avatar uploads.
 * @param {string | null} props.avatarPreview - The URL or data URI of the avatar preview image.
 * @param {string} props.mode - The mode of the form, either `'create'` or `'edit'`.
 * @param {Function} props.setAvatarPreview - A function to update the avatar preview state.
 * @param {boolean} props.isCreating - A boolean indicating whether a chat is currently being created.
 * @param {boolean} props.isUpdating - A boolean indicating whether a chat is currently being updated.
 *
 * @returns {JSX.Element} The rendered chat settings form component.
 */
export default function ChatSettingsForm({
  handleSubmit,
  handleAvatarClick,
  onSubmit,
  register,
  watch,
  setValue,
  errors,
  fileInputRef,
  avatarPreview,
  mode,
  setAvatarPreview,
  isCreating,
  isUpdating,
}: ChatSettingsFormProps) {
  const models = useAppSelector(selectLLMModels);
  const isPending = mode === 'create' ? isCreating : isUpdating;
  return (
    <>
      <form
        className="overflow-y-auto relative flex-1"
        onSubmit={handleSubmit(onSubmit)}
      >
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? 'Chat erstellen' : 'Chat bearbeiten'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? 'Erstelle einen neuen Chat mit kontextbezogenen Inhalten. Füllen Sie alle erforderlichen Felder aus, um fortzufahren. Der Titel sollte prägnant sein, die Beschreibung kann zusätzliche Details enthalten, und der Kontext sollte die Rolle und den Kommunikationsstil des Chats definieren.'
              : 'Bearbeite die Einstellungen des bestehenden Chats. Stellen Sie sicher, dass alle Felder korrekt ausgefüllt sind, um die Änderungen zu speichern. Der Titel, die Beschreibung und der Kontext sind entscheidend für die Definition der Chat-Parameter.'}
            <span className="text-gray-400 mt-4">
              Markierte Felder mit * sind verpflichtend.
            </span>
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4 my-4 px-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="avatar" className="text-right">
              Avatar
            </Label>
            <div className="lg:col-span-3 col-span-full">
              <div className="flex flex-col items-center gap-4">
                <div
                  onClick={handleAvatarClick}
                  className={`w-32 h-32 rounded-full overflow-hidden cursor-pointer relative group ${
                    !avatarPreview
                      ? 'border-2 border-dashed border-gray-300 hover:border-gray-400 bg-gray-50'
                      : ''
                  }`}
                >
                  {avatarPreview ? (
                    <>
                      <img
                        src={avatarPreview}
                        alt="Avatar preview"
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-white text-sm">Ändern</span>
                      </div>
                    </>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full p-4">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-8 w-8 text-gray-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                        />
                      </svg>
                      <span className="text-sm text-gray-500 text-center mt-2">
                        Avatar hochladen
                      </span>
                    </div>
                  )}
                </div>
                <Input
                  {...register('avatar')}
                  id="avatar"
                  type="file"
                  accept="image/*"
                  className="hidden"
                  ref={e => {
                    register('avatar').ref(e);
                    fileInputRef.current = e;
                  }}
                />
                {avatarPreview && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setAvatarPreview(null);
                      if (fileInputRef.current) {
                        fileInputRef.current.value = '';
                      }
                    }}
                  >
                    Avatar entfernen
                  </Button>
                )}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="title" className="text-right">
              Titel *
            </Label>
            <div className="lg:col-span-3 col-span-full space-y-2">
              <Input
                id="title"
                className={errors.title ? 'border-red-500' : ''}
                {...register('title', {
                  required: 'Titel ist erforderlich',
                })}
              />
              {errors.title && (
                <p className="text-red-500 text-sm">{errors.title.message}</p>
              )}
            </div>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="description" className="text-right">
              Beschreibung
            </Label>
            <Textarea
              id="description"
              className="lg:col-span-3 col-span-full"
              {...register('description')}
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="context" className="text-right">
              Kontext *
            </Label>
            <div className="lg:col-span-3 col-span-full space-y-2">
              <Textarea
                id="context"
                className={errors.context ? 'border-red-500' : ''}
                placeholder={placeholderForContext}
                rows={10}
                {...register('context', {
                  required: 'Kontext ist erforderlich',
                })}
              />
              {errors.context && (
                <p className="text-red-500 text-sm">{errors.context.message}</p>
              )}
              <div className="text-sm text-muted-foreground">
                Der Kontext muss die folgenden Elemente enthalten:
                <br />- Persönlichkeit und Rolle des KI-Assistenten
                <br />- Kommunikationsstil und Verhaltensmuster
                <br />- Spezifische Fähigkeiten und Expertise
                <br />- Umgang mit verfügbaren Tools
                <br />- Ausgabeformat und zusätzliche Regeln
                <p className=" mt-2">
                  Wenn Sie sich unsicher sind, besuchen Sie bitte{' '}
                  <a
                    href="/faq"
                    className="text-blue-500 dark:text-white underline"
                  >
                    unsere FAQ-Seite
                  </a>
                  , um mehr darüber zu erfahren, wie Sie gute
                  Eingabeaufforderungen schreiben können.
                </p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="model" className="text-right">
              Sprachmodell *
            </Label>
            {models && models.length > 0 && (
              <div className="lg:col-span-3 col-span-full space-y-2">
                <Select
                  defaultValue="gemini-3.1-flash-lite-preview"
                  value={watch('model')}
                  onValueChange={value => setValue('model', value)}
                >
                  <SelectTrigger className="w-full h-[60px]">
                    <SelectValue placeholder="Wählen Sie ein Sprachmodell" />
                  </SelectTrigger>
                  <SelectContent className="w-[var(--radix-select-trigger-width)] max-h-[300px]">
                    {models &&
                      models.length > 0 &&
                      models.map(model => (
                        <SelectItem
                          key={model.llm_model}
                          value={model.llm_model}
                          className="flex flex-col items-start py-3"
                        >
                          <div className="flex flex-col justify-start items-start">
                            <div className="font-medium text-base text-left">
                              {model.llm_model}
                            </div>
                            <div className="text-sm text-muted-foreground leading-snug text-left mt-1">
                              {model.description}
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground mt-2">
                  Das ausgewählte Sprachmodell bestimmt die Fähigkeiten und
                  Charakteristiken des Chats.
                </p>
              </div>
            )}
          </div>
          <div className="grid grid-cols-4 items-center gap-4 mt-8">
            <Label htmlFor="temperature" className="text-right">
              Temperatur
            </Label>
            <div className="lg:col-span-3 col-span-full space-y-2">
              <Slider
                id="temperature"
                min={0}
                max={1}
                step={0.01}
                value={[Number(watch('temperature') ?? 0.75)]}
                onValueChange={([val]) => setValue('temperature', val)}
              />
              <div className="flex flex-col justify-center items-center">
                <p className="text-center">{watch('temperature')}</p>
                <span className="text-sm text-muted-foreground">
                  0 = keine Kreativität, 1 = sehr kreativ
                </span>
                <span className="text-sm text-muted-foreground">
                  0.75 = Standard
                </span>
                <span className="text-sm text-muted-foreground">
                  Die Temperatur beeinflusst die Kreativität der Antworten. Ein
                  höherer Wert führt zu kreativeren, aber weniger vorhersehbaren
                  Antworten, während ein niedrigerer Wert zu präziseren und
                  fokussierteren Antworten führt.
                </span>
              </div>
            </div>
          </div>
        </div>
        <DialogFooter className="sticky bg-background border-t py-4 bottom-0">
          <div className="grid grid-cols-2 gap-4">
            <Button
              type="reset"
              variant="outline"
              className="bg-gray-400 dark:bg-accent text-white"
              disabled={isPending}
            >
              Zurücksetzen
            </Button>
            <Button
              type="submit"
              variant="outline"
              className="bg-primary dark:bg-transparent text-white"
              disabled={isPending}
            >
              {isPending
                ? mode === 'create'
                  ? 'Erstellen...'
                  : 'Speichern...'
                : mode === 'create'
                  ? 'Erstellen'
                  : 'Speichern'}
            </Button>
          </div>
        </DialogFooter>
      </form>
    </>
  );
}
