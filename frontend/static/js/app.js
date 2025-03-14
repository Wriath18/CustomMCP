/**
 * Custom MCP Frontend Application
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const queryForm = document.getElementById('query-form');
    const queryInput = document.getElementById('query-input');
    const submitBtn = document.getElementById('submit-btn');
    const conversation = document.getElementById('conversation');
    const gmailStatus = document.getElementById('gmail-status');
    const githubStatus = document.getElementById('github-status');
    const openaiStatus = document.getElementById('openai-status');

    // Check services status on page load
    checkServicesStatus();

    // Event Listeners
    queryForm.addEventListener('submit', handleQuerySubmit);

    /**
     * Handle query form submission
     * @param {Event} e - Form submit event
     */
    async function handleQuerySubmit(e) {
        e.preventDefault();
        
        const query = queryInput.value.trim();
        if (!query) return;
        
        // Disable input while processing
        setFormState(false);
        
        // Add user message to conversation
        addMessageToConversation('user', query);
        
        // Add loading message
        const loadingMessage = addLoadingMessage();
        
        try {
            // Send query to API
            const response = await sendQuery(query);
            
            // Remove loading message
            loadingMessage.remove();
            
            // Add system response to conversation
            addMessageToConversation('system', response.response, response.actions_taken);
        } catch (error) {
            // Remove loading message
            loadingMessage.remove();
            
            // Add error message
            addMessageToConversation('system', `Sorry, I encountered an error: ${error.message}`);
        } finally {
            // Re-enable input
            setFormState(true);
            
            // Clear input
            queryInput.value = '';
        }
    }

    /**
     * Send query to API
     * @param {string} query - User query
     * @returns {Promise<Object>} - API response
     */
    async function sendQuery(query) {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to process query');
        }
        
        return await response.json();
    }

    /**
     * Add a message to the conversation
     * @param {string} type - Message type ('user' or 'system')
     * @param {string} content - Message content
     * @param {string[]} [actions] - Actions taken (for system messages)
     */
    function addMessageToConversation(type, content, actions = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Convert newlines to <br> and handle basic markdown
        const formattedContent = content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        contentDiv.innerHTML = `<p>${formattedContent}</p>`;
        
        // Add actions list for system messages
        if (type === 'system' && actions && actions.length > 0) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'actions-list';
            
            const actionsTitle = document.createElement('h4');
            actionsTitle.textContent = 'Actions Taken:';
            actionsDiv.appendChild(actionsTitle);
            
            const actionsList = document.createElement('ul');
            actions.forEach(action => {
                const actionItem = document.createElement('li');
                actionItem.textContent = action;
                actionsList.appendChild(actionItem);
            });
            
            actionsDiv.appendChild(actionsList);
            contentDiv.appendChild(actionsDiv);
        }
        
        messageDiv.appendChild(contentDiv);
        conversation.appendChild(messageDiv);
        
        // Scroll to bottom
        conversation.scrollTop = conversation.scrollHeight;
        
        return messageDiv;
    }

    /**
     * Add a loading message to the conversation
     * @returns {HTMLElement} - The loading message element
     */
    function addLoadingMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        
        contentDiv.appendChild(loadingDiv);
        messageDiv.appendChild(contentDiv);
        conversation.appendChild(messageDiv);
        
        // Scroll to bottom
        conversation.scrollTop = conversation.scrollHeight;
        
        return messageDiv;
    }

    /**
     * Set form state (enabled/disabled)
     * @param {boolean} enabled - Whether the form should be enabled
     */
    function setFormState(enabled) {
        queryInput.disabled = !enabled;
        submitBtn.disabled = !enabled;
        
        if (!enabled) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        } else {
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }

    /**
     * Check the status of all services
     */
    async function checkServicesStatus() {
        try {
            const response = await fetch('/api/services/status');
            
            if (!response.ok) {
                throw new Error('Failed to check services status');
            }
            
            const statusData = await response.json();
            
            // Update Gmail status
            updateServiceStatus(gmailStatus, statusData.gmail);
            
            // Update GitHub status
            updateServiceStatus(githubStatus, statusData.github);
            
            // Update OpenAI status
            updateServiceStatus(openaiStatus, statusData.openai);
        } catch (error) {
            console.error('Error checking services status:', error);
            
            // Set all services to error state
            updateServiceStatus(gmailStatus, { status: 'error', message: 'Failed to check status' });
            updateServiceStatus(githubStatus, { status: 'error', message: 'Failed to check status' });
            updateServiceStatus(openaiStatus, { status: 'error', message: 'Failed to check status' });
        }
    }

    /**
     * Update service status display
     * @param {HTMLElement} element - Status element
     * @param {Object} status - Status data
     */
    function updateServiceStatus(element, status) {
        const iconElement = element.querySelector('i');
        const textElement = element.querySelector('span');
        
        if (status.status === 'connected') {
            element.className = 'status-item connected';
            textElement.textContent = getServiceName(element) + ': Connected';
        } else {
            element.className = 'status-item error';
            textElement.textContent = getServiceName(element) + ': Error - ' + status.message;
        }
    }

    /**
     * Get service name from status element
     * @param {HTMLElement} element - Status element
     * @returns {string} - Service name
     */
    function getServiceName(element) {
        if (element.id === 'gmail-status') return 'Gmail';
        if (element.id === 'github-status') return 'GitHub';
        if (element.id === 'openai-status') return 'OpenAI';
        return 'Unknown';
    }
}); 