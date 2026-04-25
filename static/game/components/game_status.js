const GameStatusComponent = {

    getNightActionsProgress(playersNightActionStatus) {
        const players = Array.isArray(playersNightActionStatus) ? playersNightActionStatus : [];
        const total = players.length;

        if (total === 0) {
            return { confirmed: 0, total: 0, percent: 0 };
        }

        const confirmed = players.filter(player => {
            const status = player.status;
            return status === true || String(status).toLowerCase() === "tak";
        }).length;

        return {
            confirmed,
            total,
            percent: Math.round((confirmed / total) * 100),
        };
    },

    renderNightActionsProgress(state) {
        if (state.phase !== "night_actions") return "";

        const progress = this.getNightActionsProgress(state.players_night_action_status);

        return `
            <tr>
                <td>Postęp akcji nocnych:</td>
                <td>
                    <div class="night-actions-progress" aria-label="Postęp akcji nocnych">
                        <div class="night-actions-progress__bar">
                            <div
                                class="night-actions-progress__fill"
                                style="width: ${progress.percent}%;"
                            ></div>
                        </div>
                        <div class="night-actions-progress__label">
                            ${progress.percent}% (${progress.confirmed}/${progress.total})
                        </div>
                    </div>
                </td>
            </tr>
        `;
    },

    render(state) {
        const host = document.getElementById("game_status");
        if (!host) {
            console.warn("[GameStatusComponent] Missing host: #game_status");
            return;
        }

        const confirmedAction =
            state.player_confirmed_action === null
                ? "-"
                : state.player_confirmed_action
                    ? "Tak"
                    : "trwa ...";
        const nightActionsProgress = this.renderNightActionsProgress(state);

        host.innerHTML = `
            <div class="container">
                <table>
                    <tr>
                        <td>Imię gracza:</td>
                        <td>${state.player_name ?? "-"}</td>
                    </tr>
                    <tr>
                        <td>Miejsce:</td>
                        <td>${state.player_seat ?? "-"}</td>
                    </tr>
                    <tr>
                        <td>Status gracza:</td>
                        <td>${state.is_alive ? "Żywy" : "Martwy"}</td>
                    </tr>
                    <tr>
                        <td>Stan gry:</td>
                        <td>${state.game_state_description ?? "-"}</td>
                    </tr>
                    ${state.phase === "night_actions" ? `
                    <tr>
                        <td>Akcja potwierdzona:</td>
                        <td class="player-status-text">${confirmedAction}</td>
                    </tr>
                    ` : ""}
                    ${nightActionsProgress}
                    <tr>
                        <td colspan="2">
                            <div id="players_wrapper" class="choice-container status-display">
                                <div id="players_options" class="options"></div>
                                <div id="players_status"></div>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2" style="text-align: center;">
                            <button onclick="window.location.href='/wiki'">
                                Zobacz listę postaci
                            </button>
                        </td>
                    </tr>
                    ${state.phase === "lobby" ? `
                    <tr>
                        <td colspan="2" style="text-align: center;">
                            <button onclick="window.location.href='/leave_game'">
                                Opuść grę
                            </button>
                        </td>
                    </tr>
                    ` : ""}
                </table>
            </div>
        `;

        if (window.PlayerStatusComponent && typeof window.PlayerStatusComponent.render === "function") {
            window.PlayerStatusComponent.render("players_wrapper", state.players_alive_status);
        }
    }
};

window.GameStatusComponent = GameStatusComponent;
