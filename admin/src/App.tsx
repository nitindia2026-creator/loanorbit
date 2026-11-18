import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Customers } from './pages/Customers';
import { KYCQueue } from './pages/KYCQueue';
import { UnderwritingQueue } from './pages/UnderwritingQueue';
import { Ledger } from './pages/Ledger';
import { AuditLogs } from './pages/AuditLogs';
import { Disbursements } from './pages/Disbursements';
import { Repayments } from './pages/Repayments';
import { Support } from './pages/Support';
import { getAuthToken } from './lib/api';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = getAuthToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="customers" element={<Customers />} />
          <Route path="kyc-queue" element={<KYCQueue />} />
          <Route path="underwriting" element={<UnderwritingQueue />} />
          <Route path="disbursements" element={<Disbursements />} />
          <Route path="repayments" element={<Repayments />} />
          <Route path="support" element={<Support />} />
          <Route path="ledger" element={<Ledger />} />
          <Route path="audit-logs" element={<AuditLogs />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};
