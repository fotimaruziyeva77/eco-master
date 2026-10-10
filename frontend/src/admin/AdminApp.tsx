import { useCallback, useEffect, useState, type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";

import { adminApi, setSignedOutHandler, type AdminMe } from "./api";
import { Layout } from "./Layout";
import { AccountPage } from "./pages/AccountPage";
import { AdminsPage } from "./pages/AdminsPage";
import { AuditPage } from "./pages/AuditPage";
import { ContentEditPage } from "./pages/ContentEditPage";
import { ContentListPage } from "./pages/ContentListPage";
import { FlagsPage } from "./pages/FlagsPage";
import { LoginPage } from "./pages/LoginPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SchedulePage } from "./pages/SchedulePage";
import { StatsPage } from "./pages/StatsPage";
import { UserPage } from "./pages/UserPage";
import { UsersPage } from "./pages/UsersPage";
import { WordsPage } from "./pages/WordsPage";
import { AdminContext, Loading, ToastProvider, useAdmin } from "./ui";

/** Pages outside the content editor's role (TZ 8.12: editors manage content only). */
function AdminOnly({ children }: { children: ReactNode }) {
  const { me } = useAdmin();
  return me.role === "admin" ? children : <Navigate to="/content/projects" replace />;
}

export function AdminApp() {
  // undefined: still checking the session cookie; null: signed out.
  const [me, setMe] = useState<AdminMe | null | undefined>(undefined);

  useEffect(() => {
    setSignedOutHandler(() => setMe(null));
    adminApi.me().then(setMe, () => setMe(null));
  }, []);

  const signOut = useCallback(() => {
    void adminApi.logout().finally(() => setMe(null));
  }, []);

  if (me === undefined) return <Loading />;
  if (me === null) return <LoginPage onSignedIn={setMe} />;

  const home = me.role === "admin" ? "/stats" : "/content/projects";
  return (
    <AdminContext.Provider value={{ me, signOut }}>
      <ToastProvider>
        <BrowserRouter basename="/admin">
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to={home} replace />} />
              <Route path="/stats" element={<AdminOnly><StatsPage /></AdminOnly>} />
              <Route path="/content/:type" element={<ContentListPage />} />
              <Route path="/content/:type/new" element={<ContentEditPage />} />
              <Route path="/content/:type/:id" element={<ContentEditPage />} />
              <Route path="/schedule" element={<SchedulePage />} />
              <Route path="/users" element={<AdminOnly><UsersPage /></AdminOnly>} />
              <Route path="/users/:id" element={<AdminOnly><UserPage /></AdminOnly>} />
              <Route path="/reports" element={<AdminOnly><ReportsPage /></AdminOnly>} />
              <Route path="/flags" element={<AdminOnly><FlagsPage /></AdminOnly>} />
              <Route path="/words" element={<AdminOnly><WordsPage /></AdminOnly>} />
              <Route path="/audit" element={<AdminOnly><AuditPage /></AdminOnly>} />
              <Route path="/admins" element={<AdminOnly><AdminsPage /></AdminOnly>} />
              <Route path="/account" element={<AccountPage />} />
              <Route path="*" element={<Navigate to={home} replace />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ToastProvider>
    </AdminContext.Provider>
  );
}
