export default function Dashboard({ reps, duration }) {
  return (
    <div>
      <h2>Workout Stats</h2>
      <p>Reps: {reps}</p>
      <p>Duration: {duration}s</p>
    </div>
  );
}
