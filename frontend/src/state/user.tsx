import { createContext, useContext, type ReactNode } from "react";

import type { User } from "../api/client";

type UserContextValue = { user: User; setUser: (user: User) => void };

const UserContext = createContext<UserContextValue | null>(null);

export function UserProvider({
  user,
  setUser,
  children,
}: UserContextValue & { children: ReactNode }) {
  return <UserContext.Provider value={{ user, setUser }}>{children}</UserContext.Provider>;
}

export function useUser(): UserContextValue {
  const value = useContext(UserContext);
  if (!value) throw new Error("useUser must be used inside UserProvider");
  return value;
}
