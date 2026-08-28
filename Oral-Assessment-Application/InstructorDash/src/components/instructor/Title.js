import { signOut } from "aws-amplify/auth";
import { NavLink } from "react-router-dom";

function Title() {
  const handleSignOut = async () => {
    try {
      await signOut({ global: true });
    } catch (e) {}
    window.location.replace("/");
  };

  return (
    <div className="Title">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <img src="/EducationCap.png" width="40" height="40" alt="logo" />
        <div className="TitleR">
          <h1>VivāVoce</h1>
          <p>Instructor Dashboard</p>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <NavLink
          to="/instructor-dashboard"
          style={({isActive}) => ({
            fontFamily: 'Verdana, sans-serif',
            fontSize: '12px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: isActive ? '#ffffff' : '#3b474f',
            textDecoration: 'none',
            backgroundColor: isActive ? '#264a64' : 'transparent',
            padding: '6px 12px',
            borderRadius: '4px',
          })}
        >
          Dashboard
        </NavLink>

        <NavLink
          to="/instructor/interviews"
          style={({ isActive }) => ({
            fontFamily: 'Verdana, sans-serif',
            fontSize: '12px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: isActive ? '#ffffff' : '#3b474f',
            textDecoration: 'none',
            backgroundColor: isActive ? '#264a64' : 'transparent',
            padding: '6px 12px',
            borderRadius: '4px',
          })}
        >
          Grades & Interviews
        </NavLink>
        <NavLink
          to="/instructor/classes"
          style={({ isActive }) => ({
            fontFamily: 'Verdana, sans-serif',
            fontSize: '12px',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: isActive ? '#ffffff' : '#3b474f',
            textDecoration: 'none',
            backgroundColor: isActive ? '#264a64' : 'transparent',
            padding: '6px 12px',
            borderRadius: '4px',
          })}
        >
          Classes
        </NavLink>
        <button className="SignOut" onClick={handleSignOut}>Sign Out</button>
      </div>
    </div>
  );
}

export default Title;