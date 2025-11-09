let tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();

let user = null;

if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    user = tg.initDataUnsafe.user;
    console.log('✅ User from initDataUnsafe:', user);
}

if (!user && tg.WebAppUser) {
    user = tg.WebAppUser;
    console.log('✅ User from WebAppUser:', user);
}

if (!user) {
    try {
        const initData = tg.initData;
        if (initData) {
            const params = new URLSearchParams(initData);
            const userParam = params.get('user');
            if (userParam) {
                user = JSON.parse(decodeURIComponent(userParam));
                console.log('✅ User from initData:', user);
            }
        }
    } catch (e) {
        console.error('Error parsing initData:', e);
    }
}

if (!user || !user.id) {
    console.warn('⚠️ Telegram user data not available, using test data');
    console.log('tg object:', tg);
    console.log('tg.initDataUnsafe:', tg.initDataUnsafe);
    console.log('tg.initData:', tg.initData);

    user = {
        id: 123456789,
        username: 'user',
        first_name: 'Вы',
        last_name: 'Вы'
    };
} else {
    console.log('✅ Final user data:', user);
}

const state = {
    isLoading: false,
    messageHistory: [],
    currentTab: 'chat',
    interviewState: {
        isActive: false,
        currentQuestion: 0,
        answers: [],
        score: 0
    }
};

const favoriteStates = new Map();

const INTERVIEW_QUESTIONS = [
    "Расскажите, какие основные обязанности специалиста по охране труда вы знаете?",
    "Что включает в себя система управления охраной труда (СУОТ) на предприятии?",
    "Какие виды инструктажей по охране труда существуют и в каких случаях они проводятся?",
    "Расскажите о порядке расследования несчастных случаев на производстве.",
    "Какие требования предъявляются к обеспечению работников средствами индивидуальной защиты (СИЗ)?",
    "Что такое специальная оценка условий труда (СОУТ) и как часто она проводится?",
    "Какие документы должны вестись специалистом по охране труда в организации?",
    "Расскажите о требованиях безопасности при работе на высоте.",
    "Какова процедура допуска работников к работам с повышенной опасностью?",
    "Что должен делать работодатель при выявлении профессионального заболевания у работника?"
];

const elements = {
    loadingScreen: document.getElementById('loading-screen'),
    chatContainer: document.getElementById('chat-container'),
    questionInput: document.getElementById('question-input'),
    sendButton: document.getElementById('send-button'),
    statusIndicator: document.getElementById('status-indicator'),
    statusText: document.querySelector('.status-text'),
    tabButtons: null,
    interviewContainer: null
};

const API_BASE = window.location.origin;

const ICONS = {
    copy: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>',
    speaker: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>',
    heart: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>',
    heartFilled: '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>'
};

function hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(36);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function syncFavoriteButtons(messageHash, isFavorite, favoriteId = null) {
    const buttons = favoriteStates.get(messageHash);
    if (buttons) {
        buttons.forEach(btn => {
            if (isFavorite) {
                btn.classList.add('favorited');
                btn.innerHTML = ICONS.heartFilled;
                if (favoriteId) {
                    btn.dataset.favoriteId = favoriteId;
                }
            } else {
                btn.classList.remove('favorited');
                btn.innerHTML = ICONS.heart;
                delete btn.dataset.favoriteId;
            }
        });
    }
}

async function init() {
    console.log('🚀 Initializing Mini App...');

    applyTelegramTheme();
    await initUser();
    createTabs();
    setupEventListeners();

    setTimeout(() => {
        elements.loadingScreen.classList.add('hidden');
    }, 800);

    console.log('✅ Mini App initialized');
}

function createTabs() {
    const header = document.querySelector('.app-header .header-content');

    const tabsContainer = document.createElement('div');
    tabsContainer.className = 'tabs-container';
    tabsContainer.innerHTML = `
        <button class="tab-button active" data-tab="chat">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>Консультант</span>
        </button>
        <button class="tab-button" data-tab="interview">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <polyline points="17 11 19 13 23 9"></polyline>
            </svg>
            <span>Собеседование</span>
        </button>
        <button class="tab-button" data-tab="profile">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>Профиль</span>
        </button>
    `;

    header.appendChild(tabsContainer);

    elements.tabButtons = tabsContainer.querySelectorAll('.tab-button');

    const interviewContainer = document.createElement('div');
    interviewContainer.id = 'interview-container';
    interviewContainer.className = 'interview-container hidden';
    interviewContainer.innerHTML = `
        <div class="interview-welcome">
            <div class="interview-icon">👔</div>
            <h2>Пробное собеседование</h2>
            <p>Проверьте свои знания в области охраны труда</p>
            <div class="interview-info">
                <div class="info-item">
                    <span class="info-label">Вопросов:</span>
                    <span class="info-value">${INTERVIEW_QUESTIONS.length}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Время:</span>
                    <span class="info-value">~15-20 мин</span>
                </div>
            </div>
            <button id="start-interview-btn" class="start-interview-btn">Начать собеседование</button>
        </div>
        <div class="interview-content hidden">
            <div class="interview-progress">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-text">Вопрос <span id="current-q">1</span> из ${INTERVIEW_QUESTIONS.length}</div>
            </div>
            <div class="interview-question">
                <div class="question-number">Вопрос <span id="q-number">1</span></div>
                <div class="question-text" id="question-text"></div>
            </div>
            <div class="interview-answer">
                <textarea id="interview-input" placeholder="Введите ваш ответ..."></textarea>
                <button id="submit-answer-btn" class="submit-answer-btn">Отправить ответ</button>
            </div>
        </div>
        <div class="interview-results hidden">
            <div class="results-icon" id="results-icon">🎉</div>
            <h2 id="results-title">Отличный результат!</h2>
            <div class="results-score">
                <div class="score-circle">
                    <span id="final-score">0</span>
                    <span class="score-max">/100</span>
                </div>
            </div>
            <div id="results-details" class="results-details"></div>
            <div class="results-verdict" id="results-verdict"></div>
            <div class="results-actions">
                <button id="retry-interview-btn" class="retry-btn">Пройти заново</button>
                <button id="back-to-chat-btn" class="back-btn">Вернуться к консультанту</button>
            </div>
        </div>
    `;

    document.querySelector('.app-container').insertBefore(
        interviewContainer,
        document.querySelector('.input-container')
    );

    elements.interviewContainer = interviewContainer;

    const profileContainer = document.createElement('div');
    profileContainer.id = 'profile-container';
    profileContainer.className = 'profile-container hidden';
    profileContainer.innerHTML = `
        <div class="profile-content">
            <div class="profile-header">
                <div class="profile-avatar">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                </div>
                <h2 id="profile-name">${user.first_name || 'Пользователь'}</h2>
                <p id="profile-username">@${user.username || 'user'}</p>
            </div>

            <div class="profile-stats">
                <div class="stat-card">
                    <div class="stat-icon">💬</div>
                    <div class="stat-value" id="stat-queries">0</div>
                    <div class="stat-label">Запросов</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">❤️</div>
                    <div class="stat-value" id="stat-favorites">0</div>
                    <div class="stat-label">Избранное</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📅</div>
                    <div class="stat-value" id="stat-days">0</div>
                    <div class="stat-label">Дней с нами</div>
                </div>
            </div>

            <div class="profile-section">
                <div class="section-header">
                    <h3>❤️ Избранное</h3>
                    <p class="section-subtitle">Ваша личная копилка ценных знаний</p>
                </div>
                <div id="favorites-list" class="favorites-list">
                    <div class="loading-favorites">Загрузка...</div>
                </div>
            </div>
        </div>
    `;

    document.querySelector('.app-container').insertBefore(
        profileContainer,
        document.querySelector('.input-container')
    );

    elements.profileContainer = profileContainer;
}

function applyTelegramTheme() {
    const themeParams = tg.themeParams;
    const colorScheme = tg.colorScheme;

    if (colorScheme === 'dark') {
        document.documentElement.style.setProperty('--bg-primary', themeParams.bg_color || '#0a0a0a');
        document.documentElement.style.setProperty('--bg-secondary', themeParams.secondary_bg_color || '#141414');
        document.documentElement.style.setProperty('--text-primary', themeParams.text_color || '#f5f5f5');
        document.documentElement.style.setProperty('--text-secondary', themeParams.hint_color || '#a3a3a3');
        document.documentElement.style.setProperty('--accent-primary', themeParams.button_color || '#3b82f6');
        document.documentElement.style.setProperty('--accent-secondary', themeParams.link_color || '#06b6d4');
    } else {
        document.documentElement.style.setProperty('--bg-primary', themeParams.bg_color || '#ffffff');
        document.documentElement.style.setProperty('--bg-secondary', themeParams.secondary_bg_color || '#f5f5f5');
        document.documentElement.style.setProperty('--bg-tertiary', '#e5e5e5');
        document.documentElement.style.setProperty('--text-primary', themeParams.text_color || '#000000');
        document.documentElement.style.setProperty('--text-secondary', themeParams.hint_color || '#737373');
        document.documentElement.style.setProperty('--accent-primary', themeParams.button_color || '#3b82f6');
        document.documentElement.style.setProperty('--accent-secondary', themeParams.link_color || '#0284c7');
        document.documentElement.style.setProperty('--border-color', '#d4d4d4');
        document.documentElement.style.setProperty('--bg-assistant', '#f5f5f5');
        document.documentElement.style.setProperty('--bg-user', themeParams.button_color || '#3b82f6');
    }

    console.log('Theme applied:', colorScheme, themeParams);
}

async function initUser() {
    try {
        const response = await fetch(`${API_BASE}/api/init_user`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                telegram_id: user.id,
                username: user.username,
                first_name: user.first_name,
                last_name: user.last_name
            })
        });

        const data = await response.json();

        if (data.success) {
            console.log('👤 User initialized:', data.user);
        }
    } catch (error) {
        console.error('❌ Error initializing user:', error);
    }
}

function setupEventListeners() {
    elements.sendButton.addEventListener('click', handleSendMessage);

    elements.questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    elements.questionInput.addEventListener('input', () => {
        autoResizeTextarea();
        const hasText = elements.questionInput.value.trim().length > 0;
        elements.sendButton.disabled = !hasText || state.isLoading;
    });

    elements.questionInput.addEventListener('input', () => {
        const hasText = elements.questionInput.value.trim().length > 0;
        elements.sendButton.disabled = !hasText || state.isLoading;
    });

    elements.tabButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    elements.questionInput.addEventListener('keyup', (e) => {
        if (e.key === 'Backspace' || e.key === 'Delete') {
            if (!elements.questionInput.value.trim()) {
                elements.questionInput.style.height = '44px';
            }
        }
    });

    document.getElementById('start-interview-btn')?.addEventListener('click', startInterview);
    document.getElementById('submit-answer-btn')?.addEventListener('click', submitInterviewAnswer);
    document.getElementById('retry-interview-btn')?.addEventListener('click', startInterview);
    document.getElementById('back-to-chat-btn')?.addEventListener('click', () => switchTab('chat'));
    elements.chatContainer.addEventListener('click', handleMessageActions);
}

async function handleMessageActions(e) {
    const btn = e.target.closest('.action-btn');
    if (!btn) return;

    const text = btn.dataset.text;
    const wrapper = btn.closest('.message-wrapper');
    const question = getPreviousUserMessage(wrapper);

    if (btn.classList.contains('copy-btn')) {
        await copyToClipboard(text);
        showToast('Ответ скопирован');
    } else if (btn.classList.contains('speak-btn')) {
        speakText(text, btn);
    } else if (btn.classList.contains('favorite-btn')) {
        await toggleFavorite(question, text, btn);
    }
}

function getPreviousUserMessage(currentWrapper) {
    let prev = currentWrapper.previousElementSibling;
    while (prev) {
        if (prev.classList.contains('user-wrapper')) {
            const content = prev.querySelector('.message-content');
            return content ? content.textContent : '';
        }
        prev = prev.previousElementSibling;
    }
    return '';
}

async function copyToClipboard(text) {
    const cleanText = text.replace(/<[^>]*>/g, '').replace(/\*\*/g, '');
    try {
        await navigator.clipboard.writeText(cleanText);
        tg.HapticFeedback.notificationOccurred('success');
    } catch (err) {
        console.error('Copy failed:', err);
    }
}

function speakText(text, btn) {
    const cleanText = text.replace(/<[^>]*>/g, '').replace(/\*\*/g, '');

    if ('speechSynthesis' in window) {
        if (window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            btn.classList.remove('speaking');
            return;
        }

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'ru-RU';
        utterance.rate = 0.9;

        btn.classList.add('speaking');

        utterance.onend = () => {
            btn.classList.remove('speaking');
        };

        window.speechSynthesis.speak(utterance);
        tg.HapticFeedback.notificationOccurred('success');
    } else {
        showToast('Озвучивание не поддерживается');
    }
}

async function toggleFavorite(question, answer, btn) {
    const isFavorite = btn.classList.contains('favorited');

    if (isFavorite) {
        await removeFavorite(question, answer, btn);
    } else {
        await addFavorite(question, answer, btn);
    }
}

async function addFavorite(question, answer, btn) {
    try {
        const messageHash = btn.dataset.hash;

        const response = await fetch(`${API_BASE}/api/favorites`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                telegram_id: user.id,
                question: question,
                answer: answer,
                title: question.substring(0, 50) + (question.length > 50 ? '...' : '')
            })
        });

        const data = await response.json();

        if (data.success) {
            syncFavoriteButtons(messageHash, true, data.favorite.id);
            showToast('Добавлено в избранное ❤️');
            tg.HapticFeedback.notificationOccurred('success');
        }
    } catch (error) {
        console.error('Error adding favorite:', error);
        showToast('Ошибка добавления в избранное');
    }
}

async function removeFavorite(question, answer, btn) {
    const favoriteId = btn.dataset.favoriteId;
    const messageHash = btn.dataset.hash;

    if (!favoriteId) {
        console.error('No favorite ID found');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/favorites/${favoriteId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            syncFavoriteButtons(messageHash, false);
            showToast('Удалено из избранного');
            tg.HapticFeedback.notificationOccurred('success');
        }
    } catch (error) {
        console.error('Error removing favorite:', error);
        showToast('Ошибка удаления из избранного');
    }
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

function switchTab(tab) {
    state.currentTab = tab;

    elements.tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    elements.chatContainer.classList.add('hidden');
    elements.interviewContainer.classList.add('hidden');
    elements.profileContainer.classList.add('hidden');
    document.querySelector('.input-container').classList.add('hidden');

    if (tab === 'chat') {
        elements.chatContainer.classList.remove('hidden');
        document.querySelector('.input-container').classList.remove('hidden');
    } else if (tab === 'interview') {
        elements.interviewContainer.classList.remove('hidden');
    } else if (tab === 'profile') {
        elements.profileContainer.classList.remove('hidden');
        loadProfileData();
    }
}

async function loadProfileData() {
    try {
        const profileResponse = await fetch(`${API_BASE}/api/profile/${user.id}`);
        const profileData = await profileResponse.json();

        if (profileData.success) {
            const profile = profileData.profile;

            document.getElementById('stat-queries').textContent = profile.stats.queries_count || 0;
            document.getElementById('stat-favorites').textContent = profile.favorites_count || 0;

            const createdDate = new Date(profile.user.created_at);
            const daysSince = Math.floor((new Date() - createdDate) / (1000 * 60 * 60 * 24));
            document.getElementById('stat-days').textContent = daysSince;
        }

        await loadFavorites();

    } catch (error) {
        console.error('Error loading profile:', error);
        showToast('Ошибка загрузки профиля');
    }
}

async function loadFavorites() {
    const favoritesList = document.getElementById('favorites-list');

    try {
        const response = await fetch(`${API_BASE}/api/favorites/${user.id}`);
        const data = await response.json();

        if (data.success) {
            const favorites = data.favorites;
            document.getElementById('stat-favorites').textContent = favorites.length;

            if (favorites.length === 0) {
                favoritesList.innerHTML = `
                    <div class="empty-favorites">
                        <div class="empty-icon">💭</div>
                        <p>Здесь пока пусто</p>
                        <p class="empty-hint">Добавляйте в избранное полезные ответы, нажимая на ♡</p>
                    </div>
                `;
            } else {
                favoritesList.innerHTML = favorites.map(fav => `
                    <div class="favorite-item" data-id="${fav.id}">
                        <div class="favorite-header">
                            <div class="favorite-title">${fav.title}</div>
                            <button class="favorite-delete" onclick="deleteFavoriteFromProfile(${fav.id})">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                            </button>
                        </div>
                        <div class="favorite-question">❓ ${fav.question}</div>
                        <div class="favorite-answer">${formatMessageText(fav.answer.substring(0, 200))}${fav.answer.length > 200 ? '...' : ''}</div>
                        <div class="favorite-date">${new Date(fav.created_at).toLocaleDateString('ru-RU')}</div>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading favorites:', error);
        favoritesList.innerHTML = '<div class="error-favorites">Ошибка загрузки избранного</div>';
    }
}

async function deleteFavoriteFromProfile(favoriteId) {
    if (!confirm('Удалить из избранного?')) return;

    try {
        const response = await fetch(`${API_BASE}/api/favorites/${favoriteId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            await loadFavorites();

            syncAllFavoriteButtonsFromServer();

            showToast('Удалено из избранного');
            tg.HapticFeedback.notificationOccurred('success');
        }
    } catch (error) {
        console.error('Error deleting favorite:', error);
        showToast('Ошибка удаления');
    }
}

window.deleteFavoriteFromProfile = deleteFavoriteFromProfile;

async function checkIfFavorited(answer, btn) {
    try {
        const response = await fetch(`${API_BASE}/api/favorites/${user.id}`);
        const data = await response.json();

        if (data.success) {
            const messageHash = btn.dataset.hash;
            const favorite = data.favorites.find(fav => hashCode(fav.answer) === messageHash);

            if (favorite) {
                syncFavoriteButtons(messageHash, true, favorite.id);
            }
        }
    } catch (error) {
        console.error('Error checking favorite:', error);
    }
}

async function syncAllFavoriteButtonsFromServer() {
    try {
        const response = await fetch(`${API_BASE}/api/favorites/${user.id}`);
        const data = await response.json();

        if (data.success) {
            const favorites = data.favorites;
            const favoriteAnswers = new Set(favorites.map(f => hashCode(f.answer)));
            const favoriteMap = new Map(favorites.map(f => [hashCode(f.answer), f.id]));

            favoriteStates.forEach((buttons, messageHash) => {
                const isFavorite = favoriteAnswers.has(messageHash);
                const favoriteId = favoriteMap.get(messageHash);
                syncFavoriteButtons(messageHash, isFavorite, favoriteId);
            });
        }
    } catch (error) {
        console.error('Error syncing favorite buttons:', error);
    }
}

function startInterview() {
    state.interviewState = {
        isActive: true,
        currentQuestion: 0,
        answers: [],
        score: 0
    };

    document.querySelector('.interview-welcome').classList.add('hidden');
    document.querySelector('.interview-content').classList.remove('hidden');
    document.querySelector('.interview-results').classList.add('hidden');

    showInterviewQuestion();
}

function showInterviewQuestion() {
    const q = state.interviewState.currentQuestion;
    const total = INTERVIEW_QUESTIONS.length;

    document.getElementById('current-q').textContent = q + 1;
    document.getElementById('q-number').textContent = q + 1;
    document.getElementById('question-text').textContent = INTERVIEW_QUESTIONS[q];
    document.getElementById('interview-input').value = '';

    const progress = ((q + 1) / total) * 100;
    document.querySelector('.progress-fill').style.width = `${progress}%`;
}

async function submitInterviewAnswer() {
    const answer = document.getElementById('interview-input').value.trim();

    if (!answer) {
        alert('Пожалуйста, введите ответ');
        return;
    }

    const submitBtn = document.getElementById('submit-answer-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Проверка...';

    try {
        const question = INTERVIEW_QUESTIONS[state.interviewState.currentQuestion];

        const systemPrompt = `Ты - эксперт по охране труда, проводящий собеседование.
Оцени ответ кандидата по шкале от 0 до 10 баллов.
Критерии оценки:
- Полнота ответа (0-4 балла)
- Точность и знание нормативов (0-3 балла)
- Практическая применимость (0-3 балла)

Верни ТОЛЬКО JSON в формате:
{
  "score": число от 0 до 10,
  "feedback": "краткая обратная связь 1-2 предложения"
}`;

        const response = await fetch(`${API_BASE}/api/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: `Вопрос: ${question}\n\nОтвет кандидата: ${answer}\n\nОцени этот ответ.`,
                telegram_id: user.id,
                username: user.username,
                first_name: user.first_name,
                last_name: user.last_name,
                system_prompt: systemPrompt
            })
        });

        const data = await response.json();

        if (data.success) {
            let evaluation;
            try {
                const jsonMatch = data.answer.match(/\{[\s\S]*\}/);
                if (jsonMatch) {
                    evaluation = JSON.parse(jsonMatch[0]);
                } else {
                    evaluation = { score: 5, feedback: "Ответ принят" };
                }
            } catch (e) {
                evaluation = { score: 5, feedback: "Ответ принят" };
            }

            state.interviewState.answers.push({
                question,
                answer,
                score: evaluation.score,
                feedback: evaluation.feedback
            });

            state.interviewState.score += evaluation.score;

            if (state.interviewState.currentQuestion < INTERVIEW_QUESTIONS.length - 1) {
                state.interviewState.currentQuestion++;
                showInterviewQuestion();
            } else {
                showInterviewResults();
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Произошла ошибка. Попробуйте еще раз.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Отправить ответ';
    }
}

function showInterviewResults() {
    const totalScore = state.interviewState.score;
    const maxScore = INTERVIEW_QUESTIONS.length * 10;
    const percentage = Math.round((totalScore / maxScore) * 100);

    document.querySelector('.interview-content').classList.add('hidden');
    document.querySelector('.interview-results').classList.remove('hidden');

    document.getElementById('final-score').textContent = percentage;

    let verdict, icon, title;

    if (percentage >= 80) {
        icon = '🎉';
        title = 'Отличный результат!';
        verdict = 'Вы демонстрируете превосходное знание охраны труда. Вы готовы работать специалистом по охране труда!';
    } else if (percentage >= 60) {
        icon = '👍';
        title = 'Хороший результат!';
        verdict = 'У вас есть хорошие базовые знания. С дополнительной подготовкой вы сможете успешно работать в этой области.';
    } else if (percentage >= 40) {
        icon = '📚';
        title = 'Неплохо, но есть над чем работать';
        verdict = 'Рекомендуем углубить знания нормативной базы и практических аспектов охраны труда перед трудоустройством.';
    } else {
        icon = '📖';
        title = 'Требуется дополнительное обучение';
        verdict = 'Необходимо существенно расширить знания в области охраны труда. Рекомендуем пройти специализированное обучение.';
    }

    document.getElementById('results-icon').textContent = icon;
    document.getElementById('results-title').textContent = title;
    document.getElementById('results-verdict').textContent = verdict;

    const detailsHTML = state.interviewState.answers.map((item, idx) => `
        <div class="result-item">
            <div class="result-header">
                <span class="result-q-num">Вопрос ${idx + 1}</span>
                <span class="result-score">${item.score}/10</span>
            </div>
            <div class="result-feedback">${item.feedback}</div>
        </div>
    `).join('');

    document.getElementById('results-details').innerHTML = detailsHTML;
}

function autoResizeTextarea() {
    const textarea = elements.questionInput;

    textarea.style.height = '44px';

    if (!textarea.value.trim()) {
        textarea.style.height = '44px';
        return;
    }

    const newHeight = Math.min(textarea.scrollHeight, 120);
    textarea.style.height = newHeight + 'px';
}

async function handleSendMessage() {
    const question = elements.questionInput.value.trim();

    if (!question || state.isLoading) return;

    addMessage(question, 'user');

    elements.questionInput.value = '';
    autoResizeTextarea();
    elements.sendButton.disabled = true;
    elements.sendButton.disabled = true;

    setLoadingState(true);

    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/api/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                telegram_id: user.id,
                username: user.username,
                first_name: user.first_name,
                last_name: user.last_name
            })
        });

        const data = await response.json();

        removeTypingIndicator(typingId);

        if (data.success) {
            await addMessageWithTypingEffect(data.answer, 'assistant');
            tg.HapticFeedback.notificationOccurred('success');
        } else {
            throw new Error(data.error || 'Unknown error');
        }

    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator(typingId);
        addMessage('Извините, произошла ошибка. Попробуйте еще раз.', 'assistant', true);
        tg.HapticFeedback.notificationOccurred('error');
    } finally {
        setLoadingState(false);
    }
}

function addMessage(text, type, isError = false, messageId = null) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${type}-wrapper`;
    if (messageId) wrapper.dataset.messageId = messageId;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = type === 'user'
        ? '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5.5-2.5l7.51-3.49L17.5 6.5 9.99 9.99 6.5 17.5zm5.5-6.6c.61 0 1.1.49 1.1 1.1s-.49 1.1-1.1 1.1-1.1-.49-1.1-1.1.49-1.1 1.1-1.1z"/></svg>';

    const message = document.createElement('div');
    message.className = `message ${type}-message`;

    if (isError) {
        message.style.borderColor = '#ef4444';
    }

    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = formatMessageText(text);

    message.appendChild(content);

    if (type === 'assistant' && !isError) {
        const actions = document.createElement('div');
        actions.className = 'message-actions';

        const messageHash = hashCode(text);

        actions.innerHTML = `
            <button class="action-btn copy-btn" title="Копировать ответ" data-text="${escapeHtml(text)}">
                ${ICONS.copy}
            </button>
            <button class="action-btn speak-btn" title="Озвучить ответ" data-text="${escapeHtml(text)}">
                ${ICONS.speaker}
            </button>
            <button class="action-btn favorite-btn" title="Добавить в избранное" data-text="${escapeHtml(text)}" data-hash="${messageHash}">
                ${ICONS.heart}
            </button>
        `;

        message.appendChild(actions);

        const favoriteBtn = actions.querySelector('.favorite-btn');
        if (!favoriteStates.has(messageHash)) {
            favoriteStates.set(messageHash, []);
        }
        favoriteStates.get(messageHash).push(favoriteBtn);
    }

    wrapper.appendChild(avatar);
    wrapper.appendChild(message);

    elements.chatContainer.appendChild(wrapper);
    scrollToBottom();

    state.messageHistory.push({ text, type, timestamp: new Date(), id: messageId });

    return wrapper;
}

async function addMessageWithTypingEffect(text, type, messageId = null) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${type}-wrapper`;
    if (messageId) wrapper.dataset.messageId = messageId;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5.5-2.5l7.51-3.49L17.5 6.5 9.99 9.99 6.5 17.5zm5.5-6.6c.61 0 1.1.49 1.1 1.1s-.49 1.1-1.1 1.1-1.1-.49-1.1-1.1.49-1.1 1.1-1.1z"/></svg>';

    const message = document.createElement('div');
    message.className = `message ${type}-message`;

    const content = document.createElement('div');
    content.className = 'message-content';

    message.appendChild(content);
    wrapper.appendChild(avatar);
    wrapper.appendChild(message);
    elements.chatContainer.appendChild(wrapper);

    const words = text.split(' ');
    let currentText = '';

    for (let i = 0; i < words.length; i++) {
        currentText += words[i] + ' ';
        content.innerHTML = formatMessageText(currentText);
        scrollToBottom();
        await sleep(30);
    }

    content.innerHTML = formatMessageText(text);

    const messageHash = hashCode(text);

    const actions = document.createElement('div');
    actions.className = 'message-actions';

    actions.innerHTML = `
        <button class="action-btn copy-btn" title="Копировать ответ" data-text="${escapeHtml(text)}">
            ${ICONS.copy}
        </button>
        <button class="action-btn speak-btn" title="Озвучить ответ" data-text="${escapeHtml(text)}">
            ${ICONS.speaker}
        </button>
        <button class="action-btn favorite-btn" title="Добавить в избранное" data-text="${escapeHtml(text)}" data-hash="${messageHash}">
            ${ICONS.heart}
        </button>
    `;

    message.appendChild(actions);

    const favoriteBtn = actions.querySelector('.favorite-btn');
    if (!favoriteStates.has(messageHash)) {
        favoriteStates.set(messageHash, []);
    }
    favoriteStates.get(messageHash).push(favoriteBtn);

    const question = getPreviousUserMessage(wrapper);
    checkIfFavorited(text, favoriteBtn);

    scrollToBottom();
}

function addTypingIndicator() {
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper assistant-wrapper';
    wrapper.id = 'typing-indicator';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-5.5-2.5l7.51-3.49L17.5 6.5 9.99 9.99 6.5 17.5zm5.5-6.6c.61 0 1.1.49 1.1 1.1s-.49 1.1-1.1 1.1-1.1-.49-1.1-1.1.49-1.1 1.1-1.1z"/></svg>';

    const message = document.createElement('div');
    message.className = 'message assistant-message';

    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;

    message.appendChild(indicator);
    wrapper.appendChild(avatar);
    wrapper.appendChild(message);
    elements.chatContainer.appendChild(wrapper);

    scrollToBottom();

    return 'typing-indicator';
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

function formatMessageText(text) {
    text = text.replace(/\n/g, '<br>');
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/`(.*?)`/g, '<code>$1</code>');

    return text;
}

function setLoadingState(isLoading) {
    state.isLoading = isLoading;

    if (isLoading) {
        elements.statusIndicator.classList.add('loading');
        elements.statusText.textContent = 'Обработка запроса...';
        elements.sendButton.disabled = true;
    } else {
        elements.statusIndicator.classList.remove('loading');
        elements.statusText.textContent = 'Готов к работе';
        elements.sendButton.disabled = elements.questionInput.value.trim().length === 0;
    }
}

function scrollToBottom() {
    elements.chatContainer.scrollTo({
        top: elements.chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

document.addEventListener('DOMContentLoaded', init);

tg.BackButton.onClick(() => {
    tg.close();
});

let recognition = null;
let isRecording = false;

if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        elements.questionInput.value = transcript;
        elements.sendButton.disabled = false;
        isRecording = false;
        elements.voiceButton.classList.remove('recording');
    };

    recognition.onerror = () => {
        isRecording = false;
        elements.voiceButton.classList.remove('recording');
    };

    recognition.onend = () => {
        isRecording = false;
        elements.voiceButton.classList.remove('recording');
    };
}

elements.voiceButton = document.getElementById('voice-button');

elements.voiceButton?.addEventListener('click', () => {
    if (!recognition) {
        alert('Голосовой ввод не поддерживается вашим браузером');
        return;
    }

    if (isRecording) {
        recognition.stop();
        isRecording = false;
        elements.voiceButton.classList.remove('recording');
    } else {
        recognition.start();
        isRecording = true;
        elements.voiceButton.classList.add('recording');
    }
});