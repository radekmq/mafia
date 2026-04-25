window.Screens = window.Screens || {};

window.Screens["night_truciciel"] = function(state) {

    const container = document.getElementById("game_content");
    if (!container) return;

    const data = state.character_data;
    const screenContent = data.screen_content;

    container.innerHTML = `
        <div class="container" style="overflow-x:auto;">
            <table cellspacing="0" cellpadding="8">
                <tr>
                    <td style="text-align:center; vertical-align:middle; padding:0;">
                        <a href="wiki/${data.player_link}">
                            <img
                                src="/static/images/${data.player_image}"
                                style="
                                    display:block;
                                    margin: 0 auto;
                                    width: 50%;
                                    height: auto;
                                    cursor: pointer;
                                ">
                        </a>
                    </td>

                    <td style="width:70%; vertical-align:top; white-space: pre-line;">${data.player_info}
                    </td>
                </tr>
                <tr>
                    <td>Lista Minionów:</td>
                    <td class="player-status-text">${data.truciciel_minions || ""}</td>
                </tr>
                <tr>
                    <td colspan="2">
                        <div id="poisoner_action_container"></div>
                    </td>
                </tr>
            </table>
        </div>
    `;

    const actionContainer = document.getElementById("poisoner_action_container");

    if (screenContent === "truciciel_action_completed") {
        actionContainer.innerHTML = `
            <p style="text-align:center;">${data.truciciel_status}</p>
        `;
        return;
    }


    if (screenContent === "select_player_to_poison") {
        const title = "Wybierz gracza, którego chcesz otruć:";

        ChoiceComponent.render("poisoner_action_container", {
            id: "poisoner_selected_player",
            title: title,
            options: data.player_list,
            maxSelections: 1,
            onSubmit: (selected) => {
                if (!window.socket || typeof window.socket.send !== "function") {
                    console.warn("[night_truciciel] Socket not available for Truciciel choice send");
                    return;
                }

                window.socket.send({
                    type: "poisoner_night_choice",
                    selected_player: selected[0],
                    screen_content: screenContent
                });
            }
        });
        return;
    }

    actionContainer.innerHTML = `
        <p style="text-align:center;">${data.truciciel_status || ""}</p>
    `;
};
