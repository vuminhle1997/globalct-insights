'use client';

import { Chat } from '@/frontend/types';
import { v4 as uuidv4 } from 'uuid';
import { templates } from '../templates';
import Image, { StaticImageData } from 'next/image';

export interface TemplatesChatNavigationProps {
  useAsTemplate: (
    template:
      | Chat
      | {
          id?: string;
          temperature?: number;
          title: string;
          description: string;
          context: string;
          avatar_path?: StaticImageData;
          model?: string;
        }
  ) => void;
}

/**
 * A React component that renders a navigation menu for selecting templates.
 * Each template is displayed as a clickable card with an optional avatar, title, and description.
 *
 * @component
 * @param {TemplatesChatNavigationProps} props - The props for the component.
 * @param {Function} props.useAsTemplate - A callback function invoked when a template is selected.
 *
 * @returns {JSX.Element} The rendered navigation menu for templates.
 *
 * @example
 * <TemplatesChatNavigation useAsTemplate={handleTemplateSelection} />
 */
export default function TemplatesChatNavigation({
  useAsTemplate: changeAsTemplate,
}: TemplatesChatNavigationProps) {
  return (
    <div className="space-y-2">
      {templates.map(template => (
        <div
          key={uuidv4()}
          className="p-3 border rounded-lg hover:bg-accent cursor-pointer bg-muted/50"
          onClick={() => changeAsTemplate(template)}
        >
          <div className="flex items-center gap-3">
            {template.avatar_path && (
              <Image
                width={128}
                height={128}
                src={template.avatar_path.src}
                alt={`Template ${template.title} Avatar`}
                className="w-12 h-12 rounded-full object-cover"
              />
            )}
            <div>
              <h4 className="font-medium">{template.title}</h4>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {template.description}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
