import { useState, useEffect, useCallback } from "react";
import { linkBridge } from "@webview-bridge/web";

// Define the AppBridge type based on your RN bridge definition
type AppBridge = {
  getLocalStorageItem(key: string): Promise<string | null>;
  setLocalStorageItem(key: string, value: string): Promise<boolean>;
  removeLocalStorageItem(key: string): Promise<boolean>;
  clearLocalStorage(): Promise<boolean>;
  closeApp(): Promise<string>;
  logMessage(message: string): Promise<boolean>;
  getHostInfo(): Promise<{
    version: string;
    platform: string;
    isWebView: boolean;
    hasLocalServer: boolean;
    hasBridge: boolean;
  }>;
};

// Create the bridge connection
const bridge = linkBridge<AppBridge>({
  onReady: async (method) => {
    console.log("🌉 Bridge is ready");
    const hostInfo = await method.getHostInfo();
    console.log("Host info:", hostInfo);
  },
});

/**
 * A hook that provides persistent state management using the bridge localStorage
 * Similar to useState but with automatic persistence
 *
 * @param key - The storage key to use for persistence
 * @param initialValue - The initial value to use if no stored value exists
 * @returns A tuple containing [value, setValue, isLoading, error]
 */
export function useStore<T>(
  key: string,
  initialValue?: T
): [
  T | undefined,
  (value: T | undefined) => Promise<void>,
  boolean,
  Error | null
] {
  const [value, setValue] = useState<T | undefined>(initialValue);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Load initial value from storage
  useEffect(() => {
    const loadValue = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const storedValue = await bridge.getLocalStorageItem(key);

        if (storedValue !== null) {
          try {
            // Try to parse as JSON first
            const parsedValue = JSON.parse(storedValue);
            setValue(parsedValue);
          } catch {
            // If JSON parsing fails, use the raw string value
            setValue(storedValue as T);
          }
        } else {
          // No stored value, use initial value
          setValue(initialValue);
        }
      } catch (err) {
        console.error(`Failed to load value for key "${key}":`, err);
        setError(
          err instanceof Error ? err : new Error("Failed to load stored value")
        );
        setValue(initialValue);
      } finally {
        setIsLoading(false);
      }
    };

    loadValue();
  }, [key, initialValue]);

  // Function to update the stored value
  const updateValue = useCallback(
    async (newValue: T | undefined) => {
      try {
        setError(null);

        if (newValue === undefined || newValue === null) {
          // Remove the item if value is undefined/null
          await bridge.removeLocalStorageItem(key);
          setValue(undefined);
        } else {
          // Store the new value
          const valueToStore =
            typeof newValue === "string" ? newValue : JSON.stringify(newValue);

          await bridge.setLocalStorageItem(key, valueToStore);
          setValue(newValue);
        }

        console.log(`📦 Updated storage for key "${key}":`, newValue);
      } catch (err) {
        console.error(`Failed to update value for key "${key}":`, err);
        setError(
          err instanceof Error
            ? err
            : new Error("Failed to update stored value")
        );
        throw err; // Re-throw so caller can handle if needed
      }
    },
    [key]
  );

  return [value, updateValue, isLoading, error];
}

/**
 * Hook to clear all localStorage data
 */
export function useClearAllStorage() {
  return useCallback(async () => {
    try {
      await bridge.clearLocalStorage();
      console.log("📦 Cleared all localStorage data");
      return true;
    } catch (err) {
      console.error("Failed to clear localStorage:", err);
      throw err;
    }
  }, []);
}

/**
 * Hook to remove a specific key from storage
 */
export function useRemoveStorageKey() {
  return useCallback(async (key: string) => {
    try {
      await bridge.removeLocalStorageItem(key);
      console.log(`📦 Removed storage key "${key}"`);
      return true;
    } catch (err) {
      console.error(`Failed to remove storage key "${key}":`, err);
      throw err;
    }
  }, []);
}
