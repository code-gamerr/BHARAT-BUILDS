import { Route, Routes } from "react-router-dom";
import Landing from "./landing/Landing";
import Login from "./Login";
import {
  CaseDetail,
  ConsoleLayout,
  Dashboard,
  Intelligence,
  Queue,
  RequireAuth,
} from "./Console";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/app"
        element={
          <RequireAuth>
            <ConsoleLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="intelligence" element={<Intelligence />} />
        <Route path="queue" element={<Queue />} />
        <Route path="cases/:id" element={<CaseDetail />} />
      </Route>
    </Routes>
  );
}
