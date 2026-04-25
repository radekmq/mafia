const PlayerStatusComponent = {

    normalize(player) {
        if (Array.isArray(player)) {
            return {
                display: player[0],
                isActive: player[1]
            };
        }

        return {
            display: player.name,
            isActive: player.alive ?? player.is_alive
        };
    },

    render(wrapperId, players) {
        const wrapper = document.getElementById(wrapperId);
        if (!wrapper) {
            console.warn(`[PlayerStatusComponent] Missing wrapper: #${wrapperId}`);
            return;
        }

        const container = wrapper.querySelector(".options");
        const status = wrapper.querySelector("#" + wrapperId.replace("_wrapper", "_status"));
        if (!container || !status) {
            console.warn(`[PlayerStatusComponent] Missing inner nodes in: #${wrapperId}`);
            return;
        }

        const normalized = (players || []).map(this.normalize);

        container.innerHTML = "";
        status.innerText = "";

        if (normalized.length === 0) {
            status.innerText = "Brak graczy.";
            return;
        }

        normalized.forEach(p => {
            const div = document.createElement("div");

            div.classList.add("option");
            div.classList.add(p.isActive ? "selected" : "disabled");
            div.classList.add(p.isActive ? "status-true" : "status-false");

            div.innerText = p.display + (p.isActive ? "" : " 💀");

            container.appendChild(div);
        });
    }
};

window.PlayerStatusComponent = PlayerStatusComponent;
