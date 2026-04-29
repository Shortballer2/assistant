const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");

function appendMessage(text, role) {
  const bubble = document.createElement("div");
  bubble.className = `msg ${role}`;
  bubble.textContent = text;
  chat.appendChild(bubble);
  chat.scrollTop = chat.scrollHeight;
}

appendMessage("Hi! I am your assistant. Ask me anything.", "assistant");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendMessage(message, "user");
  input.value = "";

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await resp.json();
    if (!resp.ok) {
      appendMessage(data.detail || "Something went wrong.", "assistant");
      return;
    }

    appendMessage(data.reply || "No response.", "assistant");
  } catch {
    appendMessage("Network error. Please try again.", "assistant");
  }
});
