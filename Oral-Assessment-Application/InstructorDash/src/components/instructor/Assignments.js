import axios from "axios";
import React, { useRef, useState, useEffect } from "react";
import "../../styles/InstructorDash.css";
import EmptyInt from "./EmptyInt"
import Interview from "./Interview"


export default function FileUploader({
 assignments,
 setAssignments,
 interviews,
 setInterviews,
 instructorId,
 instructorClasses,
}) {
 const [briefs, setBriefs] = useState([]);
 const [rubrics, setRubrics] = useState([]);
 const [students, setStudent] = useState([]);
 const [files, setFiles] = useState([]);
 const [text, setText] = useState('');
 const [selectedAssignment, setSelectedAssignment] = useState(null);
 const [selectedClassIdForNewAssignment, setSelectedClassIdForNewAssignment] = useState(null);
 const [questions, setQuestions] = useState([]);
 const [knowledgeBase, setKnowledgeBase] = useState([]);
 // Interview mode, chosen explicitly by the instructor. Internal strings are kept
 // stable for the bot/DB; the UI shows friendly labels (see the Mode <select>).
 //   manual         → Standard          (brief + rubric + questions)
 //   knowledge_base → Knowledge Review  (brief + knowledge base)
 //   submission     → Assignment Review (brief + rubric + questions; submission added later)
 const [mode, setMode] = useState("manual");
 // Number of lines of questioning to generate from the knowledge base (Knowledge
 // Review mode only). Defaults to 5.
 const [numQuestions, setNumQuestions] = useState(5);
 // Disables the Create button and shows progress while the (slow, LLM-backed)
 // rubric/question parse + save round-trip is in flight, so the instructor
 // doesn't click repeatedly thinking nothing happened.
 const [creating, setCreating] = useState(false);
const API_BASE = "";

 const briefInputRef = useRef(null);
 const briefRubricRef = useRef(null);
 const briefStudentRef = useRef(null);
 const briefFileRef = useRef(null);
 const questionsRef = useRef(null);
 const knowledgeBaseRef = useRef(null);
 const [currentStudentId, setCurrentStudentId] =
  useState("1234");


 useEffect(() => {
     if (assignments.length === 0) {
       setSelectedAssignment(null);
     }
   }, [assignments]);
 
   async function handleCreateAssignment() {
    // manual (Standard) and submission (Assignment Review) collect the same fields;
    // knowledge_base (Knowledge Review) uses a knowledge base instead of rubric/questions.
    const usesRubric = mode === "manual" || mode === "submission";

    if (!selectedClassIdForNewAssignment) {
    alert("Please select a class.");
    return;
  }

  if (!text.trim()) {
    alert("Please enter an assignment name.");
    return;
  }

  if (!briefs[0]?.contents) {
    alert("Please upload an assignment brief.");
    return;
  }

  if (usesRubric) {
    if (!rubrics[0]?.contents) {
      alert("Please upload a rubric.");
      return;
    }
    if (!questions[0]?.contents) {
      alert("Please upload the weighted areas of focus / questions.");
      return;
    }
  } else {
    if (!knowledgeBase[0]?.contents) {
      alert("Please upload a knowledge base.");
      return;
    }
  }

  // Build contents from only the fields that apply to the selected mode.
  const contents = usesRubric
    ? `BRIEF:\n${briefs[0]?.contents || ""}

RUBRIC:\n${rubrics[0]?.contents || ""}`
    : `BRIEF:\n${briefs[0]?.contents || ""}`;

  const localAssignment = {
    id: crypto.randomUUID(),
    name: text,
    contents,
    mode,
  };

  setCreating(true);
  try {

    // Rubric/questions only apply to the rubric modes (Standard / Assignment Review).
    // Knowledge Review stores a knowledge base instead and owns no rubric.
    let rubricId = null;
    let questionsJson = "";
    const knowledgeBaseText = usesRubric ? "" : (knowledgeBase[0]?.contents || "");

    if (usesRubric) {
      // Reformat the uploaded rubric text into the structured JSON the bot/marker
      // expect. The parse endpoint accepts any format (LLM-backed, never fails).
      const parsedRubric = await axios.post(
        "/api/parse/rubric",
        { text: rubrics[0]?.contents || "" }
      );
      // axios auto-parses the JSON body into a JS object/array even though the
      // endpoint sends it as text/plain. Re-serialise (don't String() it, which
      // would yield "[object Object]") so the DB stores valid JSON.
      const rubricContents =
        typeof parsedRubric.data === "string"
          ? parsedRubric.data
          : JSON.stringify(parsedRubric.data);

      // Reformat the questions/areas-of-focus upload into the [{text, weight}] JSON shape.
      const parsedQuestions = await axios.post(
        "/api/parse/questions",
        { text: questions[0].contents }
      );
      questionsJson =
        typeof parsedQuestions.data === "string"
          ? parsedQuestions.data
          : JSON.stringify(parsedQuestions.data);

      // The assignment owns its rubric. Create the structured rubric record and
      // attach it to the assignment.
      const rubricResponse = await axios.post(
        "/api/rubric",
        { rubricContents: rubricContents }
      );
      rubricId = parseInt(
        String(rubricResponse.data).match(/\d+/)?.[0]
      );
    } else {
      // Knowledge Review: derive the rubric + lines of questioning from the
      // knowledge base so the bot has criteria to question against and the marker
      // has a rubric to grade with. The endpoint returns both as DB-shaped JSON
      // strings; we persist the rubric as its own record and store the questions
      // on the assignment.
      // Clamp to a sane range; the backend also requires at least 1.
      const requestedQuestions = Math.min(20, Math.max(1, parseInt(numQuestions, 10) || 5));
      const generated = await axios.post(
        "/api/assignment/generate-assessment",
        { knowledgeBase: knowledgeBaseText, numQuestions: requestedQuestions }
      );

      const generatedRubric =
        typeof generated.data?.rubric === "string"
          ? generated.data.rubric
          : JSON.stringify(generated.data?.rubric ?? {});
      questionsJson =
        typeof generated.data?.questions === "string"
          ? generated.data.questions
          : JSON.stringify(generated.data?.questions ?? []);

      const rubricResponse = await axios.post(
        "/api/rubric",
        { rubricContents: generatedRubric }
      );
      rubricId = parseInt(
        String(rubricResponse.data).match(/\d+/)?.[0]
      );
    }

    const response = await axios.post(
      "/api/assignment",
      {
        name: text,
        contents: contents,
        classId: selectedClassIdForNewAssignment,
        mode: mode,
        questions: questionsJson,
        knowledgeBase: knowledgeBaseText,
        rubricId: rubricId,
      }
    );
    console.log("SENT TO BACKEND:", {
        name: text,
        contents: contents,
      });

    console.log("BACKEND RESPONSE:", response.data);

    console.log("API RESPONSE:", response.data);

    const backendAssignmentId = parseInt(
  response.data.match(/\d+/)[0]
);
const savedAssignment = {
  id: backendAssignmentId,
  name: response.data.name || response.data.Name || text,
  contents,
  mode,
  // Must be `classId` (matches the backend Assignment shape) so the interview
  // scheduler's student fetch (Interview.js reads assignment.classId) works
  // immediately, without a refresh.
  classId: selectedClassIdForNewAssignment,
};

console.log("SAVED ASSIGNMENT:", savedAssignment);

    setAssignments((prev) => [...prev, savedAssignment]);
    alert("Assignment created successfully!");

  } catch (error) {
    console.log("ERROR RESPONSE:", error.response?.data);
    console.log("STATUS:", error.response?.status);
    console.log("MESSAGE:", error.message);

    setAssignments((prev) => [...prev, { ...localAssignment, classId: selectedClassIdForNewAssignment }]);
    alert("Could not reach the server — the assignment was added locally only.");
  } finally {
    setCreating(false);
  }

  setText("");
  setStudent([]);
  setBriefs([]);
  setRubrics([]);
  setFiles([]);
  setQuestions([]);
  setKnowledgeBase([]);
  // Reset the dropdowns too so the form is fully cleared for the next assignment.
  setSelectedClassIdForNewAssignment(null);
  setMode("manual");
  setNumQuestions(5);
}


 async function handleRemoveAssignment(id) {
   if (!window.confirm("Delete this assignment? This also removes its scheduled interviews and cannot be undone.")) {
     return;
   }

   // Persist the deletion. Locally-created assignments (server unreachable) have a
   // UUID string id and were never saved, so only call the API for numeric ids.
   if (typeof id === "number") {
     try {
       await axios.delete(`/api/assignment/${id}`);
     } catch {
       alert("Failed to delete the assignment on the server.");
       return;
     }
   }

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


 function handleSelectAssignment(assignment) {
   setSelectedAssignment(assignment);
 }


 function FileRow({ item, onClick, onRemove, removable = false }) {
   return (
     <div className="fileR" onClick={onClick}>
       <div className="fileRl">
         <p className="fileRn" style={{ backgroundColor: "#d4edda", color: "#155724", padding: "6px 10px", borderRadius: "4px", textAlign: "center" }}>File uploaded successfully.<br/><strong>{item.name}</strong></p>
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

  const file = selectedFiles[0];

  const reader = new FileReader();

  reader.onload = () => {
    const fileContents = reader.result;

    const newFile = {
      name: file.name,
      contents: fileContents
    };

    if (type === "brief") {
      setBriefs([newFile]);
    } else if (type === "rubric") {
      setRubrics([newFile]);
    } else if (type === "student") {
      setStudent([newFile]);
    } else if (type == "questions") {
      setQuestions([newFile]);
    } else if (type == "knowledgeBase") {
      setKnowledgeBase([newFile]);
    }
  };

  reader.readAsText(file);

  e.target.value = "";
}


 return (
   <div className="CA">
   <div className="AssignmentSection">
     <div className="AssCreation">
       <h1>Create New Assignment</h1>
      <label>Class</label>
      <select
        style={{ marginBottom: '16px' }}
          value={selectedClassIdForNewAssignment || ""}
          onChange={e => setSelectedClassIdForNewAssignment(parseInt(e.target.value))}
      >
          <option value="">Select a class</option>
          {(instructorClasses || []).map(cls => (
              <option key={cls.id} value={cls.id}>{cls.name}</option>
          ))}
      </select>

       <label htmlFor="my-Input">Enter Assignment Name (required)</label>


       <input
         id="my-Input"
         type="text"
         value={text}
         onChange={(e) => setText(e.target.value)}
       />
       <label>Mode</label>
       <select
         style={{ marginBottom: '16px' }}
         value={mode}
         onChange={(e) => {
           // Clear uploads that don't apply to the new mode so a stale file isn't sent.
           setMode(e.target.value);
           setRubrics([]);
           setQuestions([]);
           setKnowledgeBase([]);
           setNumQuestions(5);
         }}
       >
         <option value="manual">Standard</option>
         <option value="knowledge_base">Knowledge Review</option>
         <option value="submission">Assignment Review</option>
       </select>
       <label style={{ marginBottom: '16px' }}>Please give the file picker a second to open. It may be delayed.</label>
       <label>Assignment Brief (required)</label>
       <div className="Uploadbox">
        


         <input
           ref={briefInputRef}
           type="file"
           accept=".txt"
           onChange={(e) => handleFileChange(e, "brief")}
           style={{ display: "none" }}
         />


         {briefs.length === 0 ? (
           <div className="text">
             <button onClick={() => handleIconClick(briefInputRef)}>
               <img className = "UploadI" src="/Upload.png" width="20" height="20" alt="Upload" />
             </button>
             <p>Click to upload assignment brief. Please upload a .txt file.</p>
           </div>
         ) : (
           <FileRow
             item={briefs[0]}
             onClick={() => handleIconClick(briefInputRef)}
           />
         )}
       </div>


       {(mode === "manual" || mode === "submission") && (
       <>
       <label>Rubric (required)</label>
       <div className="Uploadbox">



         <input
           ref={briefRubricRef}
           type="file"
           accept=".txt"
           onChange={(e) => handleFileChange(e, "rubric")}
           style={{ display: "none" }}
         />


         {rubrics.length === 0 ? (
           <div className="text">
             <button onClick={() => handleIconClick(briefRubricRef)}>
               <img className = "UploadI" src="/Upload.png" width="30" height="20" alt="Upload" />
             </button>
             <p>Click to upload assignment rubric. Please upload a .txt file.</p>
           </div>
         ) : (
           <FileRow
             item={rubrics[0]}
             onClick={() => handleIconClick(briefRubricRef)}
           />
         )}
       </div>
       </>
       )}

         {/* commenting out for demo purposes 
       <label>Student Assignment (optional)</label>
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
               <img className = "UploadI" src="/Upload.png" width="30" height="20" alt="Upload" />
             </button>
             <p>Click to upload student assignment. Please upload a .txt file.</p>
           </div>
         ) : (
           <FileRow
             item={students[0]}
             onClick={() => handleIconClick(briefStudentRef)}
           />
         )}
      </div>
      */}


      {(mode === "manual" || mode === "submission") && (
      <>
      <label>Weighted Areas of Focus/Global Questions (required)</label>
       <div className="Uploadbox">
        {/* for global questions */}
         <input
           ref={questionsRef}
           type="file"
           accept=".txt"
           onChange={(e) => handleFileChange(e, "questions")}
           style={{ display: "none" }}
         />


         {questions.length === 0 ? (
           <div className="text">
             <button onClick={() => handleIconClick(questionsRef)}>
               <img className = "UploadI" src="/Upload.png" width="30" height="20" alt="Upload" />
             </button>
             <p>Click to upload questions. Please upload a .txt file.</p>
           </div>
         ) : (
           <FileRow
             item={questions[0]}
             onClick={() => handleIconClick(questionsRef)}
           />
         )}
        </div>
        </>
        )}

        {mode === "knowledge_base" && (
        <>
        <label>Knowledge Base (required)</label>
       <div className="Uploadbox">
        {/* for knowledge base */}
         <input
           ref={knowledgeBaseRef}
           type="file"
           accept=".txt"
           onChange={(e) => handleFileChange(e, "knowledgeBase")}
           style={{ display: "none" }}
         />


         {knowledgeBase.length === 0 ? (
           <div className="text">
             <button onClick={() => handleIconClick(knowledgeBaseRef)}>
               <img className = "UploadI" src="/Upload.png" width="30" height="20" alt="Upload" />
             </button>
             <p>Click to upload knowledge base. Please upload a .txt file.</p>
           </div>
         ) : (
           <FileRow
             item={knowledgeBase[0]}
             onClick={() => handleIconClick(knowledgeBaseRef)}
           />
         )}
       </div>
       <label htmlFor="num-questions">Number of questions to generate</label>
       <input
         id="num-questions"
         type="number"
         min="1"
         max="20"
         style={{ marginBottom: '16px' }}
         value={numQuestions}
         onChange={(e) => setNumQuestions(e.target.value)}
       />
       </>
       )}




       <div className="create">
         <button className ="assbut" onClick={handleCreateAssignment} disabled={creating}>
           {creating ? "Creating…" : "Create Assignment"}
         </button>
       </div>
     </div>


     <div className="assignments-box">
       <div className = "label">
       <label>Assignments</label>
       </div>
       <div className="assignments-list">
         {assignments.map((assignment) => (
           <div key={assignment.id} className="assignment-item" onClick={() => handleSelectAssignment(assignment)}>
             <img src="/Assignmentimg.svg" width="30" height="30" alt="" className ="AssignmentIcon"/>
             <p className="assignment-name">{assignment.name}</p>
             <button
              className="BinIcon"
              onClick={(e) => {
                e.stopPropagation();
                handleRemoveAssignment(assignment.id);
              }}
            >
              <img src="/Trash.png" width="20" height="20" alt="Delete" />
            </button>
           </div>
         ))}
       </div>
     </div>
   </div>
   {selectedAssignment ? (
       <Interview
         assignment={selectedAssignment}
         interviews={interviews}
         setInterviews={setInterviews}
         onBack={() => setSelectedAssignment(null)}
       />
     ) : (
       <EmptyInt />
     )}
     </div>
 );
}
