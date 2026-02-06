export function startSession() {
  return {
    startTime: Date.now(),
    reps: 0,
  };
}

export function endSession(session) {
  return {
    ...session,
    endTime: Date.now(),
    duration:
      (Date.now() - session.startTime) / 1000,
  };
}
