// Jest has no UI runtime. Native gesture dispatch is exercised separately via RNGH utilities.
import { jest } from '@jest/globals';
jest.mock('react-native-worklets', () => require('react-native-worklets/src/mock'));
jest.mock('react-native-reanimated', () => require('react-native-reanimated/mock'));
