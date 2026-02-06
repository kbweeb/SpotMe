import SquatCoach from "./components/SquatCoach";
import "./App.css";

function App() {
  return (
    <div className="app-root">
      {/* Top Bar */}
      <header className="top-bar">
        <h1>GymBuddy AI</h1>
        <span className="status">● Live</span>
      </header>

      {/* Main Content */}
      <div className="main-layout">
        {/* Camera + AI */}
        <section className="camera-section">
          <SquatCoach />
        </section>

        {/* Side Panel */}
        <aside className="side-panel">
          <div className="card">
            <h2>Workout</h2>
            <p>Exercise: Squats</p>
            <p>AI Coach: Active</p>
          </div>

          <div className="card">
            <h2>Tips</h2>
            <ul>
              <li>Keep your back straight</li>
              <li>Push through your heels</li>
              <li>Control your movement</li>
            </ul>
          </div>

          <div className="card">
            <h2>Session</h2>
            <p>Reps tracked in real-time</p>
            <p>Audio feedback enabled</p>
          </div>
        </aside>
      </div>

      {/* Footer */}
      <footer className="footer">
        <p>© 2026 GymBuddy · AI-Powered Fitness Coach</p>
      </footer>
    </div>
  );
}

export default App;
