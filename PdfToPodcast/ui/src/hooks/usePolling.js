import { useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for polling an async function at regular intervals
 * @param {Function} callback - Async function to poll
 * @param {number} interval - Polling interval in milliseconds
 * @param {boolean} enabled - Whether polling is enabled
 * @param {Array} dependencies - Dependencies that should restart polling
 */
export const usePolling = (callback, interval = 2000, enabled = false, dependencies = []) => {
  const savedCallback = useRef();
  const timeoutId = useRef(null);

  // Remember the latest callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the polling
  useEffect(() => {
    const tick = async () => {
      if (savedCallback.current) {
        try {
          await savedCallback.current();
        } catch (error) {
          console.error('Polling error:', error);
        }
      }
    };

    if (enabled) {
      // Execute immediately
      tick();

      // Then poll at interval
      const id = setInterval(tick, interval);
      timeoutId.current = id;

      return () => {
        if (timeoutId.current) {
          clearInterval(timeoutId.current);
        }
      };
    } else {
      if (timeoutId.current) {
        clearInterval(timeoutId.current);
      }
    }
  }, [enabled, interval, ...dependencies]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutId.current) {
        clearInterval(timeoutId.current);
      }
    };
  }, []);
};

export default usePolling;
