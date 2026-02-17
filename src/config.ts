/**
 * Frontend configuration.
 * Change BACKEND_URL for production deployment.
 */
export const BACKEND_URL =
  process.env.NODE_ENV === "production"
    ? "https://your-backend.onrender.com" // TODO: Replace with actual deployment URL
    : "http://localhost:8000";
