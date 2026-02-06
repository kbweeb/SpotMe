export function speak(text) {
  if (!window.speechSynthesis) return;

  window.speechSynthesis.cancel();
  const msg = new SpeechSynthesisUtterance(text);
  msg.rate = 1;
  msg.pitch = 1;
  window.speechSynthesis.speak(msg);
}
