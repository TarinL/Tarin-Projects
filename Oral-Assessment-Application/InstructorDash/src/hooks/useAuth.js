import { useState, useEffect } from "react";
import { getCurrentUser, fetchAuthSession, signOut } from "aws-amplify/auth";

// Use this hook in any page to get the current user and their group
// Example: const { user, group, logout } = useAuth();
export function useAuth() {
  const [user, setUser] = useState(null);
  const [group, setGroup] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkUser();
  }, []);

  async function checkUser() {
    try {
      const currentUser = await getCurrentUser();
      const session = await fetchAuthSession();
      const groups =
        session.tokens?.accessToken?.payload?.["cognito:groups"] || [];
      setUser(currentUser);
      setGroup(groups[0] || null);
    } catch {
      setUser(null);
      setGroup(null);
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    await signOut();
    setUser(null);
    setGroup(null);
  }

  return { user, group, loading, logout };
}
