const {createElement: h, useEffect, useRef, useState} = React;
const starters = [
    "Kumusta? Anong pangalan mo?",
    "Sino si Alex Eala?",
    "Sa mall kami magkikita ng barkada mamaya.",
];

function Bubble({message}) {
    return h("p", {className: "bubble " + message.role},
        h("b", null, message.role === "user" ? "Ikaw" : "TagaLLM"),
        message.content);
}

function Chat() {
    const [history, setHistory] = useState([]);
    const [draft, setDraft] = useState("");
    const [pending, setPending] = useState(null);
    const [error, setError] = useState("");
    const [readiness, setReadiness] = useState("Tinitingnan kung handa na ang modelo…");
    useEffect(() => { inference.ready().then(setReadiness); }, []);
    const [chats, setChats] = useState(chatHistory.list);
    const [chatId, setChatId] = useState(chatHistory.newId);
    const input = useRef(null);
    const log = useRef(null);
    const inFlight = useRef(false);

    useEffect(() => {
        log.current.scrollTop = log.current.scrollHeight;
    }, [history, pending]);

    useEffect(() => {
        function refresh(event) {
            if (chatHistory.isChange(event)) setChats(chatHistory.list());
        }
        window.addEventListener("storage", refresh);
        return () => window.removeEventListener("storage", refresh);
    }, []);

    async function send(event) {
        event.preventDefault();
        const content = draft.trim();
        if (!content || inFlight.current) return;
        const message = {role: "user", content};
        inFlight.current = true;
        setPending(message);
        setError("");
        try {
            const reply = await inference.reply([...history.slice(-22), message]);
            const messages = [...history, message, {role: "assistant", content: reply}];
            setHistory(messages);
            if (!chatHistory.save(chatId, messages)) setError("Hindi na-save sa browser ang usapan.");
            setChats(chatHistory.list());
            setDraft("");
        } catch (error) {
            setError(error.message);
        } finally {
            inFlight.current = false;
            setPending(null);
        }
    }

    function openChat(chat) {
        if (inFlight.current) return;
        setChatId(chat ? chat.id : chatHistory.newId());
        setHistory(chat ? chat.messages : []);
        setDraft("");
        setError("");
        input.current.focus();
    }

    const welcome = {role: "assistant", content: "Kumusta? Anong gusto mong pag-usapan?"};
    const visible = pending ? [...history, pending] : history;
    return h("div", {className: "chat-grid"},
        h("aside", {className: "panel chat-sidebar", "aria-label": "Mga usapan"},
            h("h3", null, "Mga usapan"),
            h("button", {type: "button", className: "primary", disabled: Boolean(pending),
                onClick: () => openChat(null)}, "+ Bagong usapan"),
            h("div", {className: "chat-list"}, chats.length
                ? chats.map(chat => h("button", {key: chat.id, type: "button", disabled: Boolean(pending),
                    "aria-current": chat.id === chatId ? "true" : undefined,
                    onClick: () => openChat(chat), title: chatHistory.title(chat)}, chatHistory.title(chat)))
                : h("p", {className: "note"}, "Wala pang naka-save na usapan."))),
        h("section", {className: "panel chat-panel"},
            h("h3", null, "Usapan"),
            h("div", {className: "chatlog", role: "log", "aria-label": "Usapan", ref: log},
                h(Bubble, {message: welcome}),
                ...visible.map((message, index) => h(Bubble, {message, key: index}))),
            h("form", {className: "composer", onSubmit: send},
                h("input", {
                    ref: input, value: draft, onChange: event => setDraft(event.target.value),
                    readOnly: Boolean(pending), required: true, maxLength: 2000,
                    "aria-label": "Mensahe", placeholder: "Magkuwento ka…",
                }),
                h("button", {className: "primary", disabled: Boolean(pending)}, "Ipadala")),
            h("p", {className: "note", role: "status"}, pending ? "Sumasagot…" : error || readiness)),
        h("aside", {className: "panel"},
            h("span", {className: "tag"}, "Tambayan"),
            h("h2", null, "Anong kuwento mo?"),
            h("div", {className: "chips"}, ...starters.map(prompt =>
                h("button", {
                    key: prompt, type: "button", disabled: Boolean(pending),
                    onClick: () => {
                        setDraft(prompt);
                        input.current.focus();
                    },
                }, prompt)))));
}

ReactDOM.createRoot(document.getElementById("react-chat")).render(h(Chat));
