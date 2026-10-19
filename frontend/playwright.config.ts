import { defineConfig, devices } from "@playwright/test";

// End-to-end tests run against a live stack (`python tasks.py up` + demo users seeded,
// `python tasks.py e2e`). They are not part of the per-push CI, which has no stack.
export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
