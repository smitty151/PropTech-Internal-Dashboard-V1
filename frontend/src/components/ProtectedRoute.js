import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user } = useAuth();
  if (user === null) {
    return (
      <div className="min-h-screen flex items-center justify-center font-mono-ph text-sm" data-testid="auth-loading">
        Loading authenticated session…
      </div>
    );
  }
  if (user === false) return <Navigate to="/login" replace />;
  return children;
}
