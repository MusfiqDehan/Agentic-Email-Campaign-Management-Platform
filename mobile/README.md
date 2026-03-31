# Email Campaign Management Platform — Mobile App

A fully functional cross-platform React Native / Expo mobile app that mirrors all features of the Next.js web frontend, including authentication, campaign management, contacts, templates, and real-time notifications.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Node.js | 18+ | `node -v` to check |
| npm | 9+ | Comes with Node |
| Expo CLI | latest | Use `npx expo` from this project |
| EAS CLI | latest | Required for Android dev builds on SDK 55 |
| iOS Simulator | Xcode 15+ | macOS only |
| Android Emulator | Android Studio | All platforms |
| Android device | optional | Use a custom development build instead of Expo Go |

---

## Step-by-Step Setup

### 1. Clone and navigate

```bash
git clone <repo-url>
cd <repo-root>/mobile
```

### 2. Install dependencies

```bash
npm install
```

### 3. Create `.env` file

Create a file named `.env` in the `mobile/` directory:

```env
EXPO_PUBLIC_API_URL=http://localhost:8001/api/v1
EXPO_PUBLIC_WS_URL=ws://localhost:8001
```

> **Physical device note:** `localhost` won't reach your dev machine from a phone. Replace `localhost` with your machine's local IP address (e.g., `192.168.1.100`):
> ```env
> EXPO_PUBLIC_API_URL=http://192.168.1.100:8001/api/v1
> EXPO_PUBLIC_WS_URL=ws://192.168.1.100:8001
> ```
> Find your IP with `ipconfig` (Windows) or `ifconfig` / `ip a` (Linux/macOS).

### 4. Start the backend

Ensure the Django backend is running and accessible on port `8001`. See the root `DEPLOYMENT.md` for backend setup steps.

### 5. Install EAS CLI and log in

```bash
npm install -g eas-cli
eas login
```

### 6. Build and install the Android development client

```bash
npm run build:development:android
```

Install the generated APK on your Android device or emulator.

### 7. Start the Expo development server for the dev client

```bash
npm run start:dev-client
```

You will see a QR code in the terminal.

---

## Running the App

### Option A — Android Development Build (recommended)

1. Run `npm run build:development:android` to create a custom dev-client APK.
2. Install that APK on your Android device or emulator.
3. Start Metro with `npm run start:dev-client`.
4. Open the installed dev client and connect to the running project.

### Option B — iOS Simulator (macOS only)

With the dev server running, press **`i`** in the terminal (or run `npx expo start --ios`). Requires Xcode and iOS Simulator installed.

### Option C — Android Emulator

Use `npm run run:android` for a local native run, or install the Android development client and connect it to `npm run start:dev-client`.

### Option D — Web (limited)

Press **`w`** for a browser preview via Expo Web. Not all native features (SecureStore, ImagePicker) are available in the browser.

---

## Build Profiles (EAS)

Development build for Android:

```bash
npm run build:development:android
```

Preview APK for Android:

```bash
npm run build:preview:android
```

Production build for Android:

```bash
npx eas build --profile production --platform android
```

Production build for iOS:

```bash
npx eas build --profile production --platform ios
```

---

## Project Structure

```
mobile/
├── app/
│   ├── _layout.tsx          # Root layout (AuthProvider + SplashScreen)
│   ├── index.tsx            # Auth redirect entry point
│   ├── (auth)/              # Unauthenticated screens
│   │   ├── login.tsx
│   │   ├── signup.tsx
│   │   ├── forgot-password.tsx
│   │   ├── reset-password.tsx
│   │   └── verify-email.tsx
│   └── (tabs)/              # Authenticated tab screens
│       ├── dashboard.tsx
│       ├── campaigns.tsx
│       ├── campaign/[id].tsx
│       ├── contacts.tsx
│       ├── contact-list/[id].tsx
│       ├── templates.tsx
│       ├── template/[id].tsx
│       ├── notifications.tsx
│       └── profile.tsx
├── components/
│   └── ui/                  # Reusable UI components
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Badge.tsx
│       ├── Card.tsx
│       ├── LoadingSpinner.tsx
│       └── EmptyState.tsx
├── config/
│   ├── axios.ts             # Axios instance with auth interceptors
│   └── constants.ts         # Colors, spacing, API URLs
├── contexts/
│   └── AuthContext.tsx      # Auth state, login/logout, token management
├── hooks/
│   └── useNotifications.ts  # Notifications state hook
├── services/
│   ├── auth.ts
│   ├── campaigns.ts
│   ├── contacts.ts
│   ├── notifications.ts
│   ├── profile.ts
│   └── templates.ts
├── .env                     # Local environment variables
├── app.json                 # Expo config
├── babel.config.js
├── package.json
└── tsconfig.json
```

---

## Features

| Screen | Description |
|---|---|
| Login | Email/password login with error handling |
| Sign Up | Full registration with organization creation |
| Forgot Password | Password reset via email |
| Reset Password | Token-based password reset |
| Dashboard | Stats overview, recent campaigns, activity feed |
| Campaigns | List, search, send/pause/resume/delete campaigns |
| Campaign Detail | Performance stats with delivery/open/click rates |
| Contacts | Manage contact lists, view contacts per list |
| Templates | Browse/search templates, duplicate, preview |
| Notifications | Unread/read tabs, mark as read, delete |
| Profile | Edit profile info, upload avatar, change password |

---

## Troubleshooting

**"Network request failed"** — Your `.env` API URL is unreachable. If on a physical device, replace `localhost` with your machine's LAN IP.

**"Cannot find module '@/…'"** — Run `npx expo start --clear` to clear the Metro bundler cache.

**Expo Go says the project is incompatible** — This app is on Expo SDK 55. Use the custom development build flow above instead of Expo Go.

**The phone cannot reach the API** — Verify `EXPO_PUBLIC_API_URL` and `EXPO_PUBLIC_WS_URL` point to your machine's LAN IP, not `localhost`.

**iOS build issues** — Run `npx pod-install` inside the `ios/` directory (only relevant for bare workflow).
