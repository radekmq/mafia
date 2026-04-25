const ChoiceComponent = {

    render(containerId, config) {

        const {
            id,
            title,
            maxSelections,
            options,
            endpoint,        // opcjonalne (POST)
            onSubmit         // opcjonalne (socket)
        } = config;

        let selected = [];

        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`[ChoiceComponent] Missing container: #${containerId}`);
            return;
        }

        container.innerHTML = `
            <form id="${id}_form">
                <div id="${id}_wrapper" class="choice-container">

                    ${title ? `<h3>${title}</h3>` : ""}

                    <p id="${id}_status"></p>

                    <div id="${id}_options" class="options"></div>

                    <button id="${id}_confirm" type="button" class="inactive-btn" disabled>
                        Zatwierdź wybór
                    </button>

                    <div id="${id}_success" class="success-msg"></div>
                </div>

                <div id="${id}_hidden_selected"></div>
            </form>
        `;

        const optionsContainer = document.getElementById(`${id}_options`);
        const status = document.getElementById(`${id}_status`);
        const confirmButton = document.getElementById(`${id}_confirm`);
        const hiddenContainer = document.getElementById(`${id}_hidden_selected`);
        const successBox = document.getElementById(`${id}_success`);

        // =========================
        // 🔧 HELPERY (1:1 z Twojego kodu)
        // =========================

        function serializeValue(value) {
            return JSON.stringify(value);
        }

        function normalizeOption(option) {
            if (Array.isArray(option)) {
                const display = option[0];
                const value = option.length > 1 ? option[1] : option[0];
                return { display: String(display), value };
            }

            if (option && typeof option === "object") {
                const display = option.display ?? option.label ?? option.text ?? option.name ?? option.value;
                const value = option.value ?? option.id ?? option.key ?? option.name ?? display;
                return { display: String(display), value };
            }

            return { display: String(option), value: option };
        }

        const normalizedOptions = (options || []).map(normalizeOption);

        // =========================
        // 🔁 RENDER
        // =========================

        function renderOptions() {
            optionsContainer.innerHTML = "";

            normalizedOptions.forEach(option => {
                const div = document.createElement("div");
                div.classList.add("option");
                div.innerText = option.display;
                div.dataset.optionKey = serializeValue(option.value);

                div.onclick = () => handleClick(option.value, div);

                optionsContainer.appendChild(div);
            });

            updateStatus();
        }

        // =========================
        // 🧠 LOGIKA WYBORU
        // =========================

        function handleClick(option, element) {
            const isSelected = selected.some(o => serializeValue(o) === serializeValue(option));

            if (isSelected) {
                selected = selected.filter(o => serializeValue(o) !== serializeValue(option));
                element.classList.remove("selected");
            } else {
                if (selected.length >= maxSelections) return;

                selected.push(option);
                element.classList.add("selected");
            }

            updateStatus();
            updateDisabled();
            updateConfirmButton();
        }

        function updateStatus() {
            status.innerText = `Wybrane: ${selected.length} / ${maxSelections}`;
        }

        function updateConfirmButton() {
            confirmButton.disabled = selected.length !== maxSelections;
        }

        function updateDisabled() {
            const allOptions = optionsContainer.querySelectorAll(".option");

            allOptions.forEach(el => {
                const key = el.dataset.optionKey;

                const isSelected = selected.some(item => serializeValue(item) === key);

                if (!isSelected && selected.length >= maxSelections) {
                    el.classList.add("disabled");
                } else {
                    el.classList.remove("disabled");
                }
            });
        }

        // =========================
        // 📦 SUBMIT (POST / SOCKET)
        // =========================

        function buildHiddenInputs() {
            hiddenContainer.innerHTML = "";

            selected.forEach(item => {
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = "selected";
                input.value = serializeValue(item);
                hiddenContainer.appendChild(input);
            });

            const jsonInput = document.createElement("input");
            jsonInput.type = "hidden";
            jsonInput.name = "selected_json";
            jsonInput.value = JSON.stringify(selected);
            hiddenContainer.appendChild(jsonInput);
        }

        function showSuccess(msg) {
            successBox.innerText = msg;
            successBox.style.display = "block";
        }

        function sendSelection() {
            if (selected.length !== maxSelections) return;

            confirmButton.disabled = true;

            // 🔹 tryb socket
            if (onSubmit) {
                onSubmit(selected);
                showSuccess("Wysłano!");
                return;
            }

            // 🔹 tryb POST (jak u Ciebie)
            if (endpoint) {
                buildHiddenInputs();

                fetch(endpoint, {
                    method: "POST",
                    body: new FormData(container.querySelector("form"))
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "ok") {
                        showSuccess("Zapisano!");
                    } else {
                        showSuccess("Błąd");
                    }
                })
                .catch(() => {
                    showSuccess("Błąd połączenia");
                });
            }
        }

        confirmButton.onclick = sendSelection;

        // =========================
        // 🚀 INIT
        // =========================

        renderOptions();
        updateDisabled();
        updateConfirmButton();
    }
};

window.ChoiceComponent = ChoiceComponent;
