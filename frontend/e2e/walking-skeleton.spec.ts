import { expect, test } from "@playwright/test";

// Milestone M1 (Roadmap Week 2): a ticket travels UI -> API -> pipeline -> database ->
// queue with no manual step. Needs the demo accounts (python tasks.py demo).
const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";
const ADMIN = { email: "admin@demo.local", password: "Demo@123" };

test("a submitted ticket is classified, routed and appears for staff", async ({ page, request }) => {
  const stamp = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const email = `e2e.user.${stamp}@example.com`;
  const subject = `E2E ${stamp}: VPN stuck on connecting`;

  // 1. Register a new end user through the UI.
  await page.goto("/login");
  await page.getByRole("button", { name: /create an account/i }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Full name").fill("E2E User");
  await page.getByLabel("Password").fill("Password@123");
  await page.getByRole("button", { name: "Create account" }).click();

  // 2. Submit a ticket.
  await page.getByRole("button", { name: "New ticket" }).click();
  await page.getByLabel("Subject").fill(subject);
  await page.getByLabel("Description").fill("Since this morning the VPN client hangs on connecting at the hotel.");
  await page.getByRole("button", { name: "Submit ticket" }).click();
  await expect(page.getByText(subject)).toBeVisible();

  // 3. The pipeline runs in the background with no manual step: poll the API as admin
  //    until the ticket has left `submitted` (classified -> routed -> drafted | escalated).
  const login = await request.post(`${API_URL}/auth/login`, {
    form: { username: ADMIN.email, password: ADMIN.password },
  });
  expect(login.ok()).toBeTruthy();
  const { access_token } = await login.json();
  const headers = { Authorization: `Bearer ${access_token}` };

  let ticket: { status: string; department_id: string | null } | undefined;
  await expect
    .poll(
      async () => {
        const res = await request.get(`${API_URL}/tickets`, { headers });
        const all = (await res.json()) as Array<{ subject: string; status: string; department_id: string | null }>;
        ticket = all.find((t) => t.subject === subject);
        return ticket?.status;
      },
      { timeout: 60_000, intervals: [1_000] },
    )
    .toMatch(/^(drafted|escalated)$/);
  expect(ticket?.department_id).toBeTruthy();

  // 4. Staff see it: log out, log in as admin, find it in the ticket list.
  await page.getByRole("button", { name: "Log out" }).click();
  await page.getByLabel("Email").fill(ADMIN.email);
  await page.getByLabel("Password").fill(ADMIN.password);
  await page.getByRole("button", { name: "Log in" }).click();
  await page.waitForURL(/\/admin/);
  await page.goto("/admin/tickets");
  // The admin list holds every ticket in the database; narrow it with the page's own
  // search box, and allow for a slow first load when the pipeline is busy.
  await page.getByRole("searchbox").or(page.getByPlaceholder(/search/i)).first().fill(stamp);
  await expect(page.getByText(subject)).toBeVisible({ timeout: 20_000 });
});
