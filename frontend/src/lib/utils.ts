import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function parseAgentResponse(
  raw: string
): { type: string; content: string }[] {
  const clean = raw
    .replaceAll('<br />', '\n')
    .replaceAll('<br/>', '\n')
    .replaceAll('<br>', '\n')
    .trim();

  if (!clean) {
    return [];
  }

  const blocks: { type: string; content: string }[] = [];
  const regex =
    /(?:^|\n)\s*(Thought|Answer|Observation)\s*:?\s*([\s\S]*?)(?=(?:\n\s*(?:Thought|Answer|Observation)\s*:?)|$)/gi;

  let match;
  while ((match = regex.exec(clean)) !== null) {
    const type =
      match[1].charAt(0).toUpperCase() + match[1].slice(1).toLowerCase();
    const content = match[2].trim();

    if (!content) {
      continue;
    }

    blocks.push({
      type,
      content,
    });
  }

  // Fallback for plain assistant text without explicit Thought/Answer sections.
  if (blocks.length === 0) {
    return [{ type: 'Answer', content: clean }];
  }

  return blocks;
}
