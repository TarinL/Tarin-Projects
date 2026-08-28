import axios from "axios";
import React, { useRef, useState, useEffect } from "react";
import "../../styles/StudentDash.css"
import StuEmptyInt from "./StuEmptyInt.js"
import StuInterview from "./StuInterview"
import StuTitle from "./StuTitle"
import UpcomingInterviews from "./UpcomingInterviews"
export default function StudentDash({ user }) {
    const [assignments, setAssignments] = useState([]);
    const [interviews, setInterviews] = useState([]);

    useEffect(() => {
        if (!user?.studentId) return;
        axios.get(`/api/interview/studentid/${user.studentId}`)
            .then((res) => setInterviews(Array.isArray(res.data) ? res.data : []))
            .catch((err) => {
                console.error("Failed to fetch interviews:", err);
                setInterviews([]);
        });
    }   , [user]);
    
    return (
    
    <div className = "StudentDash">
        <StuTitle/>
        <UpcomingInterviews
            interviews={interviews}
            setInterviews={setInterviews}
            user={user}
            />
    </div>      


    )  
}
