import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // If 3000 is already taken, Vite silently picks another port (3003,
    // 3004, ...). That new origin is NOT in the backend's CORS_ORIGINS list,
    // which produces exactly the "CORS error" symptom in DevTools even
    // though the CORS config itself is correct. strictPort makes Vite fail
    // loudly instead of shifting ports silently.
    strictPort: true,
  },
});
