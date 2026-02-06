let unlocked = false;

export function unlockAudio() {
  if (unlocked) return;
  speechSynthesis.speak(new SpeechSynthesisUtterance(""));
  unlocked = true;
}

export function speak(text) {
  if (!unlocked) return;
  speechSynthesis.cancel();
  speechSynthesis.speak(new SpeechSynthesisUtterance(text));
}
