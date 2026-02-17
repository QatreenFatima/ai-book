/**
 * Frontend configuration.
 * Change BACKEND_URL for production deployment.
 */
export const BACKEND_URL =
  process.env.NODE_ENV === "production"
    ? "https://backend-tau-gold-51.vercel.app"
    : "http://localhost:8000";
