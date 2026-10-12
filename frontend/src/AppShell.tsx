import { lazy, Suspense, useEffect, type ComponentType } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router";

import { BottomNav } from "./components/BottomNav";
import { InlineLoading } from "./components/common";
import { HomeScreen } from "./screens/HomeScreen";
import { CelebrationProvider } from "./state/celebration";
import { startParam } from "./telegram";

// Home ships with the app; other screens load on first visit — a smaller first load (TZ 13).
const named = <K extends string>(load: () => Promise<Record<K, ComponentType>>, name: K) =>
  lazy(() => load().then((m) => ({ default: m[name] })));
const CardScreen = named(() => import("./screens/CardScreen"), "CardScreen");
const CategoryScreen = named(() => import("./screens/CategoryScreen"), "CategoryScreen");
const GamesScreen = named(() => import("./screens/games/GamesScreen"), "GamesScreen");
const QuizScreen = named(() => import("./screens/games/QuizScreen"), "QuizScreen");
const SortGameScreen = named(() => import("./screens/games/SortGameScreen"), "SortGameScreen");
const LearnScreen = named(() => import("./screens/LearnScreen"), "LearnScreen");
const PrivacyScreen = named(() => import("./screens/PrivacyScreen"), "PrivacyScreen");
const TermsScreen = named(() => import("./screens/PrivacyScreen"), "TermsScreen");
const ProfileScreen = named(() => import("./screens/ProfileScreen"), "ProfileScreen");
const SettingsScreen = named(() => import("./screens/SettingsScreen"), "SettingsScreen");
const ProjectScreen = named(() => import("./screens/ProjectScreen"), "ProjectScreen");
const RatingScreen = named(() => import("./screens/RatingScreen"), "RatingScreen");
const LessonScreen = named(() => import("./screens/teachers/LessonScreen"), "LessonScreen");
const ListingFormScreen = named(() => import("./screens/market/ListingFormScreen"), "ListingFormScreen");
const ListingScreen = named(() => import("./screens/market/ListingScreen"), "ListingScreen");
const MarketScreen = named(() => import("./screens/market/MarketScreen"), "MarketScreen");
const MyMarketScreen = named(() => import("./screens/market/MyMarketScreen"), "MyMarketScreen");
const TeachersScreen = named(() => import("./screens/teachers/TeachersScreen"), "TeachersScreen");
const ClassScreen = named(() => import("./screens/classes/ClassScreen"), "ClassScreen");
const JoinClassScreen = named(() => import("./screens/classes/JoinClassScreen"), "JoinClassScreen");
const MyClassScreen = named(() => import("./screens/classes/MyClassScreen"), "MyClassScreen");

function ScreenLoading() {
  return (
    <main className="screen">
      <InlineLoading />
    </main>
  );
}

const TAB_PATHS = new Set(["/", "/learn", "/games", "/rating", "/market", "/profile"]);
let startHandled = false;

function Layout() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    // Opened from a market message of the bot (startapp=market): straight to "my listings";
    // from a teacher's QR code (startapp=class_<code>): the class's join screen.
    if (startHandled) return;
    startHandled = true;
    const start = startParam();
    if (start === "market") navigate("/market/mine");
    else if (start?.startsWith("class_")) navigate(`/join/${start.slice("class_".length)}`);
  }, [navigate]);
  return (
    <Suspense fallback={<ScreenLoading />}>
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
        <Route path="/settings" element={<SettingsScreen />} />
        <Route path="/privacy" element={<PrivacyScreen />} />
        <Route path="/terms" element={<TermsScreen />} />
        <Route path="/teachers" element={<TeachersScreen />} />
        <Route path="/teachers/:slug" element={<LessonScreen />} />
        <Route path="/classes/:id" element={<ClassScreen />} />
        <Route path="/join/:code" element={<JoinClassScreen />} />
        <Route path="/my-class" element={<MyClassScreen />} />
        <Route path="/market" element={<MarketScreen />} />
        <Route path="/market/new" element={<ListingFormScreen />} />
        <Route path="/market/mine" element={<MyMarketScreen />} />
        <Route path="/market/:id" element={<ListingScreen />} />
        <Route path="/market/:id/edit" element={<ListingFormScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {TAB_PATHS.has(pathname) && <BottomNav />}
    </Suspense>
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
