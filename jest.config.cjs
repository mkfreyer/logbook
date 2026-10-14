module.exports = {
  preset: 'jest-expo',
  testMatch: ['<rootDir>/tests/*.test.tsx'],
  setupFiles: ['react-native-gesture-handler/jestSetup.js'],
  setupFilesAfterEnv: ['<rootDir>/tests/jest-setup.ts'],
  cacheDirectory: '<rootDir>/.jest-cache',
  clearMocks: true,
};
