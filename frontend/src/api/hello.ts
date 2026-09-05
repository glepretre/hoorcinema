export interface HelloResponse {
  message: string;
}

export async function getHello(): Promise<HelloResponse> {
  const response = await fetch("/api/hello/");

  if (!response.ok) {
    throw new Error("The cinema API is unavailable.");
  }

  return response.json() as Promise<HelloResponse>;
}
