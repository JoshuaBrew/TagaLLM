const inference = (() => {
    const configured = window.TAGALLM_INFERENCE_ORIGIN;
    const local = ["127.0.0.1", "localhost"].includes(location.hostname);
    const origin = configured ? new URL(configured).origin : local ? location.origin : null;
    const unavailable = "Hindi pa bukas ang online na modelo. Mababasa pa rin ang research article.";

    async function ready() {
        if (!origin) return unavailable;
        if (!configured && local) return "Handa nang subukan ang lokal na chat.";
        if (!origin.startsWith("https://")) return unavailable;
        try {
            const response = await fetch(origin + "/health", {signal: AbortSignal.timeout(8000)});
            if (response.ok && (await response.json()).ready) return "Handa na ang modelo.";
        } catch {}
        return "Nagigising pa o offline ang modelo. Subukan ulit sandali.";
    }

    async function reply(messages) {
        if (!origin || (configured && !origin.startsWith("https://"))) throw new Error(unavailable);
        if (!messages.at(-1)?.content.trim() || messages.at(-1).content.length > 2000) {
            throw new Error("Maglagay ng mensaheng hanggang 2,000 character.");
        }
        try {
            const response = await fetch(origin + "/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(messages),
                signal: AbortSignal.timeout(100000),
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok || typeof result.reply !== "string") {
                throw new Error(result.error || "Hindi pa handa ang modelo. Subukan ulit sandali.");
            }
            return result.reply;
        } catch (error) {
            if (error.name === "TimeoutError") throw new Error("Natagalan ang modelo. Subukan ulit.");
            if (error instanceof TypeError) throw new Error("Hindi makakonekta sa modelo. Subukan ulit.");
            throw error;
        }
    }

    return {ready, reply};
})();
