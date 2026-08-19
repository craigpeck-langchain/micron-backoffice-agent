import type { FC, SVGProps } from "react";

/**
 * Placeholder Micron mark - a simple monogram, not the official trademarked
 * logo. Swap this file (and the --primary color in index.css) for real
 * brand assets when available.
 */
export const MicronMark: FC<SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 32 32" fill="none" {...props}>
    <rect width="32" height="32" rx="7" fill="currentColor" />
    <path
      d="M8 23V9h3.6l4.4 8.6L20.4 9H24v14h-3.2V13.8l-4.2 8h-2.2l-4.2-8V23z"
      fill="var(--primary-foreground, #fff)"
    />
  </svg>
);
