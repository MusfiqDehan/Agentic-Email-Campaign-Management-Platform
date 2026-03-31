// Declares the process.env global for Expo public environment variables.
// Once `expo` is installed, expo/types provides a more complete declaration.
// This file allows TypeScript to resolve EXPO_PUBLIC_* variables before npm install.
declare const process: {
  env: {
    EXPO_PUBLIC_API_URL?: string;
    EXPO_PUBLIC_WS_URL?: string;
    [key: string]: string | undefined;
  };
};
