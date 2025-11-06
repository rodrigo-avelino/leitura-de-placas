# Lib Directory

This directory contains utility functions used throughout the application.

## Files

### `utils.ts`

Contains the `cn` utility function used for conditionally joining Tailwind CSS classes.

**Important:** This file is required by all UI components in `src/components/ui/`. Do not delete it and ensure it is committed to version control.

The `cn` function combines `clsx` and `tailwind-merge` to:
- Handle conditional class names
- Merge Tailwind CSS classes intelligently
- Avoid class conflicts

Example usage:
```tsx
import { cn } from "@/lib/utils";

<div className={cn("base-class", condition && "conditional-class", className)} />
```
