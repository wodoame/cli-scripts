#!/usr/bin/env bash

set -e

# Defaults
PROJECT_NAME=""
USE_ROUTER=true
INIT_GIT=false

show_help() {
  echo "Usage: $0 [project-name] [options]"
  echo ""
  echo "Creates a new React project with:"
  echo "  - Vite (via shadcn CLI)"
  echo "  - shadcn/ui preconfigured"
  echo "  - Optional React Router setup"
  echo ""
  echo "Options:"
  echo "  -h, --help         Show this help message"
  echo "  --no-router        Skip React Router setup"
  echo "  --git              Initialize git repository"
  echo ""
  echo "Examples:"
  echo "  $0 my-app"
  echo "  $0 my-app --git"
  echo "  $0 my-app --no-router"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
  -h | --help)
    show_help
    exit 0
    ;;
  --no-router)
    USE_ROUTER=false
    shift
    ;;
  --git)
    INIT_GIT=true
    shift
    ;;
  *)
    if [ -z "$PROJECT_NAME" ]; then
      PROJECT_NAME=$1
    else
      echo "Unknown argument: $1"
      exit 1
    fi
    shift
    ;;
  esac
done

check_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Error: Required command '$1' is not installed."
    echo "Please install $1 before running this script."
    exit 1
  fi
}

check_command bun
check_command node
if [ "$INIT_GIT" = true ]; then
  check_command git
fi

# Prompt if no project name
if [ -z "$PROJECT_NAME" ]; then
  read -p "Enter project name: " PROJECT_NAME
fi

echo "Creating project: $PROJECT_NAME"
echo ""

bunx --bun shadcn@latest init --name $PROJECT_NAME -t vite

cd "$PROJECT_NAME"

# Router setup
if [ "$USE_ROUTER" = true ]; then
  echo "Installing react-router-dom..."
  bun add react-router-dom

  mkdir -p src/pages

  cat <<'EOF' >src/pages/home.tsx
export default function Home() {
  return (
    <div>
      <h2 className="text-lg font-semibold">Home</h2>
      <p>Welcome to your app 🚀</p>
    </div>
  )
}
EOF

  cat <<'EOF' >src/App.tsx
import { Outlet } from "react-router-dom"
import { Button } from "@/components/ui/button"

export function App() {
  return (
    <div className="flex min-h-svh p-6">
      <div className="flex max-w-md min-w-0 flex-col gap-4 text-sm leading-loose">
        <div>
          <h1 className="font-medium">Project ready!</h1>
          <p>You may now add components and start building.</p>
          <p>We've already added the button component for you.</p>
          <Button className="mt-2">Button</Button>
        </div>

        <Outlet />

        <div className="font-mono text-xs text-muted-foreground">
          (Press <kbd>d</kbd> to toggle dark mode)
        </div>
      </div>
    </div>
  )
}

export default App
EOF

  cat <<'EOF' >src/main.tsx
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { createBrowserRouter, RouterProvider } from "react-router-dom"

import "./index.css"
import { ThemeProvider } from "@/components/theme-provider"
import App from "./App"
import Home from "./pages/home"

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <Home />,
      },
    ],
  },
])

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  </StrictMode>
)
EOF

fi

# Debug and Sourcemap setup
echo "Configuring source maps and debug scripts..."
bun add -d cross-env

cat <<'NODE_EOF' > modify_config.js
import fs from 'fs';

// 1. Update package.json
let pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
pkg.scripts['build:watch'] = 'tsc -b --watch & vite build --watch';
pkg.scripts['build:debug'] = 'cross-env VITE_SOURCEMAP=true tsc -b && cross-env VITE_SOURCEMAP=true vite build';
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));

NODE_EOF

node modify_config.js
rm modify_config.js

cat <<'EOF' > vite.config.ts
import path from "path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const enableSourcemap = env.VITE_SOURCEMAP === "true";

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    build: {
      sourcemap: enableSourcemap,
      assetsDir: "static",
    },
  };
});
EOF

# Git setup
if [ "$INIT_GIT" = true ]; then
  echo "Initializing git repository..."
  git init
  git add .
  git commit -m "Initial commit"
fi

echo ""
echo "✅ Project setup complete!"
echo "👉 Run: cd $PROJECT_NAME && bun dev"
