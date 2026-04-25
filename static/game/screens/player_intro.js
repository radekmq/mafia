window.Screens = window.Screens || {};

window.Screens["players_introduction"] = function(state) {

    const container = document.getElementById("game_content");
    if (!container) return;

    const data = state.character_data;

    container.innerHTML = `
        <div class="container" style="overflow-x:auto;">

            <h3 style="text-align:center; margin-top:0;">
                Twoja postać: ${data.role_name}
            </h3>

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
            </table>

        </div>
    `;
};
