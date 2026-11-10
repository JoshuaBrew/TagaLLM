const chatHistory = (() => {
    const prefix = "tagallm-chat:";
    const memory = new Map();

    function list() {
        const chats = new Map();
        try {
            for (let index = 0; index < localStorage.length; index++) {
                const key = localStorage.key(index);
                if (!key || !key.startsWith(prefix)) continue;
                const chat = JSON.parse(localStorage.getItem(key));
                if (chat && Array.isArray(chat.messages) && chat.messages.length) {
                    chats.set(key.slice(prefix.length), chat);
                }
            }
        } catch {
            // The current page can still keep chats in memory.
        }
        for (const [id, chat] of memory) {
            if (!chats.has(id) || chat.updatedAt > chats.get(id).updatedAt) chats.set(id, chat);
        }
        return [...chats.values()].sort((a, b) => b.updatedAt - a.updatedAt);
    }

    function save(id, messages) {
        const chat = {id, messages, updatedAt: Date.now()};
        memory.set(id, chat);
        try {
            localStorage.setItem(prefix + id, JSON.stringify(chat));
        } catch {
            return false;
        }
        return true;
    }

    return {
        list, save,
        newId: () => crypto.randomUUID(),
        title: chat => chat.messages[0].content,
        isChange: event => event.key === null || event.key.startsWith(prefix),
    };
})();
