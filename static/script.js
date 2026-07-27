const chatBox = document.getElementById("chat-box");
const input = document.getElementById("message");
const sendBtn = document.getElementById("send-btn");
const newChatBtn = document.getElementById("new-chat");

async function sendMessage() {

    const message = input.value.trim();

    if (!message) return;

    // User Message
    chatBox.innerHTML += `
        <div class="user">
            ${message}
        </div>
    `;

    chatBox.scrollTop = chatBox.scrollHeight;

    input.value = "";

    // Thinking Animation
    const thinking = document.createElement("div");
    thinking.className = "bot";
    thinking.id = "thinking";
    thinking.innerHTML = "⏳ Flint is thinking...";

    chatBox.appendChild(thinking);

    chatBox.scrollTop = chatBox.scrollHeight;

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });

        const data = await response.json();

        thinking.remove();

        chatBox.innerHTML += `
            <div class="bot">
                ${data.reply}
            </div>
        `;

    }

    catch (error) {

        thinking.remove();

        chatBox.innerHTML += `
            <div class="bot">
                ❌ Something went wrong.
            </div>
        `;

        console.error(error);

    }

    chatBox.scrollTop = chatBox.scrollHeight;

}

// Send Button
sendBtn.addEventListener("click", sendMessage);

// Press Enter
input.addEventListener("keydown", function (event) {

    if (event.key === "Enter") {

        sendMessage();

    }

});

// New Chat
newChatBtn.addEventListener("click", async () => {

    try {

        await fetch("/new-chat", {

            method: "POST"

        });

    }

    catch (error) {

        console.error(error);

    }

    chatBox.innerHTML = `
        <div class="bot">
            👋 Hello Manas! I'm Flint AI.
            <br><br>
            How can I help you today?
        </div>
    `;

    input.value = "";
    input.focus();

});