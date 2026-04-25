window.Screens = window.Screens || {};

window.Screens["night_lokaj"] = function(state) {

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
                    <td colspan="2">
                        <div id="lokaj_action_container"></div>
                    </td>
                </tr>
            </table>
        </div>
    `;

    const actionContainer = document.getElementById("lokaj_action_container");

    if (screenContent === "lokaj_action_completed") {
        actionContainer.innerHTML = `
            <p style="text-align:center;">${data.lokaj_status}</p>
        `;
        return;
    }


    if (screenContent === "select_player") {
        const title = "Wybierz gracza, któremu chcesz służyć kolejnego dnia:";

        ChoiceComponent.render("lokaj_action_container", {
            id: "lokaj_selected_player",
            title: title,
            options: data.player_list,
            maxSelections: 1,
            onSubmit: (selected) => {
                if (!window.socket || typeof window.socket.send !== "function") {
                    console.warn("[night_lokaj] Socket not available for Lokaj choice send");
                    return;
                }

                window.socket.send({
                    type: "lokaj_night_choice",
                    selected_player: selected[0],
                    screen_content: screenContent
                });
            }
        });
        return;
    }

    actionContainer.innerHTML = `
        <p style="text-align:center;">${data.lokaj_status || ""}</p>
    `;
};
