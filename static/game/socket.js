const host = window.location.hostname;

console.log("[SOCKET] host:", host);

const socket = io(`http://${host}:5000`, {
    transports: ["websocket"],
    reconnection: true,
    reconnectionAttempts: 10,
    timeout: 5000
});

window.socket = socket;

// =========================
// 🔌 CONNECT LIFECYCLE
// =========================

socket.on("connect", () => {
    console.log("[SOCKET] CONNECTED ✔ SID:", socket.id);
});

socket.on("disconnect", (reason) => {
    console.warn("[SOCKET] DISCONNECTED ❌ reason:", reason);
});

socket.on("connect_error", (err) => {
    console.error("[SOCKET] CONNECT ERROR ❌", err);
});

socket.on("reconnect_attempt", (n) => {
    console.log("[SOCKET] RECONNECT ATTEMPT:", n);
});

socket.on("reconnect", () => {
    console.log("[SOCKET] RECONNECTED ✔");
});

// =========================
// 🎮 GAME EVENT
// =========================

socket.on("state_update", (state) => {
    console.log("[SOCKET] STATE UPDATE:", state);
    UI.setState(state);
});
