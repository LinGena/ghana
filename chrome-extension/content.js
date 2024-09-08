// Функция для отправки данных на указанный эндпойнт с именем файла
function sendHTML(fileName) {
    let pageHTML = document.documentElement.outerHTML;

    return fetch('http://localhost:5000/save_html', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'html': pageHTML,
            'file': fileName
        })
    })
        .then(response => response.text())
        .then(result => {
            console.log(`HTML saved as ${fileName}:`, result);
            return { status: 'HTML saved successfully' }; // возвращаем результат
        })
        .catch(error => {
            console.error('Error sending HTML:', error);
            return { status: 'Failed to send HTML' }; // возвращаем ошибку
        });
}

// Слушаем сообщения от background.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'processPage') {
        // Определяем имя файла в зависимости от текущего URL
        let fileName;
        if (window.location.href.endsWith('about')) {
            fileName = 'page_about.html';
        } else if (window.location.href.endsWith('groups')) {
            fileName = 'page_groups.html';
        } else if (window.location.href.endsWith('likes')) {
            fileName = 'page_likes.html';
        } else {
            fileName = 'page.html';  // Основная страница
        }

        // Отправляем HTML сразу
        sendHTML(fileName).then((result) => {
            sendResponse(result); // Отправляем результат обратно
        });

        return true;  // Указываем, что ответ будет асинхронным
    }
});
