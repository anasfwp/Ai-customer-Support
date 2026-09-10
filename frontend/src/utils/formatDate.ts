import { format, formatDistanceToNow, parseISO } from 'date-fns';

/**
 * Format an ISO date string as a readable date and time.
 */
export function formatDateTime(iso: string): string {
  try {
    return format(parseISO(iso), 'MMM d, yyyy · h:mm a');
  } catch {
    return iso;
  }
}

/**
 * Format an ISO date string as "2 hours ago", "3 days ago", etc.
 */
export function formatRelative(iso: string): string {
  try {
    return formatDistanceToNow(parseISO(iso), { addSuffix: true });
  } catch {
    return iso;
  }
}

/**
 * Format an ISO date string as just the date.
 */
export function formatDate(iso: string): string {
  try {
    return format(parseISO(iso), 'MMM d, yyyy');
  } catch {
    return iso;
  }
}