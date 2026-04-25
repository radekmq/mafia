window.Screens = window.Screens || {};

window.Screens["game_over"] = function(state) {

    const container = document.getElementById("game_content");
    if (!container) return;

    const data = state;

    container.innerHTML = `
        <div class="container" style="overflow-x:auto;">
            <h4 style="text-align:center; margin-top:0;">KONIEC GRY</h4>
            <p style="text-align:center;">
                Zwycięska drużyna: ${data.winning_team}
            </p>
        </div>
    `;
};
