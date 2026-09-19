import { Navigate, Route, Routes } from "react-router-dom";
import Shell from "./layout/Shell.jsx";
import AuditLog from "./pages/AuditLog.jsx";
import AwsPipeline from "./pages/AwsPipeline.jsx";
import CaseDetail from "./pages/CaseDetail.jsx";
import Cases from "./pages/Cases.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import EntityGraph from "./pages/EntityGraph.jsx";
import Ingest from "./pages/Ingest.jsx";
import IntelFeed from "./pages/IntelFeed.jsx";
import IocSearch from "./pages/IocSearch.jsx";
import Reports from "./pages/Reports.jsx";
import Settings from "./pages/Settings.jsx";
import ThreatActors from "./pages/ThreatActors.jsx";
import Ttps from "./pages/Ttps.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Dashboard />} />
        <Route path="cases" element={<Cases />} />
        <Route path="cases/:id" element={<CaseDetail />} />
        <Route path="ioc" element={<IocSearch />} />
        <Route path="graph" element={<EntityGraph />} />
        <Route path="intel" element={<IntelFeed />} />
        <Route path="actors" element={<ThreatActors />} />
        <Route path="ttps" element={<Ttps />} />
        <Route path="reports" element={<Reports />} />
        <Route path="ingest" element={<Ingest />} />
        <Route path="aws" element={<AwsPipeline />} />
        <Route path="audit" element={<AuditLog />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
