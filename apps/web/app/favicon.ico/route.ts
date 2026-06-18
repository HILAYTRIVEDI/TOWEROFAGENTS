const ICON = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0f4935"/>
  <path d="M32 10 52 54h-9l-4-9H25l-4 9h-9L32 10Zm4 27-4-10-4 10h8Z" fill="#d6f06c"/>
</svg>`;

export function GET() {
  return new Response(ICON, {
    headers: {
      "Content-Type": "image/svg+xml",
      "Cache-Control": "public, max-age=86400",
    },
  });
}
