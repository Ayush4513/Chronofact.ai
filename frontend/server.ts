import { file, serve } from "bun";
import { join } from "path";

const distDir = join(import.meta.dir, "dist");
const port = 3000;

console.log(`🚀 Frontend server starting on http://localhost:${port}`);

serve({
  port,
  async fetch(req) {
    const url = new URL(req.url);
    let pathname = url.pathname;
    
    // Handle favicon
    if (pathname === "/favicon.ico") {
      return new Response("", {
        status: 204,
        headers: { "Content-Type": "image/x-icon" }
      });
    }
    
    // Default to index.html
    if (pathname === "/" || pathname === "") {
      pathname = "/index.html";
    }
    
    const filePath = join(distDir, pathname);
    const f = file(filePath);
    
    if (await f.exists()) {
      // Determine content type
      let contentType = "application/octet-stream";
      if (pathname.endsWith(".html")) contentType = "text/html";
      else if (pathname.endsWith(".js")) contentType = "application/javascript";
      else if (pathname.endsWith(".css")) contentType = "text/css";
      else if (pathname.endsWith(".svg")) contentType = "image/svg+xml";
      else if (pathname.endsWith(".json")) contentType = "application/json";
      
      return new Response(f, {
        headers: { "Content-Type": contentType }
      });
    }
    
    // Proxy API requests to backend
    if (pathname.startsWith("/api/") || pathname === "/health") {
      const backendUrl = `http://localhost:8000${pathname}${url.search}`;
      try {
        const response = await fetch(backendUrl, {
          method: req.method,
          headers: req.headers,
          body: req.method !== "GET" ? await req.text() : undefined,
        });
        return new Response(await response.text(), {
          status: response.status,
          headers: { "Content-Type": response.headers.get("Content-Type") || "application/json" }
        });
      } catch (e) {
        return new Response(JSON.stringify({ error: "Backend unavailable" }), {
          status: 502,
          headers: { "Content-Type": "application/json" }
        });
      }
    }
    
    // Fallback to index.html for SPA routing
    const indexPath = join(distDir, "index.html");
    const indexFile = file(indexPath);
    if (await indexFile.exists()) {
      return new Response(indexFile, {
        headers: { "Content-Type": "text/html" }
      });
    }
    
    return new Response("Not Found", { status: 404 });
  },
});

console.log(`✅ Frontend running at http://localhost:${port}`);
console.log(`   Proxying /api/* to http://localhost:8000`);

