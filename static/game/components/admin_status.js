const AdminStatusComponent = {

    renderPlayersStatus(list) {
        if (!list) return "";

        return `
            <div class="players-status">
                ${list.map(p => `
                    <div>${p.name}: ${p.status}</div>
                `).join("")}
            </div>
        `;
    },

    renderNightActionsTable(list) {
        if (!list || list.length === 0) return "";

        return `
            <table id="adminNightActionsTable">
                <thead>
                    <tr>
                        <th>Gracz</th>
                        <th>Akcja nocna</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.map(player => `
                        <tr>
                            <td>${player.name}</td>
                            <td>${player.status}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;
    },

    render(state) {
        const host = document.getElementById("admin_panel");
        if (!host) {
            console.warn("[AdminStatusComponent] Missing host: #admin_panel");
            return;
        }

        if (!state.is_admin) {
            host.innerHTML = "";
            return;
        }

        const playersStatus = state.show_player_status
            ? this.renderPlayersStatus(state.players_night_action_status)
            : "";
        const nightActionsTable = state.phase === "night_actions"
            ? this.renderNightActionsTable(state.players_night_action_status)
            : "";

        const isNomination = state.phase === "nomination";
        const isVoting = state.phase === "voting";
        const buttonLabel = isNomination ? "Zakończ nominacje" : "Następny etap";
        const buttonDisabled = isVoting ? "disabled" : "";

        host.innerHTML = `
            <div class="container">
                <h3> Panel administratora</h3>
                <button id="admin_next_step" type="button" ${buttonDisabled}>${buttonLabel}</button>
                ${playersStatus}
                ${nightActionsTable}
            </div>
        `;

        const nextStepButton = host.querySelector("#admin_next_step");
        if (!nextStepButton) {
            return;
        }

        nextStepButton.addEventListener("click", () => {
            if (window.socket && typeof window.socket.send === "function") {
                window.socket.send({ type: isNomination ? "start_execution_phase" : "next_game_state" });
                return;
            }

            console.warn("[AdminStatusComponent] Socket not available for next_game_state send");
        });
    }
};

window.AdminStatusComponent = AdminStatusComponent;
