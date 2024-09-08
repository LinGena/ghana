let isRunning = false;
let currentTabId = null;
let processedPages = new Set(); // Хранит уже обработанные страницы, чтобы избежать повторов

// Функция для получения URL из эндпойнта
function getURLFromEndpoint() {
    return fetch('http://localhost:5000/get_url', {
        method: 'GET',
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error fetching URL: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            let url = data.url;
            console.log("Initial URL from endpoint: ", url);
            processPage(url, 0);  // Начинаем с шага 0 (основная страница)
        })
        .catch(error => console.error('Error fetching URL:', error));
}

function getNextStepURL(baseUrl, step) {
    // Проверяем, если baseUrl содержит 'profile.php'
    const isProfile = baseUrl.includes('profile.php');

    switch (step) {
        case 1:
            console.log("Next step: /about");
            // Если 'profile.php' присутствует, добавляем &sk=about
            return isProfile ? baseUrl + '&sk=about' : baseUrl + '/about';  // Переход на /about
        case 2:
            console.log("Next step: /groups");
            // Если 'profile.php' присутствует, добавляем &sk=groups
            return isProfile ? baseUrl + '&sk=groups' : baseUrl + '/groups';  // Переход на /groups
        case 3:
            console.log("Next step: /likes");
            // Если 'profile.php' присутствует, добавляем &sk=likes
            return isProfile ? baseUrl + '&sk=likes' : baseUrl + '/likes';  // Переход на /likes
        default:
            console.log("No more steps.");
            return null;  // Все шаги выполнены
    }
}

// Функция для получения базового URL
function getBaseUrl(url) {
    // Проверяем, содержит ли URL 'profile.php'
    if (url.includes('profile.php')) {
        // Для profile.php просто возвращаем URL без изменений
        return url.split('&sk=')[0];  // Убираем только параметр &sk=, если он есть
    }

    // Если это обычный URL, удаляем '/about', '/groups', '/likes'
    return url.replace(/\/about|\/groups|\/likes/g, '');  // Убираем любые из этих сегментов
}

// Функция для обработки страницы по URL
function processPage(url, step) {
    if (!isRunning) return;  // Проверяем, что процесс запущен

    console.log(`Processing URL: ${url}, Step: ${step}`);

    chrome.tabs.update(currentTabId, { url: url }, function (tab) {
        chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, tabInfo) {
            // Проверяем, что вкладка соответствует текущему ID, и страница полностью загружена
            if (tabId === currentTabId && changeInfo.status === 'complete' && tabInfo.url === url && !processedPages.has(url)) {
                console.log(`Page loaded: ${url}`);

                processedPages.add(url); // Добавляем страницу в список обработанных, чтобы избежать повтора

                // Отправляем сообщение на контентный скрипт для сохранения HTML
                chrome.tabs.sendMessage(currentTabId, { action: 'processPage' }, function (response) {
                    if (response && response.status === 'HTML saved successfully') {
                        console.log(response.status);

                        let baseUrl = getBaseUrl(url);
                        // Увеличиваем шаг на +1 перед переходом
                        let nextStep = step + 1;
                        let nextURL = getNextStepURL(baseUrl, nextStep);

                        if (nextURL) {
                            console.log(`Navigating to next step (Step ${nextStep}): ${nextURL}`);
                            processPage(nextURL, nextStep);  // Переход на следующий шаг
                        } else {
                            console.log("All steps completed, fetching new URL.");
                            processedPages.clear(); // Очищаем список перед следующим циклом
                            getURLFromEndpoint();  // Повторно запрашиваем новый URL
                        }
                    } else {
                        console.error('Error processing page: ', response);
                    }
                });
            }
        });
    });
}

// Логика для старта и остановки
chrome.runtime.onMessage.addListener((message) => {
    if (message.action === 'start') {
        if (!isRunning) {
            isRunning = true;
            chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
                if (tabs && tabs[0]) {
                    currentTabId = tabs[0].id;
                    getURLFromEndpoint();  // Запуск процесса
                } else {
                    console.error('No active tab found.');
                }
            });
        }
    } else if (message.action === 'stop') {
        isRunning = false;  // Останавливаем процесс
        console.log('Process stopped');
    }
});
