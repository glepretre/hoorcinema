import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

test("renders the Hello, World message returned by the backend", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ message: "Hello, World!" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );

  await screen.findByRole("heading", { name: "Hello, World!" });
  expect(fetch).toHaveBeenCalledWith("/api/hello/");
});
