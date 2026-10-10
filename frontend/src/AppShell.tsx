import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router";

import { BottomNav } from "./components/BottomNav";
import { CardScreen } from "./screens/CardScreen";
import { CategoryScreen } from "./screens/CategoryScreen";
import { ComingSoonScreen } from "./screens/ComingSoonScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { LearnScreen } from "./screens/LearnScreen";
import { PrivacyScreen } from "./screens/PrivacyScreen";
import { ProfileScreen } from "./screens/ProfileScreen";
import { ProjectScreen } from "./screens/ProjectScreen";

const TAB_PATHS = new Set(["/", "/learn", "/games", "/rating", "/profile"]);

function Layout() {
  const { pathname } = useLocation();
  return (
    <>
      <Routes>
        <Route path="/" element={<HomeScreen />} />
        <Route path="/learn" element={<LearnScreen />} />
        <Route path="/learn/:code" element={<CategoryScreen />} />
        <Route path="/projects/:slug" element={<ProjectScreen />} />
        <Route path="/cards/:slug" element={<CardScreen />} />
        <Route path="/games" element={<ComingSoonScreen icon="🎮" />} />
        <Route path="/rating" element={<ComingSoonScreen icon="🏆" />} />
        <Route path="/profile" element={<ProfileScreen />} />
        <Route path="/privacy" element={<PrivacyScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {TAB_PATHS.has(pathname) && <BottomNav />}
    </>
  );
}

export function AppShell() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
