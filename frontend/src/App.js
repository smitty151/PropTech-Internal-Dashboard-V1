import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppShell from "./components/AppShell";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Developments from "./pages/Developments";
import Comps from "./pages/Comps";
import Calculator from "./pages/Calculator";
import DataSources from "./pages/DataSources";
import VerifyEmail from "./pages/VerifyEmail";
import ValuationMemo from "./pages/ValuationMemo";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify" element={<VerifyEmail />} />
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="developments" element={<Developments />} />
            <Route path="comps" element={<Comps />} />
            <Route path="calculator" element={<Calculator />} />
            <Route path="data-sources" element={<DataSources />} />
            <Route path="memo" element={<ValuationMemo />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
