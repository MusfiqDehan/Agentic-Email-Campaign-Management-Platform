/**
 * Extract the human-readable message from a backend error response.
 *
 * The API wraps errors as { message, errors, ... }; axios nests that under
 * response.data. Falls back to the supplied default when nothing usable
 * is present.
 */
export function getApiErrorMessage(error: unknown, fallback = 'Unexpected error'): string {
  if (typeof error === 'object' && error !== null) {
    const response = (error as { response?: { data?: { message?: unknown } } }).response;
    const message = response?.data?.message;
    if (typeof message === 'string' && message.trim()) {
      return message;
    }
  }
  return fallback;
}
