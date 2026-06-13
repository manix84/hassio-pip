import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import rootPackage from "../package.json";

export default defineConfig({
  plugins: [react()],
  base: "./",
  define: {
    __PROJECT_VERSION__: JSON.stringify(rootPackage.version)
  }
});
