import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router";

import { BottomNav } from "./components/BottomNav";
import { CardScreen } from "./screens/CardScreen";
import { CategoryScreen } from "./screens/CategoryScreen";
import { GamesScreen } from "./screens/games/GamesScreen";
import { QuizScreen } from "./screens/games/QuizScreen";
import { SortGameScreen } from "./screens/games/SortGameScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { LearnScreen } from "./screens/LearnScreen";
import { PrivacyScreen, TermsScreen } from "./screens/PrivacyScreen";
import { ProfileScreen } from "./screens/ProfileScreen";
import { ProjectScreen } from "./screens/ProjectScreen";
import { RatingScreen } from "./screens/RatingScreen";
import { LessonScreen } from "./screens/teachers/LessonScreen";
import { TeachersScreen } from "./screens/teachers/TeachersScreen";
import { CelebrationProvider } from "./state/celebration";

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
        <Route path="/games" element={<GamesScreen />} />
        <Route path="/games/quiz" element={<QuizScreen />} />
        <Route path="/games/sort" element={<SortGameScreen />} />
        <Route path="/rating" element={<RatingScreen />} />
        <Route path="/profile" element={<ProfileScreen />} />
        <Route path="/privacy" element={<PrivacyScreen />} />
        <Route path="/terms" element={<TermsScreen />} />
        <Route path="/teachers" element={<TeachersScreen />} />
        <Route path="/teachers/:slug" element={<LessonScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {TAB_PATHS.has(pathname) && <BottomNav />}
    </>
  );
}

export function AppShell() {
  return (
    <BrowserRouter>
      <CelebrationProvider>
        <Layout />
      </CelebrationProvider>
    </BrowserRouter>
  );
}
