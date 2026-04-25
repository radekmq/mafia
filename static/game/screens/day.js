window.Screens = window.Screens || {};

window.Screens["day_discussion"] = function(state) {

    Renderer.renderContent(`
        <div class="container">
            <p>Jesteś w fazie dnia, udanych dyskusji.</p>
        </div>
    `);
};

window.Screens["day_nomination"] = function(data) {

    const container = document.getElementById("game_content");
    if (!container) return;

    const options = (data.voting_system.alive_nomination_options || []).map(player => [
        `${player.name} (miejsce: ${player.seat_no})`,
        player.client_id
    ]);

    const nominatedRows = (data.voting_system.nominated_players || []).map(player => `
        <tr>
            <td>${player.name}</td>
            <td>${player.votes}</td>
        </tr>
    `).join("");

    const screenContent = data.voting_system.screen_content;

    if (screenContent === "nomination_panel") {
        Renderer.renderContent(`
            <div class="container">
                <h3>Nominacja do egzekucji:</h3>
                <div id="nomination_choice"></div>
                    ${options.length === 0 ? `
                        <p style="text-align:center;">Brak dostępnych graczy do nominacji.</p>
                    ` : ""}
                </div>
            </div></br>
            <div class="container">
                <h3>Dotychczasowe nominacje</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Gracz</th>
                            <th>Liczba głosów</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${nominatedRows || `
                            <tr>
                                <td colspan="2">Brak nominacji.</td>
                            </tr>
                        `}
                    </tbody>
                </table>
            </div>
        `);
    } else {
        Renderer.renderContent(`
            <div class="container">
                <p style="text-align:center;">"Niestety nie możesz nominować gracza do egzekucji."</p>
            </div>
            `);
    }


    if (screenContent !== "nomination_panel") {
        return;
    }

    const choiceComponent = window.ChoiceComponent || (typeof ChoiceComponent !== "undefined" ? ChoiceComponent : null);
    if (!choiceComponent || typeof choiceComponent.render !== "function") {
        console.warn("[day_nomination] ChoiceComponent not available");
        return;
    }

    choiceComponent.render("nomination_choice", {
        id: "nominate_to_execute",
        title: "Nominuj gracza do egzekucji:",
        maxSelections: 1,
        options,
        onSubmit: (selected) => {
            if (!window.socket || typeof window.socket.send !== "function") {
                console.warn("[day_nomination] Socket not available for nominate_execute send");
                return;
            }

            window.socket.send({
                type: "nominate_execute",
                selected_player: selected[0],
            });
        },
    });
};

window.Screens["day_voting"] = function(data) {
    const container = document.getElementById("game_content");
    if (!container) return;

    const votingSystem = data.voting_system || {};
    const activeVoterId = votingSystem.voter_id || null;
    const activeVoterName = votingSystem.voter_name || null;
    const votersStatus = votingSystem.voters_status || [];
    const activeNomineeName = (votingSystem.active_nominee) || "Nikt";
    const allowedToVoteYes = votingSystem.allowed_to_vote_yes !== false;

    const voteRows = votersStatus.map(player => {
        return `
            <tr>
                <td>${player.name}</td>
                <td>${player.status || "-"}</td>
            </tr>
        `;
    }).join("");

    const screenContent = votingSystem.screen_content;

    if (screenContent === "voting_panel") {
        Renderer.renderContent(`
            <div class="container">
                <p style="text-align:center;">
                    Aktualnie głosuje: ${activeVoterName || "-"}
                </p>
                <div id="vote_choice"></div>
            </div>
            <br>
            <div class="container">
                <h3>Aktualny status głosowania</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Gracz</th>
                            <th>Liczba głosów</th>
                        </tr>
                    </thead>
                    <tbody>${voteRows}</tbody>
                </table>
            </div>
        `);
    } else {
        Renderer.renderContent(`
            <div class="container">
                <p style="text-align:center;">"Niestety w tej chwili nie możesz głosować."</p>
            </div>
            </br>
            <div class="container">
                <h3>Aktualny status głosowania</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Gracz</th>
                            <th>Liczba głosów</th>
                        </tr>
                    </thead>
                    <tbody>${voteRows}</tbody>
                </table>
            </div>
            `);
    }

    const voteChoiceContainer = document.getElementById("vote_choice");
    if (!voteChoiceContainer) {
        console.warn("[day_voting] Missing #vote_choice container");
        return;
    }

    const choiceComponent = window.ChoiceComponent || (typeof ChoiceComponent !== "undefined" ? ChoiceComponent : null);
    if (!choiceComponent || typeof choiceComponent.render !== "function") {
        console.warn("[day_voting] ChoiceComponent not available");
        return;
    }

    choiceComponent.render("vote_choice", {
        id: "vote_for_nominee",
        title: `Głosuj aby wyeliminować gracza: ${activeNomineeName}`,
        maxSelections: 1,
        options: allowedToVoteYes
            ? [
                ["Głosuję za", true],
                ["Wstrzymuję się od głosu", false],
            ]
            : [
                ["Wstrzymuję się od głosu", false],
            ],
        onSubmit: (selected) => {
            if (!window.socket || typeof window.socket.send !== "function") {
                console.warn("[day_voting] Socket not available for vote_execute send");
                return;
            }

            window.socket.send({
                type: "vote_execute",
                vote: selected[0],
            });
        },
    });
};

window.Screens["day_execution"] = function(state) {
    const nominatedPlayers = state.voting_system.nominated_players || [];
    const voteRows = nominatedPlayers.map(player => {
        return `
            <tr>
                <td>${player.name}</td>
                <td>${player.votes || "-"}</td>
            </tr>
        `;
    }).join("");

    Renderer.renderContent(`
        <div class="container">
            <h3>Podsumowanie głosowania</h3>
            <p style="text-align:center;">${state.voting_system.execution_message || "-"}</p>
            <table>
                <thead>
                    <tr>
                        <th>Gracz</th>
                        <th>Liczba głosów</th>
                    </tr>
                </thead>
                <tbody>${voteRows}</tbody>
            </table>
        </div>
    `);
};
