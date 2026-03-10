import React, { useCallback, useState } from "react";
import CameraView from "./components/CameraView";
import "./App.css";

function App() {
  const [reps, setReps] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [status, setStatus] = useState("Starting GymBuddy...");
  const [exercise, setExercise] = useState("unknown");
  const [confidence, setConfidence] = useState(0);
  const [classifier, setClassifier] = useState("heuristic");

  const speak = useCallback((text) => {
    if (!text) return;
    if (typeof window === "undefined") return;
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) return;
    try {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new window.SpeechSynthesisUtterance(text));
    } catch (err) {
      console.warn("Speech synthesis failed", err);
    }
  }, []);

  const handleUpdate = useCallback(
    (data) => {
      if (data.reps !== undefined) setReps(data.reps);
      if (data.exercise) setExercise(data.exercise);
      if (data.confidence !== undefined) setConfidence(Number(data.confidence) || 0);
      if (data.classifier) setClassifier(data.classifier);

      if (data.error) {
        setFeedback(data.error);
        return;
      }
      if (data.feedback) {
        setFeedback(data.feedback);
        speak(data.feedback);
      } else {
        setFeedback("");
      }
    },
    [speak],
  );

  const handleStatus = useCallback((message) => {
    setStatus(message);
  }, []);

  return (
    <div className="app">
      <h1>GymBuddy AI (Python Powered)</h1>
      <CameraView onUpdate={handleUpdate} onStatus={handleStatus} />
      <p className="status">{status}</p>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Reps</div>
          <div className="stat-value">{reps}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Exercise</div>
          <div className="stat-value stat-value--text">{exercise}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Confidence</div>
          <div className="stat-value stat-value--text">{(confidence * 100).toFixed(1)}%</div>
        </div>
      </div>
      <p className="classifier">Classifier: {classifier}</p>
      <p className="feedback">{feedback || "No movement feedback yet."}</p>
    </div>
  );
}

export default App;
