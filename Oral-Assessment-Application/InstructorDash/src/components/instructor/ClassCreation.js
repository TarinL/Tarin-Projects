import "../../styles/InstructorDash.css";

import React, {useState, useEffect} from "react";
import axios from "axios";
import{useNavigate} from "react-router-dom";

export default function ClassManagement({instructorId, instructorClasses, setInstructorClasses}) {
    const navigate = useNavigate();
    const [newClassName, setNewClassName] = useState("");
    const [studentIdInputPerClass, setStudentIdInputPerClass] = useState({});
    const [enrolledStudentsPerClass, setEnrolledStudentsPerClass] = useState({});

    useEffect(() => {
        if (!instructorClasses.length) return;
        async function getEnrolledStudents() {
            const enrolledMap = {};
            for (let i = 0; i < instructorClasses.length; i++) {
                try {
                    const CurrentEnrolledStudents = await axios.get(`/api/class/${instructorClasses[i].id}/students`);
                    enrolledMap[instructorClasses[i].id] = CurrentEnrolledStudents.data;
                } catch {
                    enrolledMap[instructorClasses[i].id] = [];
                }
            }
            setEnrolledStudentsPerClass(enrolledMap);
        }
        getEnrolledStudents();
    }, [instructorClasses]);

    async function CreateClass() {
        if (!newClassName.trim()) {
            alert("Please enter a class name.");
            return;
        }
        try {
            const createClassResponse = await axios.post("/api/class", {
                name: newClassName,
                instructorId: instructorId
            });
            const newClassId = parseInt(String(createClassResponse.data).split(" ").pop());
            const newClass = {id: newClassId, name: newClassName, instructorId: instructorId};
            const updatedClasses = [];
            for (let i = 0; i < instructorClasses.length; i++) {
                updatedClasses.push(instructorClasses[i]);
            }
            updatedClasses.push(newClass);
            setInstructorClasses(updatedClasses);
            setNewClassName("");
        } catch (error) {
            console.error("Failed to create class: ", error);
            alert("Failed to create class.");
        }
    }

    async function AddStudentsToClass(classId) {
        const studentIdInputList = studentIdInputPerClass[classId];
        const studentIdsToAdd = [];
        const inputParts = studentIdInputList.split(/[\n,]/);
        for (let i = 0; i < inputParts.length; i++) {
            const parsedId = parseInt(inputParts[i].trim());
            if (!isNaN(parsedId)) {
                studentIdsToAdd.push(parsedId);
            }
        }
        if (!studentIdsToAdd.length) {
            alert("Please enter at least one student ID.");
            return;
        }
        try {
            const addNewStudents = await axios.post(`/api/class/${classId}/students`, {studentIds: studentIdsToAdd});
            const updatedStudentsfromDB = await axios.get(`/api/class/${classId}/students`);
            const updatedEnrolled = {};
            for (let i = 0; i < instructorClasses.length; i++) {
                if (instructorClasses[i].id === classId) {
                    updatedEnrolled[classId] = updatedStudentsfromDB.data;
                } else {
                    updatedEnrolled[instructorClasses[i].id] = enrolledStudentsPerClass[instructorClasses[i].id] || [];
                }
            }
            setEnrolledStudentsPerClass(updatedEnrolled);
            const clearedInputs = {};
            for (let i = 0; i < instructorClasses.length; i++) {
                if (instructorClasses[i].id === classId) {
                    clearedInputs[classId] = "";
                } else {
                    clearedInputs[instructorClasses[i].id] = studentIdInputPerClass[instructorClasses[i].id] || "";
                }
            }
            setStudentIdInputPerClass(clearedInputs);
            if (addNewStudents.data?.skipped?.length) {
                alert(`Added. Not found: ${addNewStudents.data.skipped.join(", ")}`);
            } else {
                alert("Students added.");
            }
        } catch (error) {
            console.error("Failed to add students:", error);
            alert("Failed to add students.");
        }
    }

    return (
        <div className="Page">

            <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '22px', fontWeight: 'normal', color: 'var(--hero)', marginBottom: '24px' }}>Class Management</h2>

            {/* create class form */}
            <div className="AssCreation" style={{ marginBottom: '24px' }}>
                <h3>Create New Class</h3>
                <input
                    type="text"
                    placeholder="Class name"
                    value={newClassName}
                    onChange={e => setNewClassName(e.target.value)}
                />
                <button onClick={CreateClass} className="assbut">Create Class</button>
            </div>

            {/* list of existing classes */}
            <div className="AssCreation">
                <h3>Your Classes</h3>
                {instructorClasses.length === 0 ? (
                    <p style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--text-muted)' }}>No classes yet.</p>
                ) : (
                    instructorClasses.map(cls => (
                        <div key={cls.id} className="class-item">

                            {/* class name header */}
                            <div className="class-item-header">
                                <span className="class-item-name">{cls.name}</span>
                                <span className="class-item-count">
                                    {enrolledStudentsPerClass[cls.id]?.length || 0} student{enrolledStudentsPerClass[cls.id]?.length !== 1 ? "s" : ""}
                                </span>
                            </div>

                            {/* enrolled students table */}
                            <div className="class-item-body">
                                {enrolledStudentsPerClass[cls.id]?.length ? (
                                    <table className="class-students-table">
                                        <thead>
                                            <tr>
                                                <th>Student ID</th>
                                                <th>Email</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {enrolledStudentsPerClass[cls.id].map(student => (
                                                <tr key={student.studentId}>
                                                    <td>{student.studentId}</td>
                                                    <td>{student.email}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : (
                                    <p style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 16px 0' }}>No students enrolled yet.</p>
                                )}

                                {/* add students */}
                                <div className="class-add-students">
                                    <p style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-muted)', margin: '0 0 6px 0' }}>
                                        Add students (comma or newline separated IDs):
                                    </p>
                                    <textarea
                                        className="class-textarea"
                                        placeholder="e.g. 123456789, 987654321"
                                        value={studentIdInputPerClass[cls.id] || ""}
                                        onChange={e => {
                                            const updatedInputs = {};
                                            updatedInputs[cls.id] = e.target.value;
                                            for (let i = 0; i < instructorClasses.length; i++) {
                                                if (instructorClasses[i].id !== cls.id) {
                                                    updatedInputs[instructorClasses[i].id] = studentIdInputPerClass[instructorClasses[i].id] || "";
                                                }
                                            }
                                            setStudentIdInputPerClass(updatedInputs);
                                        }}
                                    />
                                    <button onClick={() => AddStudentsToClass(cls.id)} className="assbut" style={{ width: 'auto', marginTop: '8px' }}>
                                        Add Students
                                    </button>
                                </div>
                            </div>

                        </div>
                    ))
                )}
            </div>
        </div>
    );
}