import React, { useState, useEffect } from 'react';
import axios from "axios";
import GradeTitle from "./GradeTitle";
import { useLocation, useParams, useNavigate } from 'react-router-dom';

import "../../styles/GradeBook.css"

export default function GradeBook({ readOnly = false }) {
    const { id } = useParams();
    const navigate = useNavigate();

    const location = useLocation();
    const clickedInterview = location.state?.interview;

    const [interviewData, setInterviewData] = useState(null);
    const [resultData, setResultData] = useState(null);

    const [transcript, setTranscript] = useState("");
    const [feedback, setFeedback] = useState("");
    const [gradingLogs, setGradingLogs] = useState([]);

    const [isEditing, setIsEditing] = useState(false);

    const [grade, setGrade] = useState("");
    const [letter, setLetter] = useState("");

    useEffect(() => {
        async function fetchGradeBookData() {
            try {
                const interviewResponse = await axios.get(
                    `/api/interview/${id}`
                );

                console.log("INTERVIEW RESPONSE:", interviewResponse.data);

                const interview = interviewResponse.data;
                setInterviewData(interview);

                // Transcript is the source of truth on the interview record, so it
                // shows even for a completed-but-not-yet-marked interview (whose
                // result fetch below would 404).
                setTranscript(interview.transcript || "");

                console.log("fetching result for id:", id); // testing
                const resultResponse = await axios.get(
                    `/api/result/${id}`
                );
                console.log("result response:", resultResponse.data); // testing

                console.log("RESULT RESPONSE:", resultResponse.data);

                const result = resultResponse.data;
                setResultData(result);

                setFeedback(result.feedback || "");

                const gradeString = result.grade || "";

                const logs = gradeString
                    .split("|")
                    .map((item) => item.trim())
                    .filter((item) => item.length > 0);

                setGradingLogs(logs);

                const totalMatch = gradeString.match(/TOTAL:\s*(\d+)\/(\d+)/);

                if (totalMatch) {
                    const achieved = Number(totalMatch[1]);
                    const possible = Number(totalMatch[2]);

                    const percentage = Math.round((achieved / possible) * 100);

                    setGrade(percentage);

                    let letterGrade = "";

                    if (percentage >= 90) {
                        letterGrade = "A+";
                    } else if (percentage >= 85) {
                        letterGrade = "A";
                    } else if (percentage >= 80) {
                        letterGrade = "A-";
                    } else if (percentage >= 75) {
                        letterGrade = "B+";
                    } else if (percentage >= 70) {
                        letterGrade = "B";
                    } else if (percentage >= 65) {
                        letterGrade = "B-";
                    } else if (percentage >= 60) {
                        letterGrade = "C+";
                    } else if (percentage >= 55) {
                        letterGrade = "C";
                    } else if (percentage >= 50) {
                        letterGrade = "C-";
                    } else {
                        letterGrade = "Fail";
                    }

                    setLetter(letterGrade);
                }

            } catch (error) {
                console.error("FAILED TO FETCH GRADEBOOK DATA:", error);

                console.log("ERROR STATUS:", error.response?.status);
                console.log("ERROR DATA:", error.response?.data);
                console.log("REQUEST URL:", error.config?.url);
            }
        }

        fetchGradeBookData();
    }, [id]);

    return (
        <div className="GradeBook">
            <button className="BackButton" onClick={() => navigate(-1)}>
            ← Back
            </button>
            <GradeTitle
                studentName={
                    clickedInterview?.name ||
                    interviewData?.user?.username ||
                    interviewData?.user?.email ||
                    "Unknown Student"
                }

                assignmentName={
                    clickedInterview?.assignmentName ||
                    interviewData?.assignment?.name ||
                    "Unknown Assignment"
                }

                interviewDate={
                    (clickedInterview?.startTime || interviewData?.startTime)
                        ? new Date(clickedInterview?.startTime || interviewData?.startTime).toLocaleString()
                        : "Unknown Date"
                }

                grade={grade}
                letter={letter}
                readOnly = {readOnly}
                isEditing={isEditing}
                setLetter={setLetter}
                setGrade={setGrade}
                setIsEditing={setIsEditing}
            />

            <div className="GradeContentRow">
                <div className="Transcript">
                    <h1>Interview Transcript</h1>
                    <p>{transcript}</p>
                </div>

                <div className="GradingLogs">
                    <h1>Grading Logs</h1>

                    {gradingLogs.map((log, index) => (
                        <p key={index}>{log}</p>
                    ))}
                </div>
            </div>

            <div className="FinalFeed">
                <h1>Final Feedback</h1>
                <p>{feedback}</p>
            </div>
        </div>
    );
}