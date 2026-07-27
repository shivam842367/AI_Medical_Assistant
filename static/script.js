const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "/login";
}

const sendBtn = document.getElementById("send-btn");
const input = document.getElementById("user-input");
const chatBox = document.getElementById("chat-box");
const historyBox = document.getElementById("history");

// Logout
document.getElementById("logout-btn").onclick = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
};

// New Chat
document.getElementById("new-chat-btn").onclick = () => {
    chatBox.innerHTML = "";
};

// Format AI Response
function formatResponse(text) {

    if (!text) return "";

    text = text
        .replace(/<br\s*\/?>/gi, "\n")
        .replace(/<\/?b>/gi, "**");

    return text
        .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
        .replace(/\n/g, "<br>")
        .replace(/^\*\s/gm, "• ");

}

async function typeMessage(element, text) {

    let formatted = formatResponse(text);

    let current = "";

    for (let i = 0; i < formatted.length; i++) {

        current += formatted.charAt(i);

        element.innerHTML = current;

        chatBox.scrollTop = chatBox.scrollHeight;

        await new Promise(resolve => setTimeout(resolve, 8));
    }

}

// Helper for Unauthorized response
function handleUnauthorized() {
    localStorage.removeItem("token");
    alert("Session expired or invalid credentials. Please log in again.");
    window.location.href = "/login";
}

// Load Chat History
async function loadHistory() {

    try {

        const response = await fetch("/ai/history", {
            headers: {
                Authorization: "Bearer " + token
            }
        });

        if (response.status === 401) {
            localStorage.removeItem("token");
            window.location.href = "/login";
            return;
        }

        if (!response.ok) return;

        const chats = await response.json();

        historyBox.innerHTML = "";

        chats.reverse().forEach(chat => {

    historyBox.innerHTML += `
    <div class="history-item"
        onclick="openChat(${chat.id})">

        <span class="history-text">
            ${chat.question}
        </span>

        <button
            class="delete-btn"
            onclick="event.stopPropagation(); deleteChat(${chat.id})">
            🗑️
        </button>

    </div>
    `;
});


    } catch (err) {

        console.log(err);

    }

}

async function deleteChat(chatId) {

    const ok = confirm("Delete this chat?");

    if (!ok) return;

    try {

        const response = await fetch(`/ai/delete/${chatId}`, {

            method: "DELETE",

            headers: {
                Authorization: "Bearer " + token
            }

        });

        if (response.status === 401) {
            handleUnauthorized();
            return;
        }

        const data = await response.json();

        if (!response.ok) {

            alert(data.detail || "Unable to delete chat.");
            return;

        }

        loadHistory();

    } catch (err) {

        console.log(err);
        alert("Something went wrong.");

    }

}

function openChat(chatId){

    fetch("/ai/history",{
        headers:{
            Authorization:"Bearer "+token
        }
    })

    .then(res => {
        if (res.status === 401) {
            handleUnauthorized();
            return null;
        }
        return res.json();
    })

    .then(chats=>{

        if(!chats) return;

        const chat=chats.find(c=>c.id===chatId);

        if(!chat) return;

        chatBox.innerHTML = `
        <div class="user">
            <b>You:</b><br>${chat.question}
            <div class="time">
                ${chat.created_at || ""}
            </div>
        </div>

        <div class="bot">
            <b>🩺 AI:</b><br><br>
            ${formatResponse(chat.answer)}
            <div class="time">${chat.created_at || ""}</div>
        </div>
        `;

    });

}

// Send Message
async function sendMessage() {

    const message = input.value.trim();

    if (message === "") return;

    sendBtn.disabled = true;
    sendBtn.innerText = "Generating...";
    input.disabled = true;

    chatBox.innerHTML += `
    <div class="user">
        <b>You:</b><br>${message}
        <div class="time">${new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
        })}</div>
    </div>
    `;

    chatBox.innerHTML += `
    <div class="bot typing-box" id="typing">

        <div class="typing-header">
            🩺 AI Assistant
        </div>

        <div class="typing-animation">
            <span></span>
            <span></span>
            <span></span>
        </div>

    </div>
    `;

    chatBox.scrollTop = chatBox.scrollHeight;

    try {

        const response = await fetch("/ai/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json",
                Authorization: "Bearer " + token
            },

            body: JSON.stringify({
                message: message
            })

        });

        const data = await response.json();

        const typing = document.getElementById("typing");

        if (typing) {
            typing.remove();
        }

        if (response.status === 401 || data.detail === "Could not validate credentials") {
            handleUnauthorized();
            return;
        }

        if (!response.ok) {

            chatBox.innerHTML += `
                <div class="bot">
                    ⚠ ${data.detail || "Something went wrong."}
                </div>
            `;

            return;

        }

       chatBox.innerHTML += `
        <div class="bot">
                <b>🩺 AI:</b><br><br>
                <div id="ai-response"></div>
                <div class="time">${new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit"
                })}</div>
        </div>
        `;

        const aiBox = document.getElementById("ai-response");

        await typeMessage(aiBox, data.response);

        chatBox.scrollTop = chatBox.scrollHeight;

        loadHistory();

    } catch (err) {

        const typing = document.getElementById("typing");

        if (typing) {
            typing.remove();
        }

        chatBox.innerHTML += `
            <div class="bot">
                ⚠ AI Service unavailable.<br>Please try again.
            </div>
        `;

    } finally {
        sendBtn.disabled = false;
        sendBtn.innerText = "Send";
        input.disabled = false;
        input.focus();
    }

}

sendBtn.onclick = sendMessage;

input.addEventListener("keydown", function(e) {

    if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
    }

});

loadHistory();

input.focus();

// ---------------- Voice Input ----------------

const micBtn = document.getElementById("mic-btn");

if ("webkitSpeechRecognition" in window) {

    const recognition = new webkitSpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    micBtn.addEventListener("click", () => {
        recognition.start();
    });

    recognition.onstart = function () {
        console.log("Voice recognition started");
    };

    recognition.onend = function () {
        console.log("Voice recognition ended");
    };

    recognition.onresult = function(event) {
        input.value = event.results[0][0].transcript;
    };

    recognition.onerror = function(event) {
        console.log("Speech Error:", event.error);
        alert("Voice recognition error: " + event.error);
    };

} else {

  micBtn.style.display = "none";

}

// ---------------- Search Chat ----------------

const searchInput = document.getElementById("search-chat");

searchInput.addEventListener("input", function () {

    const value = this.value.toLowerCase();

    document.querySelectorAll(".history-item").forEach(item => {

        const text = item.querySelector(".history-text").innerText.toLowerCase();

        if (text.includes(value)) {
            item.style.display = "flex";
        } else {
            item.style.display = "none";
        }

    });

});

// ---------------- Report Analyzer Navigation ----------------

const reportBtn = document.getElementById("report-btn");
if (reportBtn) {
    reportBtn.addEventListener("click", () => {
        window.location.href = "/report";
    });
}

// ---------------- Download Report ----------------

document.getElementById("download-btn").addEventListener("click", () => {

    const { jsPDF } = window.jspdf;

    const doc = new jsPDF();

    doc.setFontSize(18);
    doc.text("AI Medical Assistant Report", 20, 20);

    doc.setFontSize(12);

    const report = chatBox.innerText || "No conversation available.";

    const lines = doc.splitTextToSize(report, 170);

    doc.text(lines, 20, 35);

    doc.save("Medical_Report.pdf");

});

// ================= Dark Mode =================

const themeBtn = document.getElementById("theme-btn");

// Previous theme
if(localStorage.getItem("theme") === "dark"){
    document.body.classList.add("dark");
    themeBtn.innerHTML = "☀";
}

themeBtn.addEventListener("click", () => {

    document.body.classList.toggle("dark");

    if(document.body.classList.contains("dark")){

        localStorage.setItem("theme","dark");
        themeBtn.innerHTML="☀";

    }else{

        localStorage.setItem("theme","light");
        themeBtn.innerHTML="🌙";

    }

});