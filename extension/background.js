// Background Service Worker
const API_URL = "http://localhost:8000/api/v1/assistant";

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyze_message") {
        handleAnalyzeMessage(request.data, sendResponse);
        return true; // Indicates async response
    }
});

async function handleAnalyzeMessage(data, sendResponse) {
    try {
        // 1. Get API Key
        const { huntflowApiKey } = await chrome.storage.local.get("huntflowApiKey");

        if (!huntflowApiKey) {
            sendResponse({ error: "API Key missing. Please set it in Extension Options." });
            return;
        }

        // 2. Call API
        const response = await fetch(`${API_URL}/analyze_message`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-KEY": huntflowApiKey
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorText = await response.text();
            sendResponse({ error: `API Error: ${response.status} - ${errorText}` });
            return;
        }

        const result = await response.json();
        sendResponse({ success: true, data: result });

    } catch (error) {
        sendResponse({ error: `Network/Script Error: ${error.message}` });
    }
}
