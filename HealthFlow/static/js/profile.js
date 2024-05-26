$(document).ready(function() {
    // Делегирование событий для клика на заметку
    $('#notes-container').on('click', '.note-item', function() {
        const noteId = $(this).data('note-id');

        // AJAX запрос для получения полной информации о заметке
        $.ajax({
            url: `/profile/get_note_details/${noteId}/`,
            method: 'GET',
            success: function(response) {
                // Скрываем все заметки и отображаем выбранную заметку во весь блок
                $('#notes-container').html(
                    `<div class="full-note-item">
                        <button id="close-full-note">Закрыть</button>
                        <h3>${response.date}</h3>
                        <p>${response.additional_notes}</p>
                        ${response.blood_data ? `
                            <ul>
                                <li>Гемоглобин: ${response.blood_data.hemoglobin}</li>
                                <li>Лейкоциты: ${response.blood_data.leukocytes}</li>
                                <li>Лимфоциты: ${response.blood_data.lymphocytes}</li>
                            </ul>` : ''}
                        ${response.pressure_data ? `
                            <ul>
                                <li>Систолическое: ${response.pressure_data.systolic}</li>
                                <li>Диастолическое: ${response.pressure_data.diastolic}</li>
                                <li>Пульс: ${response.pressure_data.pulse_rate}</li>
                            </ul>` : ''}
                        ${response.bmi_data ? `
                            <ul>
                                <li>Рост: ${response.bmi_data.height}</li>
                                <li>Вес: ${response.bmi_data.weight}</li>
                            </ul>` : ''}
                    </div>`
                );
            },
            error: function(error) {
                console.error('Ошибка при загрузке заметки', error);
            }
        });
    });

    // Обработчик клика на кнопку "Закрыть"
    $('#notes-container').on('click', '#close-full-note', function() {
        location.reload(); // Перезагружаем страницу для отображения всех заметок
    });

    // Обработчик отправки формы добавления заметки
    $('#add-note-form').submit(function(e) {
        e.preventDefault(); // Предотвращаем отправку формы по умолчанию

        // Получаем CSRF-токен из скрытого поля формы
        var csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

        // Отправляем данные формы на сервер
        $.ajax({
            type: 'POST',
            url: '/profile/add_note/',  // URL для добавления заметки
            data: $(this).serialize() + '&csrfmiddlewaretoken=' + csrfToken, // Добавляем CSRF-токен к данным формы
            success: function(response) {
                console.log(response); // Логируем ответ сервера для отладки
                if (response.note && response.note.id) {
                    // При успешном добавлении заметки обновляем страницу или ее часть
                    // Например, добавляем новую заметку к списку на странице
                    $('#notes-container').append(
                        `<div class="note-item" data-note-id="${response.note.id}">
                            <h3>${response.note.date}</h3>
                            <div class="note-content" style="display: none;">
                                <p>${response.note.additional_notes}</p>
                                ${response.note.blood_data ? `
                                    <ul>
                                        <li>Гемоглобин: ${response.note.blood_data.hemoglobin}</li>
                                        <li>Лейкоциты: ${response.note.blood_data.leukocytes}</li>
                                        <li>Лимфоциты: ${response.note.blood_data.lymphocytes}</li>
                                    </ul>` : ''}
                                ${response.note.pressure_data ? `
                                    <ul>
                                        <li>Систолическое: ${response.note.pressure_data.systolic}</li>
                                        <li>Диастолическое: ${response.note.pressure_data.diastolic}</li>
                                        <li>Пульс: ${response.note.pressure_data.pulse_rate}</li>
                                    </ul>` : ''}
                                ${response.note.bmi_data ? `
                                    <ul>
                                        <li>Рост: ${response.note.bmi_data.height}</li>
                                        <li>Вес: ${response.note.bmi_data.weight}</li>
                                    </ul>` : ''}
                            </div>
                        </div>`
                    );
                    // Очищаем поля формы
                    $('#note-date').val('');
                    $('#additional-notes').val('');
                    $('#note-file').val('');
                    $('input[name="blood[]"]').val('');
                    $('input[name="pressure[]"]').val('');
                    $('input[name="bmi[]"]').val('');
                } else {
                    console.error('Некорректный ответ сервера', response);
                    alert('Ошибка при добавлении заметки');
                }
            },
            error: function(error) {
                alert('Ошибка при добавлении заметки');
            }
        });
    });

    // Обработчик поиска специалистов
    $('#search-specialist').on('input', function() {
        const query = $(this).val();
        if (query.trim() !== '') {
            $.ajax({
                url: `/search_specialist/?q=${query}`,
                method: 'GET',
                success: function(data) {
                    $('#search-results').html('');
                    if (data.specialists.length > 0) {
                        data.specialists.forEach(function(specialist) {
                            $('#search-results').append(`
                                <div class="search-result" data-specialist-id="${specialist.id}">
                                    <p>${specialist.name}</p>
                                </div>
                            `);
                        });
                        $('#search-results').show();
                    } else {
                        $('#search-results').hide();
                    }
                },
                error: function(error) {
                    console.error('Ошибка при поиске специалистов', error);
                }
            });
        } else {
            $('#search-results').hide();
        }
    });

    // Обработчик клика на результат поиска специалиста
    $('#search-results').on('click', '.search-result', function() {
        const specialistId = $(this).data('specialist-id');
        $.ajax({
            url: `start_chat/`,
            method: 'POST',
            data: {
                specialist_id: specialistId,
                csrfmiddlewaretoken: '{{ csrf_token }}'
            },
            success: function(data) {
                if (data.status === 'success') {
                    loadChat(data.chat_id);
                    $('#search-results').hide();
                }
            },
            error: function(error) {
                console.error('Ошибка при создании чата', error);
            }
        });
    });

    // Обработчик клика на чат
    $('.elem-chat-block').on('click', function() {
        const chatId = $(this).data('chat-id');
        loadChat(chatId);
        $('#chat-messages').data('chat-id', chatId); // Store chat id
    });

    // Функция загрузки чата
    function loadChat(chatId) {
        $.ajax({
            url: `/profile/chat_detail/${chatId}/`,
            method: 'GET',
            success: function(data) {
                $('#chat-list').hide();
                $('#hidden').hide();
                $('#chat-messages').show();
                $('#messages-list').html('');
                $('#chat-with').text(data.specialist);
                $('#avatar-with').attr('src', data.specialist_photo);
                $('#chat-contact').text(data.specialist_contact);
                data.messages.forEach(function(message) {
                    $('#messages-list').append(`
                        <div class="message ${message.sender === data.user ? 'user-message' : 'specialist-message'}">
                            <p>${message.content}</p>
                            <span>${message.timestamp}</span>
                        </div>
                    `);
                });
            },
            error: function(error) {
                console.error('Ошибка при загрузке чата', error);
            }
        });
    }

    // Обработчик клика на кнопку "Назад к чатам"
    $('#back-to-chats').on('click', function() {
        $('#hidden').show();
        $('#chat-messages').hide();
        $('#chat-list').show();
    });

    // Обработчик отправки сообщения
    $('#send-message').on('click', function() {
        const chatId = $('#chat-messages').data('chat-id');
        const messageContent = $('#message-input').val();
        if (messageContent.trim() !== '') {
            $.ajax({
                url: `send_message/`,
                method: 'POST',
                data: {
                    chat_id: chatId,
                    message: messageContent,
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                },
                success: function(data) {
                    $('#message-input').val('');
                    $('#messages-list').append(`
                        <div class="message user-message">
                            <p>${data.message}</p>
                            <span>${data.timestamp}</span>
                        </div>
                    `);
                },
                error: function(error) {
                    console.error('Ошибка при отправке сообщения', error);
                }
            });
        }
    });

    // Получаем CSRF-токен из куки
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

    // Открытие и закрытие модального окна
    var modal = document.getElementById('modal');
    var btn = document.getElementById('settingsButton');
    var span = document.getElementsByClassName('close-button')[0];
    var btn_logout = document.getElementById('logout-button');

    btn_logout.onclick = function() {
    $.ajax({
        type: 'POST',
        url: '/users/logout/',
        headers: {
            'X-CSRFToken': csrftoken // Добавляем CSRF-токен в заголовки запроса
        },
        success: function() {
            window.location.href = '../accounts'; // Перенаправляем пользователя на страницу авторизации после успешного выхода
        },
        error: function() {
            alert('Ошибка при выходе из аккаунта. Пожалуйста, попробуйте снова.');
        }
    });
};

    btn.onclick = function() {
        modal.style.display = 'block';
    }

    span.onclick = function() {
        modal.style.display = 'none';
    }

    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }

    // Обработка формы редактирования профиля
    $('#profile-form').submit(function(e) {
        e.preventDefault(); // Предотвращаем отправку формы по умолчанию

        const formData = new FormData(this); // Используем FormData для обработки файлов
        formData.append('csrfmiddlewaretoken', '{{ csrf_token }}'); // Добавляем CSRF токен

        $.ajax({
            type: 'POST',
            url: '/profile/update_profile/',
            data: formData,
            processData: false, // Не обрабатываем данные
            contentType: false, // Не устанавливаем тип контента
            success: function(response) {
                if (response.status === 'success') {
                    // Обновляем данные на странице, если нужно
                    updatePage(response);
                } else {
                    console.error('Ошибка при обновлении профиля', response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Ошибка при обновлении профиля', error);
            }
        });
    });

    function updatePage(response) {
        if (response.status === 'success') {
            $('#avatar-preview').attr('src', response.avatar_url);
            $('#name').val(response.name);
            $('#last_name').val(response.last_name);
            $('#email').val(response.email);

            // Обновляем отображаемые данные на странице
            $('#profile-avatar').attr('src', response.avatar_url);
            $('#profile-name').text(response.name);
            $('#profile-last-name').text(response.last_name);
            $('#profile-email').text(response.email);
        } else {
            console.error('Ошибка при обновлении данных профиля');
        }
    }

    // Обработчик загрузки аватара
    $('#photo').on('change', function(event) {
        const file = event.target.files[0];
        const reader = new FileReader();

        reader.onload = function(e) {
            $('#avatar-preview').attr('src', e.target.result);
        }

        if (file) {
            reader.readAsDataURL(file);
        }
    });
});
