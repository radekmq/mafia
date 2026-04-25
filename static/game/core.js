window.Screens = window.Screens || {};

window.UI = {

    state: {},

    setState(state) {
        this.state = state;
        this.render();
    },

    render() {
        Renderer.renderStatus(this.state);

        const screenName = this.state.screen || "default";
        const screenFn = window.Screens[screenName] || window.Screens["default"];

        console.log("[UI] render screen:", screenName);

        if (typeof screenFn !== "function") {
            console.error("[UI] Missing screen renderer:", screenName, window.Screens);
            Renderer.renderContent("<p>Błąd renderowania widoku</p>");
            return;
        }

        try {
            screenFn(this.state);
        } catch (err) {
            console.error("Błąd screena:", screenName, err);
            Renderer.renderContent("<p>Błąd renderowania widoku</p>");
        }

        Renderer.renderAdmin(this.state);
    }
};
