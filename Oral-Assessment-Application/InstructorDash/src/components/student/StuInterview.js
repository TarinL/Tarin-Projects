import React, { useState } from "react";
import axios from "axios";

export default function StuInterview({assignment, interviews, setInterviews, onBack, user}) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [info, setInfo] = useState('');
  const [duration, setDuration] = useState(0);
  const [selectedDuration, setSelectedDuration] = useState(null);
  const [mode, setMode] = useState('preset');

  const durations = [
    "5m", "10m", "15m", "20m",
    "25m", "30m"
  ];


  async function handleCreateInterview() {
  if (!duration) return;

  try {
    const studentEmail = user?.email || "";
    const studentId = user?.studentId || 0;

    // The rubric is owned by the assignment; the interview inherits it.
    const zoomUrl = "https://zoom.us/j/your-room-link";

    const zoomResponse = await axios.post(
      "/api/zoom",
      {
        url: zoomUrl,
      }
    );

    const zoomId = parseInt(
      String(zoomResponse.data).match(/\d+/)?.[0]
    );

    const now = new Date().toISOString();

    const interviewData = {
      id: 0,
      studentId: studentId,
      zoomId: zoomId,
      transcript: "Pending",
      startTime: now,
      status: "ongoing",
      // The form collects minutes; the DB stores duration in SECONDS.
      duration: duration * 60,
      dueDate: now,
      additionalInfo: info || "",
      assignmentId: assignment.id,
    };

    const interviewResponse = await axios.post(
      "/api/interview",
      interviewData
    );

    console.log("INTERVIEW CREATED:", interviewResponse.data);

    window.location.href = zoomUrl;

  } catch (error) {
    console.error("FAILED TO START INTERVIEW:", error);
    console.log("ERROR STATUS:", error.response?.status);
    console.log("ERROR DATA:", error.response?.data);
    console.log("REQUEST DATA:", error.config?.data);
  }
}

  return (
    <div className="newInterview">
      <h1>Schedule an interview</h1>


      <label htmlFor="duration" >Duration</label>

      <input
        type = "range"
        min = {0}
        max = {30}
        step = {1}
        value = {duration}
        onChange={(e) => setDuration(Number(e.target.value))}
        />

      <div className="durationInc">
          {[0, 5, 10, 15, 20, 25, 30].map((d) => (
            <span key={d}>{d}m</span>
          ))}
      </div>
      

      <div className="instructions">
      <h1>Custom AI Instructions</h1>

      <label htmlFor="my-Input">Additional Instructions (Optional)</label>

      <input
        id="my-Input"
        placeholder="Enter specific instructions for the AI interviewer, e.g., 'Focus on the student's understanding of A B C topics'"
        type="info"
        value={info}
        onChange={(e) => setInfo(e.target.value)}
      />
      </div>

      <div className="createInt">
          <button className = "intbut" onClick={handleCreateInterview}>
            Begin Interview
          </button>
        </div>
    </div>
  );
}