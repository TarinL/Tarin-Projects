import axios from "axios";
import React, { useRef, useState, useEffect } from "react";
import "../../styles/StudentDash.css";
import StuEmptyInt from "./StuEmptyInt"
import StuInterview from "./StuInterview"
import InterviewLoading from "./InterviewLoading";
import { useNavigate } from "react-router-dom";


export default function FileUploader({
 assignments,
 setAssignments,
 interviews,
 setInterviews,
 user,
}) {
 const [briefs, setBriefs] = useState([]);
 const [rubrics, setRubrics] = useState([]);
 const [students, setStudent] = useState([]);
 const [files, setFiles] = useState([]);
 const [text, setText] = useState('');
 const [selectedAssignment, setSelectedAssignment] = useState(null);
 const [startingInterview, setStartingInterview] = useState(null);
 const navigate = useNavigate();


 const briefInputRef = useRef(null);
 const briefRubricRef = useRef(null);
 const briefStudentRef = useRef(null);
 const briefFileRef = useRef(null);


 useEffect(() => {
     if (assignments.length === 0) {
       setSelectedAssignment(null);
     }
   }, [assignments]);

   useEffect(() => {
    if (!user?.studentId) return;
    axios.get(`/api/interview/studentid/${user.studentId}`)
      .then((res) => setInterviews(res.data))
      .catch((err) => console.error("Failed to fetch interviews:", err));
  }, [user]);

 function handleRemoveAssignment(id) {
   setAssignments((prev) => prev.filter((assignment) => assignment.id !== id));


   setInterviews((prev)=>
   prev.filter((interview) => interview.assignmentId !== id)
   );


   if (selectedAssignment && selectedAssignment.id ===id) {
     setSelectedAssignment(null);
   }
 }


 function handleIconClick(ref) {
   ref.current?.click();
 }


 async function handleSelectAssignment() {
  if (!text.trim()) {
    alert("Please enter an assignment name.");
    return;
  }

  const contents = `BRIEF:
${briefs[0]?.contents || briefs[0]?.name || ""}

RUBRIC:
${rubrics[0]?.contents || rubrics[0]?.name || ""}

STUDENT:
${students[0]?.contents || students[0]?.name || ""}`;

  try {
    const response = await axios.post(
      "/api/assignment",
      {
        name: text,
        contents: contents,
      }
    );

    const assignmentId = parseInt(
      String(response.data).match(/\d+/)?.[0]
    );

    const newAssignment = {
      id: assignmentId,
      name: text,
      contents: contents,
    };

    setAssignments((prev) => [...prev, newAssignment]);
    setSelectedAssignment(newAssignment);

    setText("");
    setStudent([]);
    setBriefs([]);
    setRubrics([]);
    setFiles([]);

  } catch (error) {
    console.error("FAILED TO CREATE ASSIGNMENT:", error);
    console.log("ERROR DATA:", error.response?.data);
  }
}


 function FileRow({ item, onClick, onRemove, removable = false }) {
   return (
     <div className="fileR" onClick={onClick}>
       <div className="fileRl">
         <p className="fileRn" style={{ backgroundColor: "#d4edda", color: "#155724", padding: "6px 10px", borderRadius: "4px", textAlign: "center" }}>
          File uploaded successfully<br/><strong>{item.name}</strong>
          </p>
       </div>


       {removable && (
         <button
           type="button"
           className="fileRr"
           onClick={(e) => {
             e.stopPropagation();
             onRemove();
           }}
         >
           ×
         </button>
       )}
     </div>
   );
 }




 async function handleFileChange(e, type) {
   const selectedFiles = Array.from(e.target.files || []);
   if (selectedFiles.length === 0) return;


   for (const file of selectedFiles) {
     const formData = new FormData();
     formData.append("file", file);


     try {
       await axios.post("https://httpbin.org/post", formData);


       const newFile = {
         id: crypto.randomUUID(),
         name: file.name,
         file,
       };


       if (type === "brief") {
         setBriefs((prev) => [newFile]);
       } else if (type === "rubric") {
         setRubrics((prev) => [newFile]);
       } else if (type === "student") {
         setStudent([newFile]);
       } else if (type === "file") {
         setFiles((prev) => [...prev, newFile]);
       }
     } catch {
       return;
     }
   }


   e.target.value = "";
 }


 return (
  <div className="StuPage">

    <div className="StuCA">

      <div className="AssignmentSec">
        <div className="AssCreation">
          <h1>Create New Assignment</h1>

          <label htmlFor="my-Input">Enter Assignment Name</label>

          <input
            id="my-Input"
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />

          <label>Assignment Brief</label>

          <div className="Uploadbox">

            <input
              ref={briefInputRef}
              type="file"
              onChange={(e) => handleFileChange(e, "brief")}
              style={{ display: "none" }}
            />

            {briefs.length === 0 ? (
              <div className="text">
                <button onClick={() => handleIconClick(briefInputRef)}>
                  <img className="UploadI" src="/Upload.png" width="24" height="24" alt="Upload" />
                </button>

                <p>Click to upload assignment brief</p>
              </div>
            ) : (
              <FileRow
                item={briefs[0]}
                onClick={() => handleIconClick(briefInputRef)}
              />
            )}
          </div>

          <label>Rubric</label>

          <div className="Uploadbox">

            <input
              ref={briefRubricRef}
              type="file"
              onChange={(e) => handleFileChange(e, "rubric")}
              style={{ display: "none" }}
            />

            {rubrics.length === 0 ? (
              <div className="text">
                <button onClick={() => handleIconClick(briefRubricRef)}>
                  <img className="UploadI" src="/Upload.png" width="24" height="24" alt="Upload" />
                </button>

                <p>Click to upload assignment rubric</p>
              </div>
            ) : (
              <FileRow
                item={rubrics[0]}
                onClick={() => handleIconClick(briefRubricRef)}
              />
            )}
          </div>

          <label>Assignment</label>

          <div className="Uploadbox">

            <input
              ref={briefStudentRef}
              type="file"
              onChange={(e) => handleFileChange(e, "student")}
              style={{ display: "none" }}
            />

            {students.length === 0 ? (
              <div className="text">
                <button onClick={() => handleIconClick(briefStudentRef)}>
                  <img className="UploadI" src="/Upload.png" width="24" height="24" alt="Upload" />
                </button>

                <p>Click to upload assignment</p>
              </div>
            ) : (
              <FileRow
                item={students[0]}
                onClick={() => handleIconClick(briefStudentRef)}
              />
            )}
          </div>


          <div className="create">
            <button
              className="assbut"
              onClick={handleSelectAssignment}
            >
              Set Up Interview
            </button>
          </div>

        </div>

        {selectedAssignment ? (
          <StuInterview
            assignment={selectedAssignment}
            interviews={interviews}
            setInterviews={setInterviews}
            onBack={() => setSelectedAssignment(null)}
            user={user}
          />
        ) : (
          <StuEmptyInt />
        )}

      </div>

    </div>
      {startingInterview && (
        <InterviewLoading
          interview={startingInterview}
          onBack={() => setStartingInterview(null)}
        />
      )}
    <div className="StudentBottomBox">
        <h1>Upcoming Interviews</h1>
        {interviews.length === 0 ? (
          <p>Currently no interviews scheduled</p>
        ) : (
          interviews.map((interview) => (
            <div key={interview.id} className="interviewCard">
              <p><strong>Assignment:</strong> {interview.assignmentId}</p>
              <p><strong>Due:</strong> {new Date(interview.dueDate).toLocaleString()}</p>
              <p><strong>Status:</strong> {interview.status}</p>
              <p><strong>Duration:</strong> {interview.duration} mins</p>
              <button
                className="joinBtn"
                onClick={async () => {
                  try {
                    await axios.post(`/api/interview/${interview.id}/start`);
                  } catch (err) {
                    console.error("Start call failed:", err);
                  }
                  navigate(`/interview/${interview.id}/loading`);
                }}
              >
                Start Interview
              </button>
            </div>
          ))
        )}
      </div>

    </div>
  );
}