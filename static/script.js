/* ============================================================
   FLINT AI — FRONTEND
   ============================================================ */

(() => {
    "use strict";

    document.addEventListener("DOMContentLoaded", () => {

        const input =
            document.getElementById("message");

        const sendBtn =
            document.getElementById("send-btn");

        const uploadBtn =
            document.getElementById("upload-btn");

        const fileInput =
            document.getElementById("fileInput");

        const chatBox =
            document.getElementById("chat-box");

        const newChatBtn =
            document.getElementById("new-chat");

        const historyBox =
            document.getElementById("chat-history");


        /* ========================================================
           SAFETY
           ======================================================== */

        if (
            !input ||
            !sendBtn ||
            !chatBox
        ) {
            console.error(
                "[Flint AI] Missing required chat elements."
            );
            return;
        }


        /* ========================================================
           STATE
           ======================================================== */

        let currentChatId = null;
        let isGenerating = false;
        let controller = null;
        let userIsScrolling = false;


        /* ========================================================
           HELPERS
           ======================================================== */

        function escapeHtml(value) {

            const div =
                document.createElement("div");

            div.textContent =
                String(value ?? "");

            return div.innerHTML;
        }


        function renderMarkdown(text) {

            const value =
                String(text ?? "");

            if (
                window.marked &&
                typeof marked.parse === "function"
            ) {
                return marked.parse(value);
            }

            return escapeHtml(value)
                .replace(/\n/g, "<br>");
        }


        function highlightCode() {

            if (!window.hljs) {
                return;
            }

            document
                .querySelectorAll("pre code")
                .forEach(block => {

                    try {
                        hljs.highlightElement(block);
                    } catch (_) {}

                });
        }


        function scrollToBottom(force = false) {

            const autoScroll =
                localStorage.getItem("flint-autoscroll");

            if (
                autoScroll === "false" &&
                !force
            ) {
                return;
            }

            if (
                userIsScrolling &&
                !force
            ) {
                return;
            }

            chatBox.scrollTo({
                top: chatBox.scrollHeight,
                behavior: "smooth"
            });
        }


        function setGeneratingUI(active) {

            isGenerating = active;

            sendBtn.disabled = active;

            input.disabled = false;

            if (uploadBtn) {
                uploadBtn.disabled = active;
            }
        }


        /* ========================================================
           USER MESSAGE
           ======================================================== */

        function addUserMessage(text) {

            const message =
                document.createElement("div");

            message.className =
                "user markdown-body";

            message.dataset.role =
                "user";

            const label =
                document.createElement("div");

            label.textContent =
                "YOU";

            const body =
                document.createElement("div");

            body.className =
                "user-message-content";

            body.innerHTML =
                renderMarkdown(text);

            message.append(
                label,
                body
            );

            chatBox.appendChild(message);

            chatBox.classList.add(
                "has-messages"
            );

            scrollToBottom(true);

            return message;
        }


        /* ========================================================
           BOT MESSAGE
           ======================================================== */

        function addBotMessage(initialText = "") {

            const message =
                document.createElement("div");

            message.className =
                "bot markdown-body flint-streaming";

            message.dataset.role =
                "assistant";

            message.dataset.rawText =
                initialText;

            message.setAttribute(
                "aria-live",
                "polite"
            );

            message.innerHTML =
                initialText
                    ? renderMarkdown(initialText)
                    : "";

            chatBox.appendChild(message);

            chatBox.classList.add(
                "has-messages"
            );

            scrollToBottom(true);

            return message;
        }


        /* ========================================================
           THINKING INDICATOR
           ======================================================== */

        function createTypingIndicator() {

            const indicator =
                document.createElement("div");

            indicator.className =
                "bot typing-indicator";

            indicator.innerHTML = `
                <span></span>
                <span></span>
                <span></span>
            `;

            chatBox.appendChild(indicator);

            scrollToBottom(true);

            return indicator;
        }


        function removeTypingIndicator(indicator) {

            if (
                indicator &&
                indicator.parentNode
            ) {
                indicator.remove();
            }
        }


        /* ========================================================
           PLOTLY
           ======================================================== */

        function loadPlotly() {

            if (window.Plotly) {
                return Promise.resolve();
            }

            return new Promise(
                (resolve, reject) => {

                    const script =
                        document.createElement("script");

                    script.src =
                        "https://cdn.plot.ly/plotly-2.35.2.min.js";

                    script.onload =
                        resolve;

                    script.onerror =
                        () => {
                            reject(
                                new Error(
                                    "Plotly could not be loaded."
                                )
                            );
                        };

                    document.head.appendChild(script);
                }
            );
        }


        async function renderChart(chartData) {

            try {

                await loadPlotly();

                let data = chartData;

                if (typeof data === "string") {
                    data = JSON.parse(data);
                }

                if (data && data.chart) {
                    data = data.chart;
                }

                if (data && data.figure) {
                    data = data.figure;
                }

                if (
                    !data ||
                    !Array.isArray(data.data)
                ) {
                    return;
                }

                const wrapper =
                    document.createElement("div");

                wrapper.className =
                    "flint-chart-wrapper";

                wrapper.style.width =
                    "100%";

                wrapper.style.margin =
                    "20px 0";

                const chart =
                    document.createElement("div");

                chart.className =
                    "flint-chart";

                chart.style.width =
                    "100%";

                chart.style.minHeight =
                    "450px";

                chart.style.height =
                    "500px";

                wrapper.appendChild(chart);

                chatBox.appendChild(wrapper);

                await Plotly.newPlot(
                    chart,
                    data.data,
                    {
                        ...(data.layout || {}),
                        autosize: true
                    },
                    {
                        responsive: true,
                        displaylogo: false,
                        modeBarButtonsToRemove: [
                            "lasso2d",
                            "select2d"
                        ]
                    }
                );

                scrollToBottom(true);

            } catch (error) {

                console.error(
                    "[Flint AI] Chart error:",
                    error
                );
            }
        }


        /* ========================================================
           SOURCES
           ======================================================== */

        function renderSources(sources) {

            if (
                !Array.isArray(sources) ||
                !sources.length
            ) {
                return;
            }

            const old =
                chatBox.querySelector(
                    ".flint-sources:last-child"
                );

            if (old) {
                old.remove();
            }

            const container =
                document.createElement("div");

            container.className =
                "flint-sources sources";

            const seen =
                new Set();

            sources.forEach(source => {

                if (!source) {
                    return;
                }

                const name =
                    source.filename ||
                    source.name ||
                    "Unknown document";

                const chunk =
                    source.chunk_index;

                const key =
                    `${name}:${chunk ?? ""}`;

                if (seen.has(key)) {
                    return;
                }

                seen.add(key);

                const item =
                    document.createElement("div");

                item.className =
                    "source-item source";

                item.textContent =
                    chunk == null
                        ? name
                        : `${name} · Chunk ${Number(chunk) + 1}`;

                container.appendChild(item);
            });

            if (container.children.length) {
                chatBox.appendChild(container);
            }

            scrollToBottom(true);
        }


        /* ========================================================
           SSE EVENT
           ======================================================== */

        function processSSEEvent(
            rawEvent,
            botMessage,
            state
        ) {

            if (
                !rawEvent ||
                !rawEvent.trim()
            ) {
                return;
            }

            let eventType = "message";
            let dataText = "";

            rawEvent
                .split("\n")
                .forEach(line => {

                    if (
                        line.startsWith("event:")
                    ) {
                        eventType =
                            line
                                .slice(6)
                                .trim();
                    }

                    else if (
                        line.startsWith("data:")
                    ) {
                        dataText +=
                            line
                                .slice(5)
                                .trim();
                    }

                });

            if (!dataText) {
                return;
            }

            let data;

            try {

                data =
                    JSON.parse(dataText);

            } catch (error) {

                console.error(
                    "[Flint AI] SSE JSON parse error:",
                    error,
                    dataText
                );

                return;
            }


            /* CHAT ID */

            if (eventType === "chat_id") {

                if (
                    data &&
                    data.chat_id != null
                ) {
                    currentChatId =
                        Number(data.chat_id);
                }

                return;
            }


            /* TOKEN */

            if (eventType === "token") {

                const text =
                    data?.text || "";

                state.botText += text;

                botMessage.dataset.rawText =
                    state.botText;

                botMessage.innerHTML =
                    renderMarkdown(
                        state.botText
                    );

                highlightCode();

                scrollToBottom();

                return;
            }


            /* SOURCES */

            if (eventType === "sources") {

                state.sources =
                    Array.isArray(data)
                        ? data
                        : [];

                return;
            }


            /* CHART */

            if (eventType === "chart") {

                state.chart =
                    data;

                return;
            }


            /* ERROR */

            if (eventType === "error") {

                state.error =
                    data?.message ||
                    "Generation failed.";

                return;
            }


            /* DONE */

            if (eventType === "done") {
                state.done = true;
            }
        }

        /* ========================================================
           SEND MESSAGE
           ======================================================== */

        async function sendMessage(prefilled = null) {

            if (isGenerating) {
                return;
            }

            const text =
                prefilled == null
                    ? input.value.trim()
                    : String(prefilled).trim();

            if (!text) {
                return;
            }


            /* USER */

            addUserMessage(text);

            input.value = "";
            input.focus();


            /* THINKING */

            const typing =
                createTypingIndicator();


            /* BOT */

            const botMessage =
                addBotMessage();


            const state = {
                botText: "",
                sources: [],
                chart: null,
                done: false,
                error: null
            };


            setGeneratingUI(true);

            controller =
                new AbortController();


            try {

                const response =
                    await fetch(
                        "/chat/stream",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                message: text,
                                chat_id:
                                    currentChatId
                            }),

                            signal:
                                controller.signal
                        }
                    );


                if (!response.ok) {

                    throw new Error(
                        `HTTP ${response.status}`
                    );
                }


                if (!response.body) {

                    throw new Error(
                        "Streaming response body is unavailable."
                    );
                }


                removeTypingIndicator(
                    typing
                );


                const reader =
                    response.body.getReader();

                const decoder =
                    new TextDecoder();

                let buffer = "";


                while (true) {

                    const {
                        value,
                        done
                    } =
                        await reader.read();


                    if (done) {
                        break;
                    }


                    buffer +=
                        decoder.decode(
                            value,
                            {
                                stream: true
                            }
                        );


                    const events =
                        buffer.split("\n\n");


                    buffer =
                        events.pop() || "";


                    events.forEach(event => {

                        processSSEEvent(
                            event,
                            botMessage,
                            state
                        );

                    });

                }


                /* Flush decoder */

                buffer +=
                    decoder.decode();


                if (buffer.trim()) {

                    processSSEEvent(
                        buffer,
                        botMessage,
                        state
                    );
                }


                /* ====================================================
                   FINAL RESPONSE
                   ==================================================== */

                if (state.error) {

                    botMessage.dataset.rawText =
                        state.error;

                    botMessage.innerHTML = `
                        <p class="flint-error">
                            ❌
                            ${escapeHtml(
                                state.error
                            )}
                        </p>
                    `;

                }

                else {

                    botMessage.dataset.rawText =
                        state.botText;

                    botMessage.innerHTML =
                        renderMarkdown(
                            state.botText
                        );


                    highlightCode();


                    if (state.chart) {

                        await renderChart(
                            state.chart
                        );
                    }


                    renderSources(
                        state.sources
                    );
                }


                botMessage.classList.remove(
                    "flint-streaming"
                );

                botMessage.classList.add(
                    "flint-complete"
                );


                highlightCode();


                addResponseActions(
                    botMessage
                );


                scrollToBottom(true);


                await loadChatHistory();

            }


            catch (error) {

                removeTypingIndicator(
                    typing
                );


                botMessage.classList.remove(
                    "flint-streaming"
                );


                const message =
                    error.name === "AbortError"
                        ? "Generation stopped."
                        : error.message;


                botMessage.dataset.rawText =
                    message;


                botMessage.innerHTML = `
                    <p class="flint-error">
                        ❌
                        ${escapeHtml(message)}
                    </p>
                `;


                addResponseActions(
                    botMessage
                );


                console.error(
                    "[Flint AI] Chat error:",
                    error
                );

            }


            finally {

                controller = null;

                setGeneratingUI(false);

                input.focus();
            }
        }


        /* ========================================================
           CHAT HISTORY
           ======================================================== */

        async function loadChatHistory() {

            if (!historyBox) {
                return;
            }


            try {

                const response =
                    await fetch("/chats");


                if (!response.ok) {
                    return;
                }


                const chats =
                    await response.json();


                historyBox.innerHTML = "";


                if (!Array.isArray(chats)) {
                    return;
                }


                chats.forEach(chat => {

                    const item =
                        document.createElement(
                            "button"
                        );

                    item.type = "button";

                    item.className =
                        "history-item";


                    if (
                        Number(chat.id) ===
                        Number(currentChatId)
                    ) {

                        item.classList.add(
                            "active"
                        );
                    }


                    item.textContent =
                        chat.title ||
                        `Chat ${chat.id}`;


                    item.addEventListener(
                        "click",
                        () => {

                            openChat(
                                chat.id
                            );

                        }
                    );


                    historyBox.appendChild(
                        item
                    );

                });

            }


            catch (error) {

                console.error(
                    "[Flint AI] History error:",
                    error
                );

            }
        }


        /* ========================================================
           OPEN CHAT
           ======================================================== */

        async function openChat(chatId) {

            if (isGenerating) {
                return;
            }


            try {

                const response =
                    await fetch(
                        `/messages/${chatId}`
                    );


                if (!response.ok) {

                    throw new Error(
                        `HTTP ${response.status}`
                    );
                }


                const messages =
                    await response.json();


                currentChatId =
                    chatId;


                chatBox.innerHTML = "";

                chatBox.classList.add(
                    "has-messages"
                );


                if (Array.isArray(messages)) {

                    messages.forEach(
                        message => {

                            if (
                                message.role ===
                                "user"
                            ) {

                                addUserMessage(
                                    message.content || ""
                                );

                            }

                            else {

                                const bot =
                                    addBotMessage(
                                        message.content || ""
                                    );


                                bot.classList.remove(
                                    "flint-streaming"
                                );

                                bot.classList.add(
                                    "flint-complete"
                                );


                                bot.dataset.rawText =
                                    message.content || "";


                                bot.innerHTML =
                                    renderMarkdown(
                                        message.content || ""
                                    );


                                addResponseActions(
                                    bot
                                );
                            }

                        }
                    );
                }


                highlightCode();

                await loadChatHistory();

                scrollToBottom(true);

                input.focus();

            }


            catch (error) {

                console.error(
                    "[Flint AI] Open chat error:",
                    error
                );

            }
        }


        /* ========================================================
           UPLOAD
           ======================================================== */

        if (
            uploadBtn &&
            fileInput
        ) {

            uploadBtn.addEventListener(
                "click",
                event => {

                    event.preventDefault();


                    if (!isGenerating) {

                        fileInput.click();

                    }

                }
            );


            fileInput.addEventListener(
                "change",
                async () => {

                    const file =
                        fileInput.files?.[0];


                    if (!file) {
                        return;
                    }


                    uploadBtn.disabled =
                        true;


                    try {

                        const form =
                            new FormData();


                        form.append(
                            "file",
                            file
                        );


                        if (
                            currentChatId !=
                            null
                        ) {

                            form.append(
                                "chat_id",
                                currentChatId
                            );
                        }


                        const response =
                            await fetch(
                                "/upload",
                                {
                                    method: "POST",
                                    body: form
                                }
                            );


                        if (!response.ok) {

                            throw new Error(
                                `Upload failed: ${response.status}`
                            );
                        }


                        const result =
                            await response.json();


                        if (
                            result.chat_id !=
                            null
                        ) {

                            currentChatId =
                                Number(
                                    result.chat_id
                                );
                        }


                        const bot =
                            addBotMessage();


                        bot.classList.remove(
                            "flint-streaming"
                        );


                        bot.dataset.rawText =
                            `${file.name} uploaded successfully.`;


                        bot.innerHTML = `
                            <p>
                                📎
                                <strong>
                                    ${escapeHtml(
                                        file.name
                                    )}
                                </strong>
                                uploaded successfully.
                            </p>

                            <p>
                                You can now ask me
                                questions about it.
                            </p>
                        `;


                        addResponseActions(
                            bot
                        );


                        await loadChatHistory();

                    }


                    catch (error) {

                        const bot =
                            addBotMessage();


                        bot.classList.remove(
                            "flint-streaming"
                        );


                        bot.innerHTML = `
                            <p class="flint-error">
                                ❌ Upload failed:
                                ${escapeHtml(
                                    error.message
                                )}
                            </p>
                        `;

                    }


                    finally {

                        uploadBtn.disabled =
                            false;

                        fileInput.value = "";

                    }

                }
            );
        }


        /* ========================================================
           NEW CHAT
           ======================================================== */

        function newChat() {

            if (controller) {
                controller.abort();
            }


            currentChatId = null;

            isGenerating = false;


            chatBox.classList.remove(
                "has-messages"
            );


            chatBox.innerHTML = `
                <div class="welcome-screen">

                    <div class="welcome-glow"></div>

                    <div class="welcome-logo">

                        <div class="welcome-logo-inner">
                            F
                        </div>

                    </div>

                    <div class="welcome-eyebrow">
                        INTELLIGENT WORKSPACE
                    </div>

                    <h1>
                        What can
                        <span>Flint</span>
                        help you solve?
                    </h1>

                    <p class="welcome-description">
                        Analyze data, understand documents,
                        create visualizations, and explore
                        ideas with your AI workspace.
                    </p>

                </div>
            `;


            input.value = "";

            input.focus();

            loadChatHistory();
        }


        if (newChatBtn) {

            newChatBtn.addEventListener(
                "click",
                newChat
            );
        }


        /* ========================================================
           SEND BUTTON
           ======================================================== */

        sendBtn.addEventListener(
            "click",
            event => {

                event.preventDefault();

                sendMessage();

            }
        );


        /* ========================================================
           ENTER KEY
           ======================================================== */

        input.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    sendMessage();

                }

            }
        );


        /* ========================================================
           CHAT SCROLL
           ======================================================== */

        chatBox.addEventListener(
            "scroll",
            () => {

                const distance =
                    chatBox.scrollHeight -
                    chatBox.scrollTop -
                    chatBox.clientHeight;


                userIsScrolling =
                    distance > 180;

            }
        );

        /* ========================================================
           SUGGESTION CARDS
           ======================================================== */

        document
            .querySelectorAll(".suggestion-card")
            .forEach(card => {

                card.addEventListener(
                    "click",
                    () => {

                        const prompt =
                            card.dataset.prompt;


                        if (!prompt) {
                            return;
                        }


                        input.value =
                            prompt;

                        input.focus();

                    }
                );

            });


        /* ========================================================
           KEYBOARD SHORTCUTS
           ======================================================== */

        document.addEventListener(
            "keydown",
            event => {

                /* NEW CHAT — Ctrl/Cmd + N */

                if (
                    (
                        event.ctrlKey ||
                        event.metaKey
                    ) &&
                    event.key.toLowerCase() === "n"
                ) {

                    event.preventDefault();

                    newChat();

                }


                /* STOP GENERATION — Escape */

                if (
                    event.key === "Escape" &&
                    controller
                ) {

                    controller.abort();

                }

            }
        );


        /* ========================================================
           SETTINGS
           ======================================================== */

        function createSettingsPanel() {

            let overlay =
                document.getElementById(
                    "flint-settings-panel"
                );


            if (overlay) {
                return overlay;
            }


            overlay =
                document.createElement("div");

            overlay.id =
                "flint-settings-panel";

            overlay.className =
                "flint-settings-overlay";


            overlay.innerHTML = `
                <div class="flint-settings-panel">

                    <div class="flint-settings-header">

                        <div>

                            <div class="flint-settings-title">
                                Settings
                            </div>

                            <div class="flint-settings-subtitle">
                                Customize your Flint workspace
                            </div>

                        </div>

                        <button
                            type="button"
                            class="flint-settings-close"
                        >
                            ×
                        </button>

                    </div>


                    <div class="flint-settings-body">

                        <div class="flint-setting-section">

                            <div class="flint-setting-label">
                                Appearance
                            </div>


                            <button
                                type="button"
                                class="flint-setting-option"
                                data-theme="dark"
                            >

                                <span>
                                    ◐
                                </span>

                                <div>

                                    <strong>
                                        Dark
                                    </strong>

                                    <small>
                                        Flint's default dark workspace
                                    </small>

                                </div>

                                <span class="setting-check">
                                    ✓
                                </span>

                            </button>


                            <button
                                type="button"
                                class="flint-setting-option"
                                data-theme="light"
                            >

                                <span>
                                    ○
                                </span>

                                <div>

                                    <strong>
                                        Light
                                    </strong>

                                    <small>
                                        A brighter workspace
                                    </small>

                                </div>

                                <span class="setting-check">
                                    ✓
                                </span>

                            </button>

                        </div>


                        <div class="flint-setting-section">

                            <div class="flint-setting-label">
                                Chat
                            </div>


                            <label class="flint-toggle-row">

                                <div>

                                    <strong>
                                        Smooth animations
                                    </strong>

                                    <small>
                                        Enable Flint UI animations
                                    </small>

                                </div>

                                <input
                                    id="flint-animations"
                                    type="checkbox"
                                    checked
                                >

                                <span class="flint-toggle"></span>

                            </label>


                            <label class="flint-toggle-row">

                                <div>

                                    <strong>
                                        Auto scroll
                                    </strong>

                                    <small>
                                        Follow new responses automatically
                                    </small>

                                </div>

                                <input
                                    id="flint-autoscroll"
                                    type="checkbox"
                                    checked
                                >

                                <span class="flint-toggle"></span>

                            </label>

                        </div>


                        <div class="flint-setting-section">

                            <div class="flint-setting-label">
                                About
                            </div>


                            <div class="flint-about-card">

                                <div class="flint-about-logo">
                                    F
                                </div>

                                <div>

                                    <strong>
                                        Flint AI
                                    </strong>

                                    <small>
                                        Intelligent AI Workspace
                                    </small>

                                    <small>
                                        Version 1.0
                                    </small>

                                </div>

                            </div>

                        </div>

                    </div>

                </div>
            `;


            document.body.appendChild(
                overlay
            );


            /* ====================================================
               THEME
               ==================================================== */

            const savedTheme =
                localStorage.getItem(
                    "flint-theme"
                ) || "dark";


            document.body.dataset.theme =
                savedTheme;


            overlay
                .querySelectorAll("[data-theme]")
                .forEach(button => {

                    button.classList.toggle(
                        "active",
                        button.dataset.theme ===
                        savedTheme
                    );


                    button.addEventListener(
                        "click",
                        () => {

                            const theme =
                                button.dataset.theme;


                            document.body.dataset.theme =
                                theme;


                            localStorage.setItem(
                                "flint-theme",
                                theme
                            );


                            overlay
                                .querySelectorAll(
                                    "[data-theme]"
                                )
                                .forEach(b => {

                                    b.classList.remove(
                                        "active"
                                    );

                                });


                            button.classList.add(
                                "active"
                            );

                        }
                    );

                });


            /* ====================================================
               ANIMATIONS
               ==================================================== */

            const animations =
                overlay.querySelector(
                    "#flint-animations"
                );


            const savedAnimations =
                localStorage.getItem(
                    "flint-animations"
                );


            if (savedAnimations !== null) {

                animations.checked =
                    savedAnimations === "true";

            }


            document.body.classList.toggle(
                "reduce-motion",
                !animations.checked
            );


            animations.addEventListener(
                "change",
                () => {

                    document.body.classList.toggle(
                        "reduce-motion",
                        !animations.checked
                    );


                    localStorage.setItem(
                        "flint-animations",
                        animations.checked
                    );

                }
            );


            /* ====================================================
               AUTO SCROLL
               ==================================================== */

            const autoScroll =
                overlay.querySelector(
                    "#flint-autoscroll"
                );


            const savedAuto =
                localStorage.getItem(
                    "flint-autoscroll"
                );


            if (savedAuto !== null) {

                autoScroll.checked =
                    savedAuto === "true";

            }


            autoScroll.addEventListener(
                "change",
                () => {

                    localStorage.setItem(
                        "flint-autoscroll",
                        autoScroll.checked
                    );

                }
            );


            /* ====================================================
               CLOSE
               ==================================================== */

            overlay
                .querySelector(
                    ".flint-settings-close"
                )
                .addEventListener(
                    "click",
                    closeSettings
                );


            overlay.addEventListener(
                "click",
                event => {

                    if (
                        event.target ===
                        overlay
                    ) {

                        closeSettings();

                    }

                }
            );


            return overlay;
        }


        function openSettings() {

            const panel =
                createSettingsPanel();


            requestAnimationFrame(
                () => {

                    panel.classList.add(
                        "visible"
                    );

                }
            );
        }


        function closeSettings() {

            const panel =
                document.getElementById(
                    "flint-settings-panel"
                );


            if (!panel) {
                return;
            }


            panel.classList.remove(
                "visible"
            );


            setTimeout(
                () => {

                    if (panel.parentNode) {
                        panel.remove();
                    }

                },
                220
            );
        }


        /* ========================================================
           SETTINGS BUTTONS
           ======================================================== */

        document
            .querySelectorAll(
                ".sidebar-settings, .header-button"
            )
            .forEach(button => {

                const text = `
                    ${button.textContent || ""}
                    ${button.getAttribute("title") || ""}
                `.toLowerCase();


                if (
                    text.includes("settings") ||
                    text.includes("⚙")
                ) {

                    button.addEventListener(
                        "click",
                        event => {

                            event.preventDefault();

                            event.stopPropagation();

                            openSettings();

                        }
                    );

                }

            });


        /* ========================================================
           RESPONSE ACTIONS
           ======================================================== */

        function addResponseActions(
            botMessage
        ) {

            if (
                !botMessage ||
                botMessage.querySelector(
                    ".flint-response-actions"
                )
            ) {
                return;
            }


            const actions =
                document.createElement("div");


            actions.className =
                "flint-response-actions";


            actions.innerHTML = `
                <button
                    type="button"
                    class="flint-action"
                    data-action="copy"
                    title="Copy response"
                >
                    <span>▣</span>
                    <span>Copy</span>
                </button>


                <button
                    type="button"
                    class="flint-action"
                    data-action="regenerate"
                    title="Regenerate response"
                >
                    <span>↻</span>
                    <span>Regenerate</span>
                </button>


                <span class="flint-action-divider"></span>


                <button
                    type="button"
                    class="flint-action flint-feedback"
                    data-action="like"
                    title="Good response"
                >
                    👍
                </button>


                <button
                    type="button"
                    class="flint-action flint-feedback"
                    data-action="dislike"
                    title="Bad response"
                >
                    👎
                </button>
            `;


            botMessage.appendChild(
                actions
            );


            /* ====================================================
               COPY
               ==================================================== */

            const copyButton =
                actions.querySelector(
                    '[data-action="copy"]'
                );


            copyButton.addEventListener(
                "click",
                async event => {

                    const button =
                        event.currentTarget;


                    const raw =
                        botMessage.dataset.rawText ||
                        botMessage.innerText ||
                        "";


                    try {

                        await navigator.clipboard.writeText(
                            raw
                        );


                        button.innerHTML = `
                            <span>✓</span>
                            <span>Copied</span>
                        `;


                        setTimeout(
                            () => {

                                button.innerHTML = `
                                    <span>▣</span>
                                    <span>Copy</span>
                                `;

                            },
                            1600
                        );

                    }


                    catch (error) {

                        console.error(
                            "[Flint AI] Copy failed:",
                            error
                        );

                    }

                }
            );


            /* ====================================================
               LIKE / DISLIKE
               ==================================================== */

            const like =
                actions.querySelector(
                    '[data-action="like"]'
                );


            const dislike =
                actions.querySelector(
                    '[data-action="dislike"]'
                );


            like.addEventListener(
                "click",
                () => {

                    like.classList.toggle(
                        "selected"
                    );


                    dislike.classList.remove(
                        "selected"
                    );

                }
            );


            dislike.addEventListener(
                "click",
                () => {

                    dislike.classList.toggle(
                        "selected"
                    );


                    like.classList.remove(
                        "selected"
                    );

                }
            );


            /* ====================================================
               REGENERATE
               ==================================================== */

            actions
                .querySelector(
                    '[data-action="regenerate"]'
                )
                .addEventListener(
                    "click",
                    () => {

                        regenerateResponse(
                            botMessage
                        );

                    }
                );

        }

        /* ========================================================
           REGENERATE RESPONSE
           ======================================================== */

        async function regenerateResponse(
            botMessage
        ) {

            if (isGenerating) {
                return;
            }


            /*
             * Find the closest previous user message.
             */

            let previous =
                botMessage.previousElementSibling;


            while (
                previous &&
                !previous.classList.contains("user")
            ) {

                previous =
                    previous.previousElementSibling;

            }


            if (!previous) {

                console.warn(
                    "[Flint AI] Original user message not found."
                );

                return;
            }


            /*
             * Extract the original prompt.
             */

            const content =
                previous.querySelector(
                    ".user-message-content"
                );


            const original =
                (
                    content
                        ? content.innerText
                        : previous.innerText
                ).trim();


            if (!original) {
                return;
            }


            /*
             * Remove the old response.
             */

            botMessage.remove();


            /*
             * Generate a fresh response.
             */

            await sendMessage(
                original
            );
        }


        /* ========================================================
           INITIALIZATION
           ======================================================== */

        loadChatHistory();

        input.focus();


        console.log(
            "[Flint AI] Frontend initialized successfully."
        );

    });

})();