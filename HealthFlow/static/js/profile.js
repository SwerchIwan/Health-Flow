$(document).ready(function() {
    $('.stars input').on('change', function() {
        const rating = $(this).val();
        const specialistContact = $('#chat-contact').text();

        if (specialistContact) {
            $.ajax({
                url: '/profile/set_rating/',
                method: 'POST',
                data: {
                    'specialist_contact': specialistContact,
                    'rating': rating,
                    'csrfmiddlewaretoken': '{{ csrf_token }}'
                },
                success: function(data) {
                    if (data.status === 'success') {
                        $('#average-rating').text('Рейтинг специалиста: ' + data.new_average_rating);

                    // Показать элемент .result и установить таймер для его скрытия
                    const resultElement = $('.stars .result');
                    resultElement.show().css('opacity', '1');

                    setTimeout(function() {
                        resultElement.fadeOut(); // Используем jQuery fadeOut для скрытия
                    }, 1000); // 3000 миллисекунд = 3 секунды
                    } else {
                        console.error('Ошибка при сохранении рейтинга:', data.message);
                    }
                },
                error: function(error) {
                    console.error('Ошибка при сохранении рейтинга', error);
                }
            });
        } else {
            console.error('Specialist ID is not defined.');
        }
    });


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
                        <input id="close-full-note" type="button" value="Закрыть" />
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

        var formData = new FormData(this); // Используем FormData для отправки файлов
        formData.append('csrfmiddlewaretoken', $('input[name="csrfmiddlewaretoken"]').val());

        // Отправляем данные формы на сервер
        $.ajax({
            type: 'POST',
            url: '/profile/add_note/',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                console.log(response); // Логируем ответ сервера для отладки
                if (response.status === 'success' && response.note_id) {
                    // При успешном добавлении заметки обновляем страницу или ее часть
                    $('#notes-container').append(
                        `<div class="note-item" data-note-id="${response.note_id}">
                            <h3>${response.date}</h3>
                            <div class="note-content" style="display: none;">
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
                console.error('Ошибка при отправке данных на сервер', error);
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
                // Обновляем данные о чате
                $('#chat-messages').data('chat-id', data.chatId);
                $('#chat-with').text(data.specialist_name);
                $('#avatar-with').attr('src', data.specialist_photo);
                $('#messages-list').html('');
                $('#average-rating').text('');

                $('#search-results').hide();
                loadChat(data.chatId);
            }
        },
        error: function(error) {
            console.error('Ошибка при создании чата', error);
        }
    });
});

$(document).on('click', '.all-chats', function() {
    const chatId = $(this).data('chat-id');
    loadChat(chatId);
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
                $('#average-rating').text("Средний рейтинг: " + data.average_rating);
                $('#chat-messages').data('chat-id', chatId);
                var currentUser = data.user;

                $('.stars').attr('data-current-rating', data.user_rating);

                // Получаем значение user_rating из атрибута data-current-rating
                const userRating = $('.stars').attr('data-current-rating');

                // Сначала сбросим все звезды
                $('.stars input').prop('checked', false);

                // Устанавливаем атрибут checked в зависимости от значения user_rating
                if (userRating) {
                    $(`.stars input[value="${userRating}"]`).prop('checked', true);
                }

                    // Показать элемент .result и установить таймер для его скрытия
                    const resultElement = $('.stars .result');
                    resultElement.show().css('opacity', '1');

                    setTimeout(function() {
                        resultElement.fadeOut(); // Используем jQuery fadeOut для скрытия
                    }, 1000); // 3000 миллисекунд = 3 секунды

                data.messages.forEach(function(message) {
                    $('#messages-list').append(`
                        <div class="message ${message.sender === currentUser ? 'user-message' : 'specialist-message'}">
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

    $(document).on('click', '.delete', function(event) {
    event.stopPropagation(); // Останавливаем всплытие события
    const chatBlock = $(this).closest('.elem-chat-block');
    const chatId = chatBlock.data('chat-id');

    if (confirm('Вы уверены, что хотите удалить этот чат?')) {
        $.ajax({
            url: `/profile/delete_chat/${chatId}/`,
            method: 'POST',
            data: {
                'csrfmiddlewaretoken': '{{ csrf_token }}'
            },
            success: function(data) {
                if (data.status === 'success') {
                    chatBlock.remove();
                    alert('Чат успешно удален.');
                } else {
                    alert('Ошибка при удалении чата: ' + data.message);
                }
            },
            error: function(error) {
                console.error('Ошибка при удалении чата', error);
                alert('Ошибка при удалении чата.');
            }
        });
    }
});

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

document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('bmiChart').getContext('2d');

    fetch('get_bmi_data/')
        .then(response => response.json())
        .then(data => {
            const bmiChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        {
                            label: 'Вес (кг)',
                            data: data.weights,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            fill: true,
                            pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: 'rgba(75, 192, 192, 1)'
                        },
                        {
                            label: 'Рост (м)',
                            data: data.heights,
                            borderColor: 'rgba(153, 102, 255, 1)',
                            backgroundColor: 'rgba(153, 102, 255, 0.2)',
                            fill: true,
                            pointBackgroundColor: 'rgba(153, 102, 255, 1)',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: 'rgba(153, 102, 255, 1)'
                        },
                        {
                            label: 'Гемоглобин',
                            data: data.hemoglobin,
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            fill: true,
                            pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: 'rgba(255, 99, 132, 1)'
                        },
                        {
                            label: 'Лейкоциты',
                            data: data.leukocytes,
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            fill: true,
                            pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                        },
                        {
                            label: 'Лимфоциты',
                            data: data.lymphocytes,
                            borderColor: 'rgba(255, 206, 86, 1)',
                            backgroundColor: 'rgba(255, 206, 86, 0.2)',
                            fill: true,
                            pointBackgroundColor: 'rgba(255, 206, 86, 1)',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: 'rgba(255, 206, 86, 1)'
                        },
                        {
                            label: 'Систолическое давление',
                            data: data.systolic,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            fill: true,
                            pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: 'rgba(75, 192, 192, 1)'
                        },
                        {
                            label: 'Диастолическое давление',
                            data: data.diastolic,
                            borderColor: 'rgba(153, 102, 255, 1)',
                            backgroundColor: 'rgba(153, 102, 255, 0.2)',
                            fill: true,
                            pointBackgroundColor: 'rgba(153, 102, 255, 1)',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: 'rgba(153, 102, 255, 1)'
                        },
                        {
                            label: 'Частота пульса',
                            data: data.pulse_rate,
                            borderColor: 'rgba(255, 159, 64, 1)',
                            backgroundColor: 'rgba(255, 159, 64, 0.2)',
                            fill: true,
                            pointBackgroundColor: 'rgba(255, 159, 64, 1)',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: 'rgba(255, 159, 64, 1)'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    title: {
                        display: true,
                        text: 'График изменения параметров по датам',
                        fontSize: 18,
                        fontColor: '#333'
                    },
                    legend: {
                        position: 'top',
                        labels: {
                            fontColor: '#333',
                            fontSize: 12
                        }
                    },
                    scales: {
                        xAxes: [{
                            display: true,
                            scaleLabel: {
                                display: true,
                                labelString: 'Дата',
                                fontColor: '#333'
                            },
                            ticks: {
                                fontColor: '#333'
                            }
                        }],
                        yAxes: [{
                            display: true,
                            ticks: {
                                beginAtZero: true,
                                fontColor: '#333'
                            },
                            scaleLabel: {
                                display: true,
                                labelString: 'Значение',
                                fontColor: '#333'
                            },
                            gridLines: {
                                display: true,
                                color: "rgba(75, 192, 192, 0.2)"
                            }
                        }]
                    },
                    tooltips: {
                        mode: 'index',
                        intersect: false,
                    },
                    hover: {
                        mode: 'nearest',
                        intersect: true
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching BMI data:', error));
});



function redirectToTelegram() {
    window.open("https://t.me/HealthFlow_bot", "_blank");
}
