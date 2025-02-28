function loadConfigFile() {
    const configData = fetch('/api/settingFile/')
        .then(response => response.json())
        .then(data => {
            console.log('configData:', data);
            generateConfigUI(data);
            addEventListeners();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
document.addEventListener('DOMContentLoaded', loadConfigFile);

function generateConfigUI(config) {
    const disabled_keys = ['BIRDNET_VERSION', 'BIRDNET_UI_VERSION', 'BIRDNET_ADDRESS', 'BIRDNET_PORT', 'BIRDNET_WS_PORT'];

    const form = document.getElementById('config-form');
    for (const key in config) {
        if (config.hasOwnProperty(key)) {
            const label = document.createElement('label');
            label.textContent = key;
            const input = document.createElement('input');
            input.type = 'text';
            input.name = key;
            input.value = config[key];
            // Disable input if the key is in disabled_keys
            if (disabled_keys.includes(key)) {
                input.disabled = true;
            }
            form.appendChild(label);
            form.appendChild(input);
            form.appendChild(document.createElement('br'));
        }
    }
}

function addEventListeners() {
    document.getElementById('save-settings-button').addEventListener('click', function() {
        const formData = new FormData(document.getElementById('config-form'));
        const configObject = {};
    formData.forEach((value, key) => {
        configObject[key] = value;
    });

    fetch('/update_config/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(configObject),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
    })
    .catch(error => {
            console.error('Error:', error);
        });
    });

}