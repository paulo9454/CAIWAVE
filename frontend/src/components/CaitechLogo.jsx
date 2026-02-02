import React from "react";

/**
 * CAITECH Official Logo Component
 * 
 * LOCKED BRANDING - Only CAITECH admin can modify
 * 
 * Specifications:
 * - Blue background: #0032FA
 * - White WiFi signal icon
 * - Flat design, no gradients, no shadows
 * - Used across: Favicon, Login, Dashboards, Captive Portal, Marketing
 */

export const CaitechLogo = ({ size = 32, className = "" }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      width={size}
      height={size}
      className={className}
    >
      {/* Blue Background */}
      <rect width="32" height="32" rx="4" fill="#0032FA" />
      
      {/* WiFi Signal Icon (White) */}
      <g fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round">
        {/* Signal Arc 1 (Outermost) */}
        <path d="M 7 17 Q 16 7 25 17" />
        {/* Signal Arc 2 */}
        <path d="M 10 19 Q 16 11 22 19" />
        {/* Signal Arc 3 */}
        <path d="M 13 21 Q 16 16 19 21" />
      </g>
      
      {/* Center Dot */}
      <circle cx="16" cy="25" r="2" fill="#FFFFFF" />
    </svg>
  );
};

export const CaitechLogoLarge = ({ size = 64, className = "" }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      width={size}
      height={size}
      className={className}
    >
      {/* Blue Background */}
      <rect width="512" height="512" rx="64" fill="#0032FA" />
      
      {/* WiFi Signal Icon (White) */}
      <g fill="none" stroke="#FFFFFF" strokeWidth="36" strokeLinecap="round">
        {/* Signal Arc 1 (Outermost) */}
        <path d="M 128 280 Q 256 120 384 280" />
        {/* Signal Arc 2 */}
        <path d="M 176 310 Q 256 190 336 310" />
        {/* Signal Arc 3 */}
        <path d="M 218 340 Q 256 260 294 340" />
      </g>
      
      {/* Center Dot */}
      <circle cx="256" cy="380" r="28" fill="#FFFFFF" />
    </svg>
  );
};

// Logo with text for headers
export const CaitechLogoWithText = ({ size = 32, className = "" }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <CaitechLogo size={size} />
      <span className="font-semibold text-lg tracking-tight">CAITECH</span>
    </div>
  );
};

export default CaitechLogo;
