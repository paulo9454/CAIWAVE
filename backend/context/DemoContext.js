import { createContext, useState } from "react";

export const DemoContext = createContext();

export const DemoProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [connected, setConnected] = useState(false);

  return (
    <DemoContext.Provider value={{
      user,
      setUser,
      session,
      setSession,
      connected,
      setConnected
    }}>
      {children}
    </DemoContext.Provider>
  );
};
