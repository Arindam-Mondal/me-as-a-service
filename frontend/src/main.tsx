import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Self-hosted variable fonts (no CDN).
import "@fontsource-variable/shantell-sans";
import "@fontsource-variable/hanken-grotesk";

import "./styles/tokens.css";
import "./styles/global.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
