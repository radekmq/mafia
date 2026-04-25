const Renderer = {

    renderStatus(state) {
        if (window.GameStatusComponent && typeof window.GameStatusComponent.render === "function") {
            window.GameStatusComponent.render(state);
            return;
        }

        const gameStatus = document.getElementById("game_status");
        if (gameStatus) {
            gameStatus.innerHTML = "";
        }
    },

    renderContent(html) {
        document.getElementById("game_content").innerHTML = html;
    },


    renderAdmin(state) {
        if (window.AdminStatusComponent && typeof window.AdminStatusComponent.render === "function") {
            window.AdminStatusComponent.render(state);
            return;
        }

        const adminPanel = document.getElementById("admin_panel");
        if (adminPanel) {
            adminPanel.innerHTML = "";
        }
    },
};
