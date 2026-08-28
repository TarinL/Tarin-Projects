import "../../styles/InstructorDash.css";
import React, { useState, useEffect } from "react";
import axios from "axios";

export default function Interview({
  assignment,
  interviews,
  setInterviews,
}) {

  const [studentId, setStudentId] = useState("");
  const [email, setEmail] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [info, setInfo] = useState("");
  const [duration, setDuration] = useState(0);
  const [selectedTime, setSelectedTime] = useState(null);
  const [mode, setMode] = useState("preset");
  const [status, setStatus] = useState("scheduled");
  const [classStudents, setClassStudents] = useState([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [studentSelectionMode, setStudentSelectionMode] = useState("all");

  console.log("assignment:", assignment);
  console.log("class students:", classStudents);
  console.log("assignment classId:", assignment?.classId);

  useEffect(() => { //fetching students when assignemnt loads for student checkboxes
      if (!assignment?.classId) return;
      async function fetchClassStudents() {
          try {
              const response = await axios.get(`/api/class/${assignment.classId}/students`);
              setClassStudents(response.data || []);
          } catch {
              console.error("Failed to fetch class students");
          }
      }
      fetchClassStudents();
  }, [assignment?.classId]);

  useEffect(() => {
    if (classStudents.length > 0) {
        setSelectedStudentIds(classStudents.map(s => s.studentId));
    }
}, [classStudents]); // timing fix for tarins error


  const times = [
    "08:00", "08:30", "09:00", "09:30",
    "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00", "17:30",
    "18:00", "18:30", "19:00", "19:30",
    "20:00", "20:30", "21:00", "21:30",
    "22:00", "22:30", "23:00", "23:30"
  ];

async function handleCreateInterview() {
  const selectedDueTime =
    mode === "preset" ? selectedTime : time;

    const startDateTime =
  new Date(`${date}T${selectedDueTime}:00`).toISOString();

  const studentsToSchedule = studentSelectionMode === "all" 
    ? classStudents.map(s => s.studentId) 
    : selectedStudentIds; // removes timing issues

if (!studentsToSchedule.length || !date || !selectedDueTime || !duration || duration < 1 || duration > 60) {
  alert("Please fill in all required fields. Duration must be between 1 and 60 minutes.");
  return;
}
for (let i = 0; i < studentsToSchedule.length; i++) {
    const currentStudentId = studentsToSchedule[i];
    try {

    // The rubric is owned by the assignment; the interview inherits it. No
    // per-interview rubric is created here any more.
    const zoomResponse = await axios.post(
      "/api/zoom",
      {
        url: "placeholder-link",
        meetingId: 14839
      }
    );

    console.log(
      "ZOOM RESPONSE:",
      zoomResponse.data.meetingId
    );

    const zoomId =
      zoomResponse.data.meetingId ||
      parseInt(
        String(zoomResponse.data)
          .match(/\d+/)?.[0]
      );

    const interviewData = {
      studentId: currentStudentId,
      zoomId: zoomId,
      transcript: "",
      startTime: startDateTime,
      status: "scheduled",
      // The form collects minutes (1–60); the DB stores duration in SECONDS.
      duration: duration * 60,
      dueDate: startDateTime,
      additionalInfo: info || "",
      assignmentId: assignment.id
    };

    console.log(
      "INTERVIEW DATA:",
      interviewData
    );

    const interviewResponse = await axios.post(
      "/api/interview",
      interviewData
    );

    console.log(
      "INTERVIEW CREATED:",
      interviewResponse.data
    );

// Resolve the actual student being scheduled (the loop iterates over IDs).
// The old code read unused empty `studentId`/`email` state, which left the
// row blank until a refresh reloaded it from the backend.
const studentRecord = classStudents.find(s => s.studentId === currentStudentId);

const newInterview = {
  id:
    interviewResponse.data.id ||
    parseInt(
      String(interviewResponse.data)
        .match(/\d+/)?.[0]
    ),

  studentId: currentStudentId,

  name: studentRecord?.username || studentRecord?.email || "Unknown",
  email: studentRecord?.email || "",
  time: startDateTime,
  assignmentName: assignment.name,
  assignmentId: assignment.id,
  status: "scheduled",
  dueDate: startDateTime,
  studentSubmission: "",

  zoomUrl:
    zoomResponse.data.url ||
    "https://zoom.us/j/your-room-link",
};

setInterviews((prev) => [...prev, newInterview]);

  } catch (error) {

    console.error(
      "Failed to schedule interview:",
      error
    );

    console.log(
      "ERROR STATUS:",
      error.response?.status
    );

    console.log(
  "VALIDATION ERRORS:",
  error.response?.data?.errors
);

    console.log(
      "ERROR HEADERS:",
      error.response?.headers
    );

    console.log(
      "REQUEST DATA:",
      error.config?.data
    );

    alert("Failed to schedule interview");
  }
}
alert("Interviews scheduled successfully!");

// Clear the form so the next interview starts blank.
setDate("");
setTime("");
setSelectedTime(null);
setDuration(0);
setInfo("");
setStudentSelectionMode("all");
setSelectedStudentIds(classStudents.map(s => s.studentId));
}

  return (
    <div className="newInterview">

      <h1>Schedule an interview</h1>

      <label>Select Students *</label>
<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' , textAlign: "left"}}>
          <input
              type="radio"
              name="studentSelection"
              value="all"
              style={{width:"auto"}}
              checked={studentSelectionMode === "all"}
              onChange={() => {
                  setStudentSelectionMode("all");
                  setSelectedStudentIds(classStudents.map(s => s.studentId));
              }}
          />
          <span>Select All</span>
      </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
    <input
        type="radio"
        name="studentSelection"
        value="specific"
        style={{width:"auto"}}
        checked={studentSelectionMode === "specific"}
        onChange={() => {
            setStudentSelectionMode("specific");
            setSelectedStudentIds([]);
        }}
    />
    <span>Select Specific Students</span>
</div>

<div style={{ marginBottom: '16px' , maxHeight: '200px', overflowY: 'auto', border: '1px solid var(--border)', padding: '8px', display: studentSelectionMode === 'specific' ? 'block' : 'none' }}>
              {classStudents.map(student => (
                <div key={student.studentId} className="toggle">
                  <input
                  type="checkbox"
                  style={{width:'auto'}}
                  checked={selectedStudentIds.includes(student.studentId)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedStudentIds(prev => [...prev, student.studentId]);
                    } else {
                      setSelectedStudentIds(prev => prev.filter(id => id !== student.studentId));
                    }
                  }}
              />
              <span>{student.username || student.email}</span>
        </div>
              ))}
      </div>
      </div>

      <label htmlFor="date">Due By Date *</label>

      <input
        id="date"
        type="date"
        value={date}
        onChange={(e) => setDate(e.target.value)}
      />

      <div className="timeBox">

        <div className="toggle">

          <button
            className={`presetB ${
              mode === "preset" ? "active" : ""
            }`}
            onClick={() => setMode("preset")}
          >
            Preset Time Due
          </button>

          <button
            className={`customB ${
              mode === "custom" ? "active" : ""
            }`}
            onClick={() => setMode("custom")}
          >
            Custom Time Due
          </button>

        </div>

        {mode === "preset" && (
          <div className="time-grid">

            {times.map((time) => (
              <button
                key={time}
                className={`time-btn ${
                  selectedTime === time
                    ? "selected"
                    : ""
                }`}
                onClick={() => setSelectedTime(time)}
              >
                {time}
              </button>
            ))}

          </div>
        )}

        {mode === "custom" && (
          <div className="custBox">

            <input
              type="time"
              value={time}
              onChange={(e) =>
                setTime(e.target.value)
              }
            />

          </div>
        )}
      </div>

      <label htmlFor="duration">Duration (mins) *</label>
        <input
          id="duration"
          type="number"
          min={1}
          max={60}
          placeholder="e.g. 15"
          value={duration || ""}
          onChange={(e) => setDuration(Number(e.target.value))}
        />

      <div className="instructions">

        <h1>Custom AI Instructions</h1>

        <label htmlFor="info">
          Additional Instructions
        </label>

        <input
          id="info"
          placeholder="Focus on understanding of Topic A"
          value={info}
          onChange={(e) => setInfo(e.target.value)}
        />

      </div>

      <div className="createInt">

        <button
          className="intbut"
          onClick={handleCreateInterview}
        >
          Schedule an Interview
        </button>

      </div>
    </div>
  );
}