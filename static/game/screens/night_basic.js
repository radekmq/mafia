window.Screens = window.Screens || {};

window.Screens["night_basic"] = function(state) {

    const container = document.getElementById("game_content");
    if (!container) return;

    const data = state && state.character_data ? state.character_data : {};
    const screenContent = data.screen_content || "";

    container.innerHTML = `
        <div class="container" style="overflow-x:auto;">
            <table cellspacing="0" cellpadding="8">
                <tr>
                    <td style="text-align:center; vertical-align:middle; padding:0;">
                        <a href="wiki/${data.player_link || ""}">
                            <img
                                src="/static/images/${data.player_image || ""}"
                                style="
                                    display:block;
                                    margin: 0 auto;
                                    width: 50%;
                                    height: auto;
                                    cursor: pointer;
                                ">
                        </a>
                    </td>

                    <td style="width:70%; vertical-align:top; white-space: pre-line;">${data.player_info || ""}
                    </td>
                </tr>
                <tr>
                    <td colspan="2">
                        <div id="action_container"></div>
                    </td>
                </tr>
            </table>
        </div>
    `;

    const actionContainer = document.getElementById("action_container");

    if (screenContent === "action_completed") {
        actionContainer.innerHTML = `
            <p class="player-status-text" style="text-align:center;">${data.player_status}</p>
        `;
        return;
    }

    if (screenContent === "confirm_night_action") {
        actionContainer.innerHTML = `
            <p class="player-status-text" style="text-align:center;">${data.player_status}</p>
            <div style="text-align:center; margin-top:10px;">
                <button id="confirm_night_action" type="button">OK</button>
            </div>
        `;

        document.getElementById("confirm_night_action").onclick = () => {
            if (!window.socket || typeof window.socket.send !== "function") {
                console.warn("[night_basic] Socket not available for night action confirmation send");
                return;
            }

            window.socket.send({
                type: "confirm_night_action",
                confirmed_night_action: true,
            });
        };
        return;
    }

    actionContainer.innerHTML = `
        <p class="player-status-text" style="text-align:center;">${data.player_status || ""}</p>
    `;
};
