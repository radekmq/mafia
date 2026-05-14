window.Screens = window.Screens || {};

window.Screens["night_mnich"] = function(state) {

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
                        <div id="mnich_action_container"></div>
                    </td>
                </tr>
            </table>
        </div>
    `;

    const actionContainer = document.getElementById("mnich_action_container");

    if (screenContent === "mnich_action_completed") {
        actionContainer.innerHTML = `
            <p style="text-align:center;">${data.mnich_status}</p>
        `;
        return;
    }

    if (screenContent === "confirm_first_night_action") {
        actionContainer.innerHTML = `
            <p style="text-align:center;">${data.mnich_status}</p>
            <div style="text-align:center; margin-top:10px;">
                <button id="confirm_mnich_first_night" type="button">OK</button>
            </div>
        `;

        document.getElementById("confirm_mnich_first_night").onclick = () => {
            if (!window.socket || typeof window.socket.send !== "function") {
                console.warn("[night_mnich] Socket not available for Mnich confirmation send");
                return;
            }

            window.socket.send({
                type: "confirm_night_action",
                confirmed_night_action: true,
            });
        };
        return;
    }


    if (screenContent === "select_player") {
        const title = "Wybierz gracza, którego chcesz ochraniać przed Demonem:";

        ChoiceComponent.render("mnich_action_container", {
            id: "mnich_selected_player",
            title: title,
            options: data.player_list,
            maxSelections: 1,
            onSubmit: (selected) => {
                if (!window.socket || typeof window.socket.send !== "function") {
                    console.warn("[night_mnich] Socket not available for Mnich choice send");
                    return;
                }

                window.socket.send({
                    type: "mnich_night_choice",
                    selected_player: selected[0],
                    screen_content: screenContent
                });
            }
        });
        return;
    }

    actionContainer.innerHTML = `
        <p style="text-align:center;">${data.mnich_status || ""}</p>
    `;
};
