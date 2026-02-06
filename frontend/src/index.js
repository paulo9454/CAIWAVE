import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Remove external badges
const removeBadges = () => {
  document.querySelectorAll('a').forEach(el => {
    const href = el.getAttribute('href') || '';
    const text = el.textContent || '';
    if (href.includes('emergent') || text.includes('Made with')) {
      el.remove();
    }
  });
  document.querySelectorAll('[id*="emergent"]').forEach(el => el.remove());
};

// Run immediately and on intervals
removeBadges();
setInterval(removeBadges, 200);

// Add CSS to hide badges
const style = document.createElement('style');
style.textContent = `
  a[href*="emergent"], [id*="emergent"], 
  a[style*="position: fixed"][style*="bottom"][style*="right"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
  }
`;
document.head.appendChild(style);

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
