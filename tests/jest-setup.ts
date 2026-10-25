// Jest has no UI runtime. Native gesture dispatch is exercised separately via RNGH utilities.
import { jest } from '@jest/globals';
// Reanimated 4.7's official mock imports its native initializer through index.
// Jest has no native CSS event dispatcher (JSReanimated throws on registration).
// Stub only that native initialization; keep the library's public Jest mock.
jest.mock('react-native-reanimated/src/initializers', () => ({ initializeReanimatedModule: jest.fn() }));
jest.mock('react-native-worklets', () => require('react-native-worklets/src/mock'));
jest.mock('react-native-reanimated', () => require('react-native-reanimated/mock'));
