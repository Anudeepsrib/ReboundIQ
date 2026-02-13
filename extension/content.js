// JobNova - LinkedIn Integration

// Wait for page load
window.addEventListener('load', () => {
    // Use MutationObserver because LinkedIn is a SPA
    const observer = new MutationObserver((mutations) => {
        checkForMessageInput();
    });

    observer.observe(document.body, { childList: true, subtree: true });
});

let activePanel = null;

function checkForMessageInput() {
    const messageForm = document.querySelector('.msg-form__contenteditable');
    const sendButtonContainer = document.querySelector('.msg-form__footer-actions');

    if (messageForm && sendButtonContainer && !document.getElementById('jobnova-btn')) {
        injectButton(sendButtonContainer);
    }
}

function injectButton(container) {
    const btn = document.createElement('button');
    btn.id = 'jobnova-btn';
    btn.innerHTML = '<span>✨</span> AI Reply';
    
    // Style matches LinkedIn buttons but stands out
    btn.style.cssText = `
        background: transparent;
        color: #0a66c2;
        border: 1px solid #0a66c2;
        padding: 5px 12px;
        border-radius: 16px;
        margin-right: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 4px;
        transition: background 0.2s;
    `;

    btn.onmouseover = () => {
        btn.style.background = 'rgba(10, 102, 194, 0.1)';
    };
    btn.onmouseout = () => {
        btn.style.background = 'transparent';
    };

    btn.onclick = async (e) => {
        e.preventDefault();
        
        // Remove existing panel if open
        if (activePanel) activePanel.remove();

        // Show loading state
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="jobnova-spinner" style="display:inline-block; width:12px; height:12px; border-width:2px;"></span> Analyzing...';
        btn.disabled = true;

        try {
            const data = await analyzeThread();
            showPanel(data, document.querySelector('.msg-form__contenteditable'));
        } catch (error) {
            alert("JobNova Error: " + error.message);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    };

    container.insertBefore(btn, container.firstChild);
}

async function analyzeThread() {
    // Scrape valid message from other person
    const messages = document.querySelectorAll('.msg-s-message-list__event');
    let lastMessageText = "";
    
    for (let i = messages.length - 1; i >= 0; i--) {
        const msg = messages[i];
        if (!msg.classList.contains('msg-s-message-list__event--me')) {
            lastMessageText = msg.innerText;
            break;
        }
    }

    if (!lastMessageText) {
        throw new Error("No recent message found from recruiter.");
    }

    // Attempt to find Sender Name
    // This is fragile and depends on LinkedIn DOM structure
    let senderName = "Recruiter";
    try {
        const header = document.querySelector('.msg-entity-lockup__entity-title');
        if (header) senderName = header.innerText.split('\n')[0];
    } catch (e) { console.log("Could not find sender name"); }

    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage({
            action: "analyze_message",
            data: {
                message_text: lastMessageText,
                sender_name: senderName,
                company_name: "", 
                desired_tone: "professional"
            }
        }, (response) => {
            if (response.error) reject(new Error(response.error));
            else resolve(response.data);
        });
    });
}

function showPanel(data, targetElement) {
    const panel = document.createElement('div');
    panel.className = 'jobnova-panel';
    panel.innerHTML = `
        <div class="jobnova-panel-header">
            <h3>JobNova AI Assistant</h3>
            <button class="jobnova-close-btn">&times;</button>
        </div>
        <div class="jobnova-panel-content">
            <div class="jobnova-analysis">
                <strong>Analysis</strong>
                <span>${data.analysis || "Intent detected."}</span>
            </div>
            
            ${data.company_research ? `
            <div class="jobnova-research">
                <h4>Company Context</h4>
                <p>${data.company_research}</p>
            </div>` : ''}

            <div class="jobnova-responses">
                <h4>Suggested Reply</h4>
                <div class="jobnova-response">
                    <div class="jobnova-response-text" contenteditable="true">${data.suggested_reply}</div>
                    <div class="jobnova-actions">
                        <button class="jobnova-btn jobnova-btn-secondary" id="jobnova-copy">Copy</button>
                        <button class="jobnova-btn jobnova-btn-primary" id="jobnova-insert">Insert</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Position the panel
    if (targetElement) {
        const rect = targetElement.getBoundingClientRect();
        panel.style.top = `${rect.top - 450}px`; // crude positioning above input
        panel.style.left = `${rect.left}px`;
        panel.style.zIndex = '100000'; // high z-index
    }

    // Event Listeners
    panel.querySelector('.jobnova-close-btn').onclick = () => panel.remove();
    
    panel.querySelector('#jobnova-copy').onclick = () => {
        const text = panel.querySelector('.jobnova-response-text').innerText;
        navigator.clipboard.writeText(text);
        const btn = panel.querySelector('#jobnova-copy');
        btn.innerText = 'Copied!';
        setTimeout(() => btn.innerText = 'Copy', 1500);
    };

    panel.querySelector('#jobnova-insert').onclick = () => {
        if (targetElement) {
            const text = panel.querySelector('.jobnova-response-text').innerText;
            targetElement.innerText = text;
            targetElement.dispatchEvent(new Event('input', { bubbles: true }));
            panel.remove();
        }
    };

    document.body.appendChild(panel);
    activePanel = panel;
}
