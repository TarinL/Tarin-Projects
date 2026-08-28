// spacing all multiples of 8 derived from https://m3.material.io/styles/spacing/tokens
// font and typography sizing derived from https://m3.material.io/styles/typography/type-scale-tokens
// checked text contrast using: https://webaim.org/resources/contrastchecker/

// FONT SIZES ARE ARBITRARY, NEED TO FIX

import React, {useState, useEffect} from 'react';
import axios from 'axios';
import {useNavigate} from 'react-router-dom';

// Friendly labels for the internal interview mode strings stored on the assignment.
const MODE_LABELS = {
    manual: 'Standard',
    knowledge_base: 'Knowledge Review',
    submission: 'Assignment Review',
};

async function getGradeForInterview(interviewId) {
    try {
        const res = await axios.get(`/api/result/${interviewId}`);
        let APIgradeResult;
        if (res.data?.grade) {
            APIgradeResult = res.data.grade;
        } else {
            APIgradeResult = ""
        }
        const gradeOutOf100 = APIgradeResult.match(/TOTAL:\s*(\d+)\/(\d+)/); // unsure this is neccessary; check swagger
        if (gradeOutOf100) {
            return `${gradeOutOf100[1]}/${gradeOutOf100[2]}`;
        } else {
            return "-";
        }
    } catch {
        return "-";
    }
}

function AssignmentGroup({assignmentName, mode, interviews, grades, onRowClick, onDelete}) {
    // Track submissions uploaded this session so the cell can reflect "Uploaded ✓".
    const [uploaded, setUploaded] = useState({});

    async function handleSubmissionUpload(e, interviewId) {
        const file = e.target.files?.[0];
        e.target.value = "";
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async () => {
            try {
                await axios.patch(`/api/interview/${interviewId}/submission`, {
                    studentSubmission: reader.result,
                });
                setUploaded(prev => ({...prev, [interviewId]: true}));
            } catch {
                alert("Failed to upload submission.");
            }
        };
        reader.readAsText(file);
    }

    const rows = [];
    for (let i = 0; i < interviews.length; i++) {
        const interviewRow = interviews[i];
        const interviewGrade = grades[interviewRow.id]
        rows.push({...interviewRow, grade:interviewGrade})
    }

    return (
        // wrapper box for each assignment table 
        <div style={{border: '1px solid #bcd5e6', borderRadius: '8px', marginBottom:'16px', overflow: 'hidden'}}>
            {/* assignment name header bar */}
            <div style={{padding: '16px 24px', background:'#f8fafc', borderBottom: '1px solid #bcd5e6', fontFamily: 'Verdana, sans-serif', fontSize: '14px', color: '#264a64'  }}>
                <span>{assignmentName}</span>
            </div>
            {/* data table */}
            <table style={{width: '100%', borderCollapse: 'collapse', fontFamily: 'Verdana, sans-serif', fontSize: '14px', background: '#ffffff'}}> 
                {/* column titles */}
                <thead>
                    <tr style={{ background: '#f8fafc' }}>
                        <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', textTransform: 'uppercase', color: '#264a64', borderBottom: '1px solid #bcd5e6', width: '36px' }}></th>
                        <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', textTransform: 'uppercase', color: '#264a64', borderBottom: '1px solid #bcd5e6' }}>Student ID</th>
                        <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', textTransform: 'uppercase', color: '#264a64', borderBottom: '1px solid #bcd5e6' }}>Email</th>
                        <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', textTransform: 'uppercase', color: '#264a64', borderBottom: '1px solid #bcd5e6' }}>Mode</th>
                        <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', textTransform: 'uppercase', color: '#264a64', borderBottom: '1px solid #bcd5e6' }}>Due Date</th>
                        <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', textTransform: 'uppercase', color: '#264a64', borderBottom: '1px solid #bcd5e6' }}>Submission</th>
                        <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', textTransform: 'uppercase', color: '#264a64', borderBottom: '1px solid #bcd5e6' }}>Status</th>
                        <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', textTransform: 'uppercase', color: '#264a64', borderBottom: '1px solid #bcd5e6' }}>Mark</th>
                    </tr>
                </thead>
                {/* student data rows */}
                <tbody>
                    {rows.map(row => (
                        <tr key={row.id} onClick={() => onRowClick(row)} style={{cursor:'pointer', borderBottom: '1px solid #bcd5e6', background: '#ffffff'}}>
                            {/* delete — inline, leftmost; same trash icon as the assignments list */}
                            <td style={{ padding: '8px 16px' }}>
                                <button
                                    className="BinIcon"
                                    onClick={(e) => { e.stopPropagation(); onDelete(row.id); }}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                                >
                                    <img src="/Trash.png" width="20" height="20" alt="Delete" />
                                </button>
                            </td>
                            {/* student id */}
                            <td style={{ padding: '8px 16px', color: '#264a64' }}>
                                {row.studentId || '—'}
                            </td>
                            {/* email — list endpoint nests the student under `user` */}
                            <td style={{ padding: '8px 16px', color: '#3b474f' }}>
                                {row.user?.email || row.email || '—'}
                            </td>
                            {/* mode — constant per assignment group */}
                            <td style={{ padding: '8px 16px', color: '#264a64' }}>
                                {MODE_LABELS[mode] || '—'}
                            </td>
                            {/* due date */}
                            <td style={{ padding: '8px 16px', color: '#264a64' }}>
                                {row.dueDate ? new Date(row.dueDate).toLocaleDateString() : '—'}
                            </td>
                            {/* submission — instructor uploads the student's work for Assignment Review */}
                            <td style={{ padding: '8px 16px', color: '#264a64' }}>
                                {mode === 'submission' ? (
                                    <label
                                        onClick={(e) => e.stopPropagation()}
                                        style={{ color: '#2563eb', cursor: 'pointer', textDecoration: 'underline' }}
                                    >
                                        {uploaded[row.id] || row.studentSubmission ? 'Uploaded ✓ (replace)' : 'Upload'}
                                        <input
                                            type="file"
                                            accept=".txt"
                                            style={{ display: 'none' }}
                                            onChange={(e) => handleSubmissionUpload(e, row.id)}
                                        />
                                    </label>
                                ) : '—'}
                            </td>
                            {/* status */}
                            <td style={{ padding: '8px 16px', color: '#264a64', textTransform: 'capitalize' }}>
                                {row.status || '—'}
                            </td>
                            {/* mark */}
                            <td style={{ padding: '8px 16px', color: '#264a64'}}>
                                {row.grade || '-'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div> 
    );
}

export default function ScheduledView({interviews, setInterviews, assignments}) {
    const navigate = useNavigate();
    const [grades, setGrades] = useState({});

    async function handleDeleteInterview(interviewId) {
        if (!window.confirm("Delete this interview? This cannot be undone.")) {
            return;
        }
        try {
            await axios.delete(`/api/interview/${interviewId}`);
            setInterviews(prev => prev.filter(i => i.id !== interviewId));
        } catch {
            alert("Failed to delete the interview.");
        }
    }

    useEffect(() => {
        async function loadGrades() {
            const gradeResults = {};
            for (let i = 0; i < interviews.length; i++) {
                const interviewRow = interviews[i];
                const interviewGrade = await getGradeForInterview(interviewRow.id);
                gradeResults[interviewRow.id] = interviewGrade;
            }
            setGrades(gradeResults);
        }
        loadGrades();

    }, [interviews]);

    const assignmentGroups = [];
    for (let i = 0; i < assignments.length; i++) {
        const assignment = assignments[i];
        const assignmentInterviews = [];
        for (let j = 0; j < interviews.length; j++) {
            if ((interviews[j].assignmentId) == assignment.id) {
                assignmentInterviews.push(interviews[j]);
            }
        }
        if (assignmentInterviews.length > 0) {
            assignmentGroups.push({
                id: assignment.id,
                name: assignment.name,
                mode: assignment.mode,
                interviews: assignmentInterviews,
            });
        }
    }
    return (
    <div style={{ padding: '24px' }}>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '22px', fontWeight: 'normal', color: 'var(--hero)', marginBottom: '24px' }}>Grades & Interviews</h2>
        {assignmentGroups.map(group => (
            <AssignmentGroup
                key={group.id}
                assignmentName={group.name}
                mode={group.mode}
                interviews={group.interviews}
                grades={grades}
                onRowClick={row => navigate(`/report/${row.id}`, { state: { interview: row } })}
                onDelete={handleDeleteInterview}
            />
        ))}
    </div>
    );
}



