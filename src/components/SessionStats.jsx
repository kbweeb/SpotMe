export default function SessionStats({ reps }) {
  function saveSession() {
    const sessions = JSON.parse(localStorage.getItem("sessions")) || [];
    sessions.push({
      reps,
      date: new Date().toISOString(),
    });
    localStorage.setItem("sessions", JSON.stringify(sessions));
  }

  return <button onClick={saveSession}>Save Session</button>;
}
