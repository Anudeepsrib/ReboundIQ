document.addEventListener('DOMContentLoaded', restoreOptions);
document.getElementById('save').addEventListener('click', saveOptions);

function saveOptions() {
    const apiKey = document.getElementById('apiKey').value;

    chrome.storage.local.set({
        huntflowApiKey: apiKey
    }, () => {
        const status = document.getElementById('status');
        status.style.display = 'block';
        setTimeout(() => {
            status.style.display = 'none';
        }, 2000);
    });
}

function restoreOptions() {
    chrome.storage.local.get({
        huntflowApiKey: ''
    }, (items) => {
        document.getElementById('apiKey').value = items.huntflowApiKey;
    });
}
