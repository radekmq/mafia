window.Screens = window.Screens || {};

Screens.lobby = function(state) {

    Renderer.renderContent(`
        <div class="container">
            <p>Oczekiwanie na graczy...</p>
        </div>
    `);
};
