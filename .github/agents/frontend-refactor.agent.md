Refactor the following code to adhere to modern Next.js (App Router) and ShadCN/Tailwind best practices. 

### GOALS:
1.  **Component Splitting**: Extract large, "messy" components into smaller, reusable atoms and molecules in `@/components/ui` or `@/components/shared`.
2.  **RSC vs. Client**: Audit `use client` directives. Move data fetching and state-less logic to React Server Components. Only keep interactivity (hooks, event handlers) in Client Components.
3.  **ShadCN Alignment**: Ensure all UI elements use existing ShadCN primitives. Replace hardcoded Tailwind colors/spacing with theme variables (e.g., use `text-primary` or `bg-accent` instead of `text-blue-600`).
4.  **Tailwind Optimization**: Use the `cn()` utility for conditional classes. Consolidate repetitive Tailwind patterns into `variants` using `cva` (Class Variance Authority) where appropriate.
5.  **Type Safety**: Ensure all components have strict TypeScript interfaces. Eliminate `any` and use descriptive prop naming (e.g., `isLoading`, `isOpen`).
6.  **Readability**: Implement a logical file structure: (Imports -> Types -> Constants -> Main Component -> Sub-components).

### OUTPUT REQUIREMENT:
Provide the refactored code for each file. For major changes, briefly explain *why* the architectural change was made (e.g., "Moved data fetching to RSC for better LCP").

[ATTACH YOUR FILES OR DIRECTORY HERE]
