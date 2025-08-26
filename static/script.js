// Global state
let currentUser = null;
let authToken = null;
let currentSessionId = null;
let sessions = [];
let otpData = null; // Store OTP verification data
let otpTimer = null; // OTP countdown timer

// API wrapper with automatic logout on 401
async function apiFetch(input, init) {
    if (!init) init = {};
    if (!init.headers) init.headers = {};

    const token = localStorage.getItem('authToken');
    if (token) {
        init.headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(input, init);

    if (response.status === 401) {
        handleUnauthorized();
        return response;
    }

    return response;
}

function handleUnauthorized() {
    console.log('🔒 Session expired or unauthorized - logging out');
    logout();
    showToast('⏰ Your session has expired. Please log in again.', 'error');
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    setupEventListeners();
    console.log('🎉 Medical RAG Chatbot loaded!');
});

// Authentication functions
function checkAuthStatus() {
    const token = localStorage.getItem('authToken');
    const user = localStorage.getItem('currentUser');
    
    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);
        showChatInterface();
    } else {
        showAuthInterface();
    }
}

function showAuthInterface() {
    document.getElementById('auth-screen').style.display = 'flex';
    document.getElementById('chat-screen').style.display = 'none';
    showRoleSelection();
    console.log('👤 Showing authentication screen');
}

function showChatInterface() {
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('chat-screen').style.display = 'flex';
    
    // Update user info in header
    document.getElementById('userName').textContent = currentUser.full_name || currentUser.email;
    const userRoleEl = document.getElementById('userRole');
    userRoleEl.textContent = currentUser.role === 'professional' ? 'Medical Professional' : 'General User';
    userRoleEl.className = `user-role ${currentUser.role}`;
    
    // Show appropriate UI based on user role
    updateUIForUserRole();
    loadSessions();
    checkIndexStatus();
    console.log('💬 Showing chat interface for:', currentUser.email, 'Role:', currentUser.role);
}

function updateUIForUserRole() {
    const uploadSection = document.getElementById('uploadSection');
    const roleInfoSection = document.getElementById('roleInfoSection');
    const welcomeText = document.getElementById('welcomeText');
    
    if (currentUser.role === 'professional') {
        // Show upload section for professionals
        uploadSection.style.display = 'block';
        roleInfoSection.style.display = 'none';
        welcomeText.textContent = 'Upload PDF documents and ask questions about medical information.';
    } else {
        // Show role info for general users
        uploadSection.style.display = 'none';
        roleInfoSection.style.display = 'block';
        welcomeText.textContent = 'Ask questions about medical information from documents uploaded by medical professionals.';
    }
}

// Navigation functions
function showRoleSelection() {
    hideAllForms();
    document.getElementById('role-selection').style.display = 'block';
}

function showLogin() {
    hideAllForms();
    document.getElementById('login-form').style.display = 'block';
}

function showGeneralRegister() {
    hideAllForms();
    document.getElementById('general-register-form').style.display = 'block';
}

function showProfessionalRegister() {
    hideAllForms();
    document.getElementById('professional-register-form').style.display = 'block';
}

function showOTPVerification() {
    hideAllForms();
    document.getElementById('otp-verification-form').style.display = 'block';
    
    // Display phone number
    if (otpData && otpData.phone_number) {
        document.getElementById('otpPhoneDisplay').textContent = otpData.phone_number;
    }
    
    // Start countdown timer
    startOTPTimer();
    
    // Clear OTP input and focus
    document.getElementById('otpCode').value = '';
    document.getElementById('otpCode').focus();
}

function hideAllForms() {
    document.getElementById('role-selection').style.display = 'none';
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('general-register-form').style.display = 'none';
    document.getElementById('professional-register-form').style.display = 'none';
    document.getElementById('otp-verification-form').style.display = 'none';
}

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    authToken = null;
    currentUser = null;
    currentSessionId = null;
    sessions = [];
    otpData = null;
    clearOTPTimer();
    showAuthInterface();
    showToast('👋 Logged out successfully!', 'success');
}

// Event listeners
function setupEventListeners() {
    // Role selection buttons
    document.getElementById('generalUserBtn').addEventListener('click', showGeneralRegister);
    document.getElementById('professionalUserBtn').addEventListener('click', showProfessionalRegister);
    
    // Navigation links
    document.getElementById('showLoginLink').addEventListener('click', (e) => {
        e.preventDefault();
        showLogin();
    });
    document.getElementById('showRoleSelectionFromLogin').addEventListener('click', (e) => {
        e.preventDefault();
        showRoleSelection();
    });
    document.getElementById('switchToProfessional').addEventListener('click', (e) => {
        e.preventDefault();
        showProfessionalRegister();
    });
    document.getElementById('switchToGeneral').addEventListener('click', (e) => {
        e.preventDefault();
        showGeneralRegister();
    });
    document.getElementById('showLoginFromGeneral').addEventListener('click', (e) => {
        e.preventDefault();
        showLogin();
    });
    document.getElementById('showLoginFromProfessional').addEventListener('click', (e) => {
        e.preventDefault();
        showLogin();
    });
    document.getElementById('backToProfessionalRegister').addEventListener('click', (e) => {
        e.preventDefault();
        clearOTPTimer();
        showProfessionalRegister();
    });
    
    // Auth forms
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('generalRegisterForm').addEventListener('submit', handleGeneralRegister);
    document.getElementById('professionalRegisterForm').addEventListener('submit', handleProfessionalRegister);
    document.getElementById('otpVerificationForm').addEventListener('submit', handleOTPVerification);
    
    // OTP buttons
    document.getElementById('resendOtpBtn').addEventListener('click', handleResendOTP);
    
    // Chat interface buttons
    document.getElementById('logoutBtn').addEventListener('click', logout);
    document.getElementById('newSessionBtn').addEventListener('click', createNewSession);
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    
    // Upgrade button for general users
    document.getElementById('upgradeBtn').addEventListener('click', logout);
    
    // Chat input
    const questionInput = document.getElementById('questionInput');
    questionInput.addEventListener('input', handleInputChange);
    questionInput.addEventListener('keydown', handleKeyPress);
    
    // File upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => {
        if (currentUser && currentUser.role === 'professional') {
            fileInput.click();
        } else {
            showToast('⚠️ Only medical professionals can upload files', 'error');
        }
    });
    
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleFileDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // OTP input formatting
    document.getElementById('otpCode').addEventListener('input', handleOTPInput);
}

// OTP functions
function startOTPTimer() {
    let timeLeft = 300; // 5 minutes in seconds
    const timerElement = document.getElementById('otpTimer');
    
    clearOTPTimer(); // Clear any existing timer
    
    otpTimer = setInterval(() => {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        if (timeLeft <= 0) {
            clearOTPTimer();
            timerElement.textContent = 'Expired';
            document.getElementById('verifyOtpBtn').disabled = true;
            showToast('⏰ OTP has expired. Please request a new one.', 'error');
        }
        
        timeLeft--;
    }, 1000);
}

function clearOTPTimer() {
    if (otpTimer) {
        clearInterval(otpTimer);
        otpTimer = null;
    }
}

function handleOTPInput(e) {
    // Only allow digits and limit to 6 characters
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 6) {
        value = value.substring(0, 6);
    }
    e.target.value = value;
    
    // Enable/disable verify button
    document.getElementById('verifyOtpBtn').disabled = value.length !== 6;
}

// Auth handlers - UPDATED to use apiFetch
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    console.log('🔐 Attempting login for:', email);
    
    try {
        const response = await apiFetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showChatInterface();
            showToast(`✅ Welcome back, ${currentUser.full_name || currentUser.email}!`, 'success');
        } else {
            showToast('❌ ' + (data.detail || 'Login failed'), 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('🌐 Network error during login', 'error');
    }
}

async function handleGeneralRegister(e) {
    e.preventDefault();
    const fullName = document.getElementById('generalFullName').value;
    const email = document.getElementById('generalEmail').value;
    const password = document.getElementById('generalPassword').value;
    
    console.log('📝 Attempting general registration for:', email);
    
    try {
        const response = await apiFetch('/auth/register/general', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                full_name: fullName
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showChatInterface();
            showToast('🎉 Registration successful! Welcome to Medical RAG Chatbot!', 'success');
        } else {
            showToast('❌ ' + (data.detail || 'Registration failed'), 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('🌐 Network error during registration', 'error');
    }
}

async function handleProfessionalRegister(e) {
    e.preventDefault();
    const legalNo = document.getElementById('professionalLegalNo').value;
    const phoneNumber = document.getElementById('professionalPhone').value;
    const email = document.getElementById('professionalEmail').value;
    const password = document.getElementById('professionalPassword').value;
    
    console.log('👨‍⚕️ Requesting OTP for professional registration:', email);
    
    try {
        const response = await apiFetch('/auth/professional/request-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                legal_no: legalNo,
                phone_number: phoneNumber
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            otpData = {
                phone_number: data.phone_number,
                email: data.email
            };
            showOTPVerification();
            showToast(`📱 ${data.message}`, 'success');
        } else {
            showToast('❌ ' + (data.detail || 'Professional registration failed'), 'error');
        }
    } catch (error) {
        console.error('Professional registration error:', error);
        showToast('🌐 Network error during registration', 'error');
    }
}

async function handleOTPVerification(e) {
    e.preventDefault();
    const otpCode = document.getElementById('otpCode').value;
    
    if (!otpData) {
        showToast('❌ OTP verification data not found', 'error');
        return;
    }
    
    console.log('🔐 Verifying OTP for:', otpData.phone_number);
    
    try {
        const response = await apiFetch('/auth/professional/verify-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone_number: otpData.phone_number,
                email: otpData.email,
                otp_code: otpCode
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            clearOTPTimer();
            authToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showChatInterface();
            showToast(`🎉 Welcome Dr. ${currentUser.full_name}! Your account has been verified.`, 'success');
        } else {
            showToast('❌ ' + (data.detail || 'OTP verification failed'), 'error');
        }
    } catch (error) {
        console.error('OTP verification error:', error);
        showToast('🌐 Network error during OTP verification', 'error');
    }
}

async function handleResendOTP() {
    if (!otpData) {
        showToast('❌ OTP data not found', 'error');
        return;
    }
    
    const resendBtn = document.getElementById('resendOtpBtn');
    resendBtn.disabled = true;
    resendBtn.textContent = 'Sending...';
    
    try {
        const response = await apiFetch('/auth/professional/resend-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone_number: otpData.phone_number,
                email: otpData.email
            }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            startOTPTimer(); // Restart timer
            document.getElementById('verifyOtpBtn').disabled = false;
            document.getElementById('otpCode').value = '';
            showToast('📱 New OTP sent successfully!', 'success');
        } else {
            showToast('❌ ' + (data.detail || 'Failed to resend OTP'), 'error');
        }
    } catch (error) {
        console.error('Resend OTP error:', error);
        showToast('🌐 Network error during OTP resend', 'error');
    } finally {
        // Re-enable button after 30 seconds
        setTimeout(() => {
            resendBtn.disabled = false;
            resendBtn.textContent = 'Resend OTP';
        }, 30000);
    }
}

// Chat functions
function handleInputChange() {
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    const hasText = questionInput.value.trim().length > 0;
    sendBtn.disabled = !hasText || !authToken;
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const sendBtn = document.getElementById('sendBtn');
        if (!sendBtn.disabled) {
            sendMessage();
        }
    }
}

async function sendMessage() {
    const questionInput = document.getElementById('questionInput');
    const sendBtn = document.getElementById('sendBtn');
    const messagesContainer = document.getElementById('messagesContainer');
    const question = questionInput.value.trim();
    
    if (!question || !authToken) return;
    
    console.log('💬 Sending message:', question);
    
    // Clear input and disable
    questionInput.value = '';
    sendBtn.disabled = true;
    
    // Add user message to UI
    addMessage('user', question);
    
    // Show typing indicator
    const typingElement = addTypingIndicator();
    
    try {
        const response = await apiFetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                session_id: currentSessionId,
                top_k: 4,
                provider: 'auto'
            }),
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingElement);
        
        if (response.ok) {
            // Update current session ID
            currentSessionId = data.session_id;
            
            // Add assistant response
            addMessage('assistant', data.answer, data.citations);
            
            // Show limit warning if reached
            if (data.limit_reached) {
                showToast('⚠️ Session message limit reached. Start a new session to continue.', 'error');
            }
            
            // Refresh sessions list
            loadSessions();
        } else {
            addMessage('assistant', `❌ Error: ${data.detail || 'Failed to get response'}`);
            showToast('❌ ' + (data.detail || 'Failed to get response'), 'error');
        }
    } catch (error) {
        console.error('Send message error:', error);
        removeTypingIndicator(typingElement);
        addMessage('assistant', '🌐 Network error occurred. Please try again.');
        showToast('🌐 Network error occurred', 'error');
    }
    
    // Re-enable input
    handleInputChange();
}

function addMessage(role, content, citations = null) {
    const messagesContainer = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    messageDiv.appendChild(contentDiv);
    
    // Add citations if available
    if (citations && citations.length > 0) {
        const citationsDiv = document.createElement('div');
        citationsDiv.className = 'citations';
        
        const citationsTitle = document.createElement('h4');
        citationsTitle.textContent = '📚 Sources:';
        citationsDiv.appendChild(citationsTitle);
        
        citations.forEach(citation => {
            const citationItem = document.createElement('div');
            citationItem.className = 'citation-item';
            citationItem.textContent = `📄 ${citation.source} (Page ${citation.page}) - Score: ${citation.score.toFixed(3)}`;
            citationsDiv.appendChild(citationItem);
        });
        
        messageDiv.appendChild(citationsDiv);
    }
    
    // Remove welcome message if it exists
    const welcomeMessage = messagesContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator() {
    const messagesContainer = document.getElementById('messagesContainer');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <span>🤖 AI is thinking</span>
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return typingDiv;
}

function removeTypingIndicator(element) {
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}

// Session management - UPDATED to use apiFetch
async function loadSessions() {
    try {
        const response = await apiFetch('/sessions');
        
        if (response.ok) {
            sessions = await response.json();
            renderSessions();
        }
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

function renderSessions() {
    const sessionsList = document.getElementById('sessionsList');
    sessionsList.innerHTML = '';
    
    if (sessions.length === 0) {
        sessionsList.innerHTML = '<div style="text-align: center; color: #718096; padding: 1rem;">No sessions yet</div>';
        return;
    }
    
    sessions.forEach(session => {
        const sessionDiv = document.createElement('div');
        sessionDiv.className = `session-item ${currentSessionId === session.id ? 'active' : ''}`;
        sessionDiv.onclick = () => loadSession(session.id);
        
        sessionDiv.innerHTML = `
            <div class="session-title">${session.title}</div>
            <div class="session-time">${new Date(session.updated_at).toLocaleDateString()}</div>
        `;
        
        sessionsList.appendChild(sessionDiv);
    });
}

async function createNewSession() {
    console.log('➕ Creating new session');
    
    try {
        const response = await apiFetch('/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: 'New chat'
            }),
        });
        
        if (response.ok) {
            const newSession = await response.json();
            currentSessionId = newSession.id;
            
            // Clear messages
            clearMessages();
            
            // Reload sessions
            loadSessions();
            
            showToast('✅ New session created!', 'success');
        }
    } catch (error) {
        console.error('Failed to create new session:', error);
        showToast('❌ Failed to create new session', 'error');
    }
}

async function loadSession(sessionId) {
    console.log('📂 Loading session:', sessionId);
    
    try {
        const response = await apiFetch(`/sessions/${sessionId}`);
        
        if (response.ok) {
            const sessionData = await response.json();
            currentSessionId = sessionId;
            
            // Clear current messages
            clearMessages();
            
            // Load session messages
            sessionData.messages.forEach(message => {
                addMessage(message.role, message.content, message.citations);
            });
            
            // Update UI
            renderSessions();
        }
    } catch (error) {
        console.error('Failed to load session:', error);
        showToast('❌ Failed to load session', 'error');
    }
}

function clearMessages() {
    const messagesContainer = document.getElementById('messagesContainer');
    const welcomeMessage = currentUser && currentUser.role === 'professional' 
        ? 'Upload PDF documents and ask questions about medical information.'
        : 'Ask questions about medical information from documents uploaded by medical professionals.';
    
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <h2>🤖 Welcome to Medical RAG Chatbot</h2>
            <p>${welcomeMessage}</p>
        </div>
    `;
}

// File upload functions
function handleDragOver(e) {
    e.preventDefault();
    const uploadArea = document.getElementById('uploadArea');
    if (currentUser && currentUser.role === 'professional') {
        uploadArea.classList.add('dragover');
    }
}

function handleDragLeave(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.classList.remove('dragover');
    
    if (!currentUser || currentUser.role !== 'professional') {
        showToast('⚠️ Only medical professionals can upload files', 'error');
        return;
    }
    
    const files = Array.from(e.dataTransfer.files);
    uploadFiles(files);
}

function handleFileSelect(e) {
    if (!currentUser || currentUser.role !== 'professional') {
        showToast('⚠️ Only medical professionals can upload files', 'error');
        return;
    }
    
    const files = Array.from(e.target.files);
    uploadFiles(files);
}

async function uploadFiles(files) {
    if (!currentUser || currentUser.role !== 'professional') {
        showToast('⚠️ Only medical professionals can upload files', 'error');
        return;
    }
    
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    if (pdfFiles.length === 0) {
        showToast('❌ Please select PDF files only', 'error');
        return;
    }
    
    console.log('📄 Uploading', pdfFiles.length, 'PDF files');
    
    const uploadStatus = document.getElementById('uploadStatus');
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadStatus.innerHTML = '<div class="upload-info">📤 Uploading files...</div>';
    uploadArea.classList.add('loading');
    
    try {
        for (let file of pdfFiles) {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await apiFetch('/upload', {
                method: 'POST',
                body: formData,
            });
            
            const data = await response.json();
            
            if (response.ok) {
                uploadStatus.innerHTML = `<div class="upload-success">✅ ${file.name} uploaded successfully!</div>`;
            } else {
                uploadStatus.innerHTML = `<div class="upload-error">❌ ${data.detail || 'Failed to upload'}</div>`;
            }
        }
        
        // Check index status after upload
        checkIndexStatus();
        showToast(`🎉 ${pdfFiles.length} file(s) uploaded successfully!`, 'success');
        
    } catch (error) {
        console.error('Upload error:', error);
        uploadStatus.innerHTML = '<div class="upload-error">❌ Upload failed due to network error</div>';
        showToast('❌ Upload failed', 'error');
    } finally {
        uploadArea.classList.remove('loading');
        fileInput.value = ''; // Clear file input
    }
}

async function checkIndexStatus() {
    try {
        const response = await apiFetch('/health');
        const data = await response.json();
        const indexStatus = document.getElementById('indexStatus');
        
        if (data.index_exists) {
            indexStatus.textContent = '📚 Knowledge base ready';
            indexStatus.className = 'index-ready';
            const questionInput = document.getElementById('questionInput');
            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = !questionInput.value.trim();
        } else {
            const statusText = currentUser && currentUser.role === 'professional' 
                ? '⚠️ No documents uploaded yet' 
                : '⚠️ Waiting for medical professionals to upload documents';
            indexStatus.textContent = statusText;
            indexStatus.className = 'index-missing';
        }
    } catch (error) {
        console.error('Failed to check index status:', error);
    }
}

// Utility functions
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', function() {
    const questionInput = document.getElementById('questionInput');
    if (questionInput) {
        questionInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }
});
