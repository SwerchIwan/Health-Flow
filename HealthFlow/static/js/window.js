document.addEventListener("DOMContentLoaded", function() {
    var cornerPopup = document.getElementById("cornerPopup");
    var closeBtn = document.getElementById("closeBtn");
    var maximizeBtn = document.getElementById("maximizeBtn");
    var blackCircle = document.getElementById("blackCircle");
    var messageArea = document.getElementById("messageArea");
    var supportForm = document.getElementById("supportForm");
    var messageInput = document.getElementById("messageInput");

    // Функция для разворачивания окна в полный размер
    function maximizeWindow() {
        cornerPopup.classList.toggle("maximized");
    }

    // Функция для закрытия окна
    function closeWindow() {
        cornerPopup.style.opacity = "0"; // Плавное исчезновение окна
        setTimeout(function() {
            cornerPopup.style.display = "none"; // Скрытие окна
            blackCircle.style.bottom = "20px"; // Появление круга
        }, 300); // Длительность анимации
    }

    // Функция для открытия окна
    function openWindow() {
        blackCircle.style.bottom = "-40px"; // Скрытие круга
        cornerPopup.style.display = "block"; // Появление окна
        setTimeout(function() {
            cornerPopup.style.opacity = "1"; // Плавное появление окна
        }, 100); // Задержка перед появлением окна
    }

    // Функция для отправки сообщения
    function sendMessage(message, sender) {
        var messageElement = document.createElement("div");
        messageElement.classList.add("message");
        messageElement.classList.add(sender === "user" ? "sender" : "receiver");
        messageElement.textContent = message;
        messageArea.appendChild(messageElement);
        messageArea.scrollTop = messageArea.scrollHeight; // Прокрутка вниз при добавлении сообщения
    }

    // Обработчик отправки формы
    supportForm.addEventListener("submit", function(event) {
        event.preventDefault();
        var message = messageInput.value.trim();
        if (message !== "") {
            sendMessage(message, "user");
            messageInput.value = "";
            // Здесь можно добавить логику отправки сообщения на сервер или куда-либо еще
        }
    });

    // Открываем немодальное окно в начальном размере
    cornerPopup.style.display = "block";

    // Закрываем немодальное окно при нажатии на кнопку закрытия
    closeBtn.addEventListener("click", function(event) {
        event.preventDefault();
        closeWindow();
    });

    // Разворачиваем окно в полный размер при нажатии на кнопку масштабирования
    maximizeBtn.addEventListener("click", function(event) {
        event.preventDefault();
        maximizeWindow();
    });

    // Открываем окно при клике на черный круг
    blackCircle.addEventListener("click", function() {
        openWindow();
    });

    // Пример сообщения от техподдержки
    sendMessage("Добрый день! Как я могу вам помочь?", "support");
});

// Обновляем позицию окна техподдержки при прокрутке страницы
window.addEventListener('scroll', function() {
    var cornerPopup = document.getElementById('cornerPopup');
    var windowHeight = window.innerHeight;
    var scrollTop = window.scrollY || window.pageYOffset;

    // Позиция окна техподдержки
    var popupBottomPosition = windowHeight - cornerPopup.offsetHeight + scrollTop;

    // Устанавливаем позицию окна техподдержки
    cornerPopup.style.bottom = popupBottomPosition + 'px';
});
