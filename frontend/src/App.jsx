import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard";
import ForgotPassword from "./pages/ForgotPassword";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import Sites from "./pages/Sites";
import Cameras from "./pages/Cameras";
import Workers from "./pages/Workers";
import PpeRules from "./pages/PpeRules";
import LiveMonitoring from "./pages/LiveMonitoring";
import VideoAnalysis from "./pages/VideoAnalysis";
import ImageAnalysis from "./pages/ImageAnalysis";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/live" element={<LiveMonitoring />} />
          <Route path="/video-analysis" element={<VideoAnalysis />} />
          <Route path="/image-analysis" element={<ImageAnalysis />} />
          <Route path="/sites" element={<Sites />} />
          <Route path="/cameras" element={<Cameras />} />
          <Route path="/workers" element={<Workers />} />
          <Route path="/ppe-rules" element={<PpeRules />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
