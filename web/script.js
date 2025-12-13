let chatBox = document.getElementById("chat-box");

function addMessage(message, sender) {
    let msgDiv = document.createElement("div");
    msgDiv.classList.add("msg", sender);
    msgDiv.textContent = message;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function sendMessage() {
    let input = document.getElementById("user-input");
    let text = input.value.trim();

    if (!text) return;

    addMessage(text, "user");
    input.value = "";

    // Dummy bot response
    setTimeout(() => {
        addMessage("Thanks! Your message was: " + text, "bot");
    }, 500);
}

