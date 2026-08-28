import "../../styles/StudentDash.css";
import { signOut } from "aws-amplify/auth";

function clearAmplifyStorage() {
  Object.keys(localStorage)
    .filter(key => key.startsWith("CognitoIdentityServiceProvider") || key.startsWith("amplify"))
    .forEach(key => localStorage.removeItem(key));
}

function StuTitle() {
  const handleSignOut = async () => {
    try {
      await signOut({ global: true });
    } catch (e) {}
    clearAmplifyStorage();
    window.location.replace("/");
  };

    return (
        <div className="Title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <img src="/EducationCap.png" width="40" height="40" alt="logo" />
            <div className="TitleR">
              <h1>VivāVoce</h1>
              <p>Student Dashboard</p>
            </div>
          </div>
          <button className="StuSignOut" onClick={handleSignOut}>Sign Out</button>
        </div>
      );
    }

export default StuTitle;