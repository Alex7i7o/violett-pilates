/**
 * Haptic feedback utility
 * Safe wrapper around navigator.vibrate for supported devices (mainly Android and some webviews).
 * iOS Safari does not support navigator.vibrate, so this degrades gracefully.
 */

export const haptics = {
  success: () => {
    if (typeof window !== 'undefined' && navigator && 'vibrate' in navigator) {
      navigator.vibrate([15, 50, 15]); // Two short light taps
    }
  },
  error: () => {
    if (typeof window !== 'undefined' && navigator && 'vibrate' in navigator) {
      navigator.vibrate([50, 50, 50, 50]); // Heavy buzzing pattern
    }
  },
  warning: () => {
    if (typeof window !== 'undefined' && navigator && 'vibrate' in navigator) {
      navigator.vibrate([30, 40, 30]); 
    }
  },
  light: () => {
    if (typeof window !== 'undefined' && navigator && 'vibrate' in navigator) {
      navigator.vibrate(10); // Single light tap
    }
  },
  heavy: () => {
    if (typeof window !== 'undefined' && navigator && 'vibrate' in navigator) {
      navigator.vibrate(40); // Single heavy tap
    }
  }
};
