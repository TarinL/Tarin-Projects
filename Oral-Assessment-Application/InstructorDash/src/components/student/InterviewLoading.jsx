import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import "../../styles/StudentDash.css";
import { useParams, useNavigate } from "react-router-dom";

// Used only to animate the bar at a believable pace; the join button is revealed
// by the real READY signal from the bot, not by a timer.
const ESTIMATE_MS = 25000;
// Safety net: if the READY status never arrives (e.g. a status write failed), let
// the student in once the room has existed this long rather than stranding them.
const FALLBACK_MS = 45000;

// Rotating messages so the screen never looks frozen. These are deliberately
// silly — the real progress is the bar and the READY signal, so the copy leans
// into being obviously a joke rather than pretending to report genuine phases.
const JOINING_MESSAGES = [
  "Gone fishing for your interviewer…",
  "Catching the interviewer…",
  "Bribing the interviewer with coffee…",
  "Teaching the AI some manners…",
  "Reticulating splines…",
  "Waking the interviewer from its nap…",
  "Polishing the interviewer's monocle…",
  "Convincing the interviewer to come to work…",
];

export default function InterviewLoading() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [zoomUrl, setZoomUrl] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(6);
  const [elapsed, setElapsed] = useState(0);
  const [msgIndex, setMsgIndex] = useState(0);

  const pollRef = useRef(null);
  const tickRef = useRef(null);
  const roomReadyAtRef = useRef(null); // timestamp when the zoom room became available
  const urlRef = useRef(null);
  const revealedRef = useRef(false);

  function reveal(url) {
    if (revealedRef.current) return;
    revealedRef.current = true;
    clearInterval(pollRef.current);
    setZoomUrl(url);
  }

  // Poll the interview: wait for the room (zoom URL), then for the real READY
  // signal the bot writes once it's in the call with audio prepared.
  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 45; // 45 × 2s = 90s before giving up on the room appearing

    pollRef.current = setInterval(async () => {
      attempts++;
      try {
        const response = await axios.get(`/api/interview/${id}/`);
        const url = response.data?.zoom?.url;
        const status = (response.data?.status || "").toUpperCase();

        if (url && url !== "placeholder-link") {
          if (!roomReadyAtRef.current) {
            roomReadyAtRef.current = Date.now();
            urlRef.current = url;
          }
          // The bot is in the call and ready — let the student in immediately.
          if (status === "READY" || status === "COMPLETED") {
            reveal(url);
            return;
          }
          // Safety net if the READY write never lands.
          if (Date.now() - roomReadyAtRef.current >= FALLBACK_MS) {
            reveal(url);
            return;
          }
        }

        if (attempts >= maxAttempts && !roomReadyAtRef.current) {
          clearInterval(pollRef.current);
          setError("The interview room is taking too long to start. Please go back and try again.");
        }
      } catch {
        clearInterval(pollRef.current);
        setError("We couldn't reach the interview service. Please go back and try again.");
      }
    }, 2000);

    return () => clearInterval(pollRef.current);
  }, [id]);

  // Smooth progress + elapsed timer, once per second.
  useEffect(() => {
    tickRef.current = setInterval(() => {
      setElapsed((e) => e + 1);
      setProgress((p) => {
        if (roomReadyAtRef.current) {
          // Room is up: ease 50 → 95 while we wait for the bot to be READY.
          const fraction = Math.min(1, (Date.now() - roomReadyAtRef.current) / ESTIMATE_MS);
          return Math.max(p, 50 + 45 * fraction);
        }
        // Still provisioning: creep toward 50 so it always feels alive.
        return p >= 50 ? p : p + 1.5;
      });
    }, 1000);

    return () => clearInterval(tickRef.current);
  }, []);

  // Rotate the reassurance message.
  useEffect(() => {
    const t = setInterval(() => setMsgIndex((i) => (i + 1) % JOINING_MESSAGES.length), 3500);
    return () => clearInterval(t);
  }, []);

  function backToDashboard() {
    clearInterval(pollRef.current);
    clearInterval(tickRef.current);
    navigate("/student-dashboard");
  }

  const displayProgress = zoomUrl ? 100 : Math.round(progress);

  return (
    <div className="LoadingPage">
      {error ? (
        <>
          <h2>Something went wrong</h2>
          <p>{error}</p>
          <button className="joinBtn" onClick={() => navigate(-1)}>Go Back</button>
        </>
      ) : zoomUrl ? (
        <>
          <h2>Your interview room is ready!</h2>
          <div className="ProgressBar"><div className="ProgressFill" style={{ width: "100%" }} /></div>
          <p>Your AI interviewer is already in the room. Click below to join.</p>
          <a href={zoomUrl} target="_blank" rel="noreferrer">
            <button className="joinBtn">Join Zoom Meeting →</button>
          </a>
          <button className="joinBtn" onClick={() => navigate("/student-dashboard")}>
            Back to Dashboard
          </button>
        </>
      ) : (
        <>
          <h2>Setting up your interview…</h2>
          <div className="ProgressBar">
            <div className="ProgressFill" style={{ width: `${displayProgress}%` }} />
          </div>
          <p className="ProgressMessage">{JOINING_MESSAGES[msgIndex]}</p>
          <p className="ProgressMeta">
            {displayProgress}% · {elapsed}s elapsed — this usually takes under a minute.
          </p>
          <button className="joinBtn" onClick={backToDashboard}>Back to Dashboard</button>
        </>
      )}
    </div>
  );
}
