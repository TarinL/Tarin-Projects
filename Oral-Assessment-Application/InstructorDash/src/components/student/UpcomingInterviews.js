import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "../../styles/StudentDash.css";

export default function UpcomingInterviews({ interviews, setInterviews, user }) {
  const navigate = useNavigate();

  const [assignmentNamesByAssignmentId, setAssignmentNamesByAssignmentId] = useState({});
  const [classNamesByAssignmentId, setClassNamesByAssignmentId] = useState({});
  const [gradeByInterviewId, setGradeByInterviewId] = useState({});

  useEffect(() => {
    if (!interviews.length) return;
    async function fetchAssignmentNames() {
      const assignmentNamesMap = {};
      const classNamesMap = {};
      for (let i = 0; i < interviews.length; i++) {
        const currentAssignmentId = interviews[i].assignmentId;
        if (currentAssignmentId && !assignmentNamesMap[currentAssignmentId]) {
          try {
            const assignmentDetailResponse = await axios.get(`/api/assignment/${currentAssignmentId}`);
            assignmentNamesMap[currentAssignmentId] = assignmentDetailResponse.data?.name || currentAssignmentId;
            const classId = assignmentDetailResponse.data?.classId;
            if (classId) {
              try {
                const classResponse = await axios.get(`/api/class/${classId}`);
                classNamesMap[currentAssignmentId] = classResponse.data?.name || "—";
              } catch {
                classNamesMap[currentAssignmentId] = "—";
              }
            }
          } catch {
            assignmentNamesMap[currentAssignmentId] = currentAssignmentId;
          }
        }
      }
      setAssignmentNamesByAssignmentId(assignmentNamesMap);
      setClassNamesByAssignmentId(classNamesMap);
    }
    fetchAssignmentNames();
  }, [interviews]);

  useEffect(() => {
    if (!interviews.length) return;
    async function fetchGrades() {
      const gradesMap = {};
      for (let i = 0; i < interviews.length; i++) {
        try {
          const resultResponse = await axios.get(`/api/result/${interviews[i].id}`);
          const gradeString = resultResponse.data?.grade || "";
          const totalMatch = gradeString.match(/TOTAL:\s*(\d+)\/(\d+)/);
          if (totalMatch) {
            gradesMap[interviews[i].id] = totalMatch[1] + "/" + totalMatch[2];
          } else {
            gradesMap[interviews[i].id] = "—";
          }
        } catch {
          gradesMap[interviews[i].id] = "—";
        }
      }
      setGradeByInterviewId(gradesMap);
    }
    fetchGrades();
  }, [interviews]);

  async function handleStartInterview(interviewId) {
    try {
      await axios.post(`/api/interview/${interviewId}/start`);
    } catch (err) {
      console.error("Start call failed:", err);
    }
    navigate(`/interview/${interviewId}/loading`);
  }

  // Status ordering: scheduled first, then completed, then failed.
  function statusRank(status) {
    const s = (status || "").toLowerCase();
    if (s === "scheduled") return 0;
    if (s === "completed" || s === "graded") return 1;
    if (s === "failed") return 2;
    return 3;
  }

  // Group interviews by class name, then within each class sort by status. Scheduled
  // rows come first with the nearest due dates at the top; completed and failed
  // follow (most recent first).
  const classGroups = [];
  if (Array.isArray(interviews)) {
    const groupsByClassName = {};
    for (const interview of interviews) {
      const className = classNamesByAssignmentId[interview.assignmentId] || "—";
      if (!groupsByClassName[className]) {
        groupsByClassName[className] = [];
        classGroups.push({ className, rows: groupsByClassName[className] });
      }
      groupsByClassName[className].push(interview);
    }
    classGroups.sort((a, b) => a.className.localeCompare(b.className));
    for (const group of classGroups) {
      group.rows.sort((a, b) => {
        const rankDiff = statusRank(a.status) - statusRank(b.status);
        if (rankDiff !== 0) return rankDiff;
        // Scheduled: soonest due date first; others: most recent first.
        const diff = new Date(a.dueDate) - new Date(b.dueDate);
        return statusRank(a.status) === 0 ? diff : -diff;
      });
    }
  }

  function renderRow(interview) {
    const interviewStatus = interview.status?.toLowerCase();
    const isDone = interviewStatus === "completed" || interviewStatus === "graded";
    const isScheduled = interviewStatus === "scheduled";
    return (
      <tr key={interview.id}>
        <td>{classNamesByAssignmentId[interview.assignmentId] || "—"}</td>
        <td>{assignmentNamesByAssignmentId[interview.assignmentId] || interview.assignmentId}</td>
        <td>{new Date(interview.dueDate).toLocaleString()}</td>
        <td>{interview.status}</td>
        <td>{Math.round((interview.duration || 0) / 60)} mins</td>
        <td>{isDone ? gradeByInterviewId[interview.id] || "—" : ""}</td>
        <td>
          {isDone ? (
            <button className="StuTableBtn" onClick={() => navigate(`/student/report/${interview.id}`)}>
              View
            </button>
          ) : isScheduled ? (
            <button className="StuTableBtn" onClick={() => handleStartInterview(interview.id)}>
              Start
            </button>
          ) : null}
        </td>
      </tr>
    );
  }

  return (
    <div className="InterviewsSection">
      <h1>My Interviews</h1>
      {interviews.length === 0 ? (
        <p>No interviews scheduled.</p>
      ) : (
        classGroups.map((group) => (
          <div className="InterviewsTable" key={group.className}>
            <h2>{group.className}</h2>
            <table>
              <colgroup>
                <col style={{ width: '13%' }} />
                <col style={{ width: '23%' }} />
                <col style={{ width: '19%' }} />
                <col style={{ width: '12%' }} />
                <col style={{ width: '9%' }} />
                <col style={{ width: '8%' }} />
                <col style={{ width: '11%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Class</th>
                  <th>Assignment</th>
                  <th>Due</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Grade</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {group.rows.map(renderRow)}
              </tbody>
            </table>
          </div>
        ))
      )}
    </div>
  );
}