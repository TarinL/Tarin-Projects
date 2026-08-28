import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { getCurrentUser, fetchAuthSession, signOut } from "aws-amplify/auth";
import "./config/awsConfig.js";
import "./styles/shared.css";
import axios from "axios";

// Existing instructor components
import Title from "./components/instructor/Title.js";
import Tallys from "./components/instructor/Tallys.js";
import Assignments from "./components/instructor/Assignments.js";
import TitleInterview from "./components/gradebook/TitleInterview";
import ScheduledView from "./components/gradebook/ScheduledView";
import GradeBook from "./components/gradebook/GradeBook";
import InterviewLoading from "./components/student/InterviewLoading";
import ClassCreation from "./components/instructor/ClassCreation";
import StuGradeBook from "./components/student/StuGradeBook";

// student components 
import StudentDash from "./components/student/StudentDash.js";

// Login page
import Login from "./pages/Login.jsx";

// The existing instructor app — kept exactly as it was
function InstructorApp({assignments, setAssignments, instructorId, classes, interviews, setInterviews}) {

  return (
    <div className="Page">
      <Title />
      <Tallys assignments={assignments} interviews={interviews} />
      <Assignments
        assignments={assignments}
        setAssignments={setAssignments}
        interviews={interviews}
        setInterviews={setInterviews}
        instructorId={instructorId}
        instructorClasses={classes}
      />
    </div>
  );
}

function StudentApp({ user }) {
  return (
    <div className="Page">
      <StudentDash user={user} />
    </div>
  );
}

// Blocks access if user isn't logged in or is the wrong group
function ProtectedRoute({ children, requiredGroup, userGroup, loading }) {
  if (loading) return <div style={loadingStyle}>Loading...</div>;
  if (!userGroup) return <Navigate to="/" replace />;
  if (userGroup !== requiredGroup) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const [userGroup, setUserGroup] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [interviews, setInterviews] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [uniqueCognitoId, setUniqueCognitoId] = useState(null);
  const [classes, setClasses] = useState([]);

  useEffect(() => {
    checkSession();
  },  []);

  useEffect(() => {
    if (userGroup !== "Teachers") return;
    if (!user?.username) return;
    async function fetchAllInterviews() {
      
        try {
          const response = await axios.get(`/api/instructor/${parseInt(user.username)}/interviews`);
          console.log("interview object:", response.data);
          if (Array.isArray(response.data)) {
            const mappedInterviews = [];
        for (let i = 0; i < response.data.length; i++) {
            const interview = response.data[i];
            mappedInterviews.push({
                id: interview.id,
                name: interview.user?.username || interview.user?.email || "Unknown",
                email: interview.user?.email || "",
                time: interview.startTime,
                assignmentId: interview.assignmentId,
                status: interview.status,
                studentId: interview.user?.studentId,
                dueDate: interview.dueDate,
                studentSubmission: interview.studentSubmission,
            });
        }
        setInterviews(mappedInterviews);
    }
        } catch {

        }
    }
    fetchAllInterviews();
}, [userGroup, user]);

useEffect(() => {
      if (userGroup !== "Teachers") return;
      if (!user?.username) return; // to keep tally updated 
      async function fetchAllAssignments() {
        try {
          const response = await axios.get(`/api/instructor/${parseInt(user?.username)}/assignments`);
          const assignmentArray = response.data;
          if (Array.isArray(assignmentArray)) {
            setAssignments(assignmentArray);
          }
        } catch {
          // no assignments yet
        }
      }
      fetchAllAssignments();
    }, [userGroup, user]);

useEffect(() => {
    if (userGroup !== "Teachers") return;
    if (!user?.username) return;
    async function fetchInstructorClasses() {
        try {
            const response = await axios.get(`/api/instructor/${parseInt(user.username)}/classes`);
            if (Array.isArray(response.data)) {
                setClasses(response.data);
            }
        } catch {
            // no classes yet
        }
    }
    fetchInstructorClasses();
}, [userGroup, user]);

  async function checkSession() {
    try {
      const currentUser = await getCurrentUser();
      const session = await fetchAuthSession({ forceRefresh: true });
      const groups = session.tokens?.accessToken?.payload?.["cognito:groups"] || [];
      const emailVal = session.tokens?.idToken?.payload?.email || "";
      const username = currentUser.username;
      const studentId = parseInt(username);
      const uniqueCognitoId = session.tokens?.idToken?.payload?.sub || null; // need to double check this when backend can get instructors 

      setUniqueCognitoId(uniqueCognitoId);
      setUserGroup(groups[0] || null);
      setUser({ email: emailVal, username, group: groups[0], studentId });
if (groups[0] === "Teachers") {
    try {
        await axios.post('/api/instructor', {
            id: parseInt(username),
            name: emailVal
        });
    } catch {
    }
}

if (groups[0] === "Students") {
    try {
        // The Cognito login username is the student ID, so build a display name
        // from the given/family name attributes captured at signup. Fall back to
        // the ID only if neither is present.
        const idPayload = session.tokens?.idToken?.payload || {};
        const givenName = idPayload.given_name || "";
        const familyName = idPayload.family_name || "";
        const fullName = `${givenName} ${familyName}`.trim() || username;
        console.log("creating student record for:", parseInt(username), fullName, emailVal);
        await axios.post('/api/user', {
            studentId: parseInt(username),
            username: fullName,
            email: emailVal
        });
    } catch (err) {
        console.log("student create error:", err.response?.status, err.response?.data);
    }
}
    
    } catch {
      setUserGroup(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Login page - public */}
        <Route path="/" element={<Login onLoginSuccess={(group, userObject) => {
          setUserGroup(group);
          setUser(userObject);
        }} />} />

        {/* Instructor dashboard - Teachers only */}
        <Route
          path="/instructor-dashboard"
          element={
            <ProtectedRoute
              requiredGroup="Teachers"
              userGroup={userGroup}
              loading={loading}
            >
              <InstructorApp assignments={assignments} setAssignments={setAssignments} interviews={interviews} setInterviews={setInterviews} instructorId={parseInt(user?.username)} classes={classes}/>
            </ProtectedRoute>
          }
        />
        <Route
          path="/instructor/interviews"
          element={
            <ProtectedRoute
              requiredGroup="Teachers"
              userGroup={userGroup}
              loading={loading}
            >
              <div className="Page">
                <Title />
                <ScheduledView interviews={interviews} setInterviews={setInterviews} assignments={assignments}/>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/report/:id"
          element={
            <ProtectedRoute
              requiredGroup="Teachers"
              userGroup={userGroup}
              loading={loading}
            >
              <GradeBook />
            </ProtectedRoute>
          }
        />

        <Route
          path="/student-dashboard"
          element={
            <ProtectedRoute
              requiredGroup="Students"
              userGroup={userGroup}
              loading={loading}
            >
              <StudentApp user={user} />
            </ProtectedRoute>
          }
        />

        <Route
          path="/interview/:id/loading"
          element={
            <ProtectedRoute
              requiredGroup="Students"
              userGroup={userGroup}
              loading={loading}
            >
              <InterviewLoading />
            </ProtectedRoute>
          }
        />

         <Route
            path="/student/report/:id"
            element={
              <ProtectedRoute requiredGroup="Students" userGroup={userGroup} loading={loading}>
                <StuGradeBook />
              </ProtectedRoute>
            }
          />

        <Route
          path="/instructor/classes" // takes to class creation page
          element={
              <ProtectedRoute
                  requiredGroup="Teachers"
                  userGroup={userGroup}
                  loading={loading}
              >
                  <div className="Page">
                      <Title />
                      <ClassCreation
                          instructorId={parseInt(user?.username)}
                          instructorClasses={classes}
                          setInstructorClasses={setClasses}
                      />
                  </div>
              </ProtectedRoute>
          }
      />
      {/* Any unknown URL goes back to login */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

const loadingStyle = {
  minHeight: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontFamily: "monospace",
  color: "#888",
  backgroundColor: "#f7f6f3",
};
