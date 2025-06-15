import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import React from "react";
import "./index.css";

// ===== MONKEY PATCH useState =====
// This must happen BEFORE importing App.jsx

// Store original useState
const originalUseState = React.useState;

// Create persistent useState
function persistentUseState(initialValue) {
  const keyRef = React.useRef(null);

  if (!keyRef.current) {
    // Generate a unique key for this useState call
    const error = new Error();
    const stack = error.stack || "";
    // Use first few stack frames to create a semi-deterministic key
    const stackLines = stack.split("\n").slice(2, 5).join("");
    const hash = btoa(stackLines.replace(/[^a-zA-Z0-9]/g, "")).slice(0, 8);
    keyRef.current = `state-${hash}-${Date.now().toString(36)}`;
  }

  const key = keyRef.current;

  // Load from localStorage
  const getInitialValue = () => {
    try {
      const stored = localStorage.getItem(key);
      return stored !== null ? JSON.parse(stored) : initialValue;
    } catch {
      return initialValue;
    }
  };

  const [state, setState] = originalUseState(getInitialValue);

  // Persist on every state change
  const setPersistentState = React.useCallback(
    (newState) => {
      setState((prevState) => {
        const nextState =
          typeof newState === "function" ? newState(prevState) : newState;

        try {
          localStorage.setItem(key, JSON.stringify(nextState));
        } catch (error) {
          console.warn("Failed to persist state:", error);
        }

        return nextState;
      });
    },
    [key]
  );

  return [state, setPersistentState];
}

// Patch React.useState (for React.useState usage)
React.useState = persistentUseState;

// For ES6 named imports, we need to intercept at the module level
// This is the key part - we modify React's export before any other imports
Object.defineProperty(React, "useState", {
  value: persistentUseState,
  writable: false,
  configurable: true,
});

// ===== IMPORT APP AFTER PATCHING =====
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
