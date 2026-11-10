const form = document.querySelector("form");
const input = form.querySelector("input");
const send = form.querySelector("button");
const reset = document.querySelector("#reset");
const log = document.querySelector(".chatlog");
const statusLine = document.querySelector("[role=status]");
const welcome = log.firstElementChild;
const history = [];
const chatList = document.querySelector(".chat-list");
let chatId = chatHistory.newId();

function renderChatList() {
    const chats = chatHistory.list();
    chatList.replaceChildren();
    if (!chats.length) {
        const empty = document.createElement("p");
        empty.className = "note";
        empty.textContent = "Wala pang naka-save na usapan.";
        chatList.append(empty);
    }
    for (const chat of chats) {
        const button = document.createElement("button");
        button.type = "button";
        button.disabled = send.disabled;
        button.textContent = button.title = chatHistory.title(chat);
        if (chat.id === chatId) button.setAttribute("aria-current", "true");
        button.addEventListener("click", () => openChat(chat));
        chatList.append(button);
    }
}

function openChat(chat) {
    if (send.disabled) return;
    chatId = chat ? chat.id : chatHistory.newId();
    history.splice(0, history.length, ...(chat ? chat.messages : []));
    log.replaceChildren(welcome);
    for (const message of history) add(message.role, message.content);
    statusLine.textContent = "";
    input.value = "";
    renderChatList();
    input.focus();
}

function add(role, content) {
    const bubble = document.createElement("p");
    const label = document.createElement("b");
    label.textContent = role === "user" ? "Ikaw" : "TagaLLM";
    bubble.className = "bubble " + role;
    bubble.append(label, document.createTextNode(content));
    log.append(bubble);
    log.scrollTop = log.scrollHeight;
    return bubble;
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const content = input.value.trim();
    if (!content || send.disabled) return;
    const message = {role: "user", content};
    const pending = add("user", content);
    send.disabled = reset.disabled = input.disabled = true;
    renderChatList();
    statusLine.textContent = "Sumasagot…";
    try {
        const reply = await inference.reply([...history.slice(-22), message]);
        history.push(message, {role: "assistant", content: reply});
        add("assistant", reply);
        input.value = "";
        statusLine.textContent = chatHistory.save(chatId, history) ? "" : "Hindi na-save sa browser ang usapan.";
    } catch (error) {
        pending.remove();
        statusLine.textContent = error.message;
    } finally {
        send.disabled = reset.disabled = input.disabled = false;
        renderChatList();
        input.focus();
    }
});

reset.addEventListener("click", () => openChat(null));
window.addEventListener("storage", event => {
    if (chatHistory.isChange(event)) renderChatList();
});
renderChatList();

for (const chip of document.querySelectorAll(".chips button")) {
    chip.addEventListener("click", () => {
        if (send.disabled) return;
        input.value = chip.textContent;
        input.focus();
    });
}

inference.ready().then(message => {
    if (!send.disabled && !statusLine.textContent) statusLine.textContent = message;
});
