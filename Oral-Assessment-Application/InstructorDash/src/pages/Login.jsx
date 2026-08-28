import { useState } from "react";
import { signIn, confirmSignIn, fetchAuthSession, signOut } from "aws-amplify/auth";
import { useNavigate } from "react-router-dom";
import "../config/awsConfig.js";
import "../styles/shared.css";
import "../styles/Login.css";

export default function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [needsNewPassword, setNeedsNewPassword] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
await signOut({ global: true });
    } catch {}
      try {
      const result = await signIn({ username: email, password });
      if (result.nextStep?.signInStep === "CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED") {
        setNeedsNewPassword(true);
        setLoading(false);
        return;
      }
      await redirectByGroup();
    } catch (err) {
      setError(err.message || "Login failed. Please check your details.");
    } finally {
      setLoading(false);
    }
  };

  const handleNewPassword = async (e) => {
    e.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await confirmSignIn({
        challengeResponse: newPassword,
        options: {
          userAttributes: {
            preferred_username: email,
            given_name: firstName,
            family_name: lastName,
          }
        }
      });
      await fetchAuthSession({ forceRefresh: true });
      await redirectByGroup();
    } catch (err) {
      setError(err.message || "Failed to set new password.");
    } finally {
      setLoading(false);
    }
  };

  const redirectByGroup = async () => {
    const session = await fetchAuthSession({ forceRefresh: true });
    console.log("ID TOKEN PAYLOAD:", session.tokens?.idToken?.payload);
    const groups = session.tokens?.accessToken?.payload?.["cognito:groups"] || [];
    const emailVal = session.tokens?.idToken?.payload?.email || "";
    const username = session.tokens?.idToken?.payload?.["cognito:username"] || "";

    const userObject = { email: emailVal, username, group: groups[0], studentId: username };

    if (groups.includes("Teachers")) {
      onLoginSuccess("Teachers", userObject);
      navigate("/instructor-dashboard");
    } else if (groups.includes("Students")) {
      onLoginSuccess("Students", userObject);
      navigate("/student-dashboard");
    } else {
      setError("Your account has not been assigned a role yet. Please contact support.");
    }
  };

  if (needsNewPassword) {
      return (
        <div className="LoginPage">
          <div className="LoginCard">
            <div className="LoginHeader">
              <h1>Set New Password</h1>
              <p>Please complete your profile to continue.</p>
            </div>
            <form onSubmit={handleNewPassword} className="LoginForm">
              <div className="LoginField">
                <label>First Name</label>
                <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="Jane" required />
              </div>
              <div className="LoginField">
                <label>Last Name</label>
                <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Smith" required />
              </div>
              <div className="LoginField">
                <label>New Password</label>
                <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="••••••••" required />
              </div>
              <div className="LoginField">
                <label>Confirm New Password</label>
                <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="••••••••" required />
              </div>
              {error && <div className="LoginError"><span>!</span><span>{error}</span></div>}
              <button type="submit" disabled={loading} className="LoginButton">
                {loading ? "Saving..." : "Complete Setup →"}
              </button>
            </form>
          </div>
        </div>
      );
    }

    return (
      <div className="LoginPage">
        <div className="LoginCard">
          <div className="LoginHeader">
            <h1>Sign In</h1>
          </div>
          <form onSubmit={handleLogin} className="LoginForm">
            <div className="LoginField">
              <label>Use your email to sign in. Do not enter your username.</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
            </div>
            <div className="LoginField">
              <label>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
            </div>
            {error && <div className="LoginError"><span>!</span><span>{error}</span></div>}
            <button type="submit" disabled={loading} className="LoginButton">
              {loading ? "Signing in..." : "Sign in →"}
            </button>
          </form>
          <p className="LoginFooter">Access is by invitation only. Contact your administrator if you need an account.</p>
        </div>
      </div>
    );
  }