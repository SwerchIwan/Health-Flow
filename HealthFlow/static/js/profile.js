$(document).ready(function() {
    function csrfToken() {
        var inputToken = $('input[name="csrfmiddlewaretoken"]').first().val();
        if (inputToken) return inputToken;
        var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    $('.stars input').on('change', function() {
        const rating = $(this).val();
        const specialistContact = $('#chat-contact').text();

        if (specialistContact) {
            $.ajax({
                url: '/profile/set_rating/',
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken() },
                data: {
                    'specialist_contact': specialistContact,
                    'rating': rating
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


    function escapeHtml(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function formatDate(value) {
        if (!value) return '';
        const d = new Date(value);
        if (isNaN(d.getTime())) return value;
        return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
    }

    function metricRow(label, value) {
        if (value === null || value === undefined || value === '') return '';
        return `<dt>${label}</dt><dd>${escapeHtml(value)}</dd>`;
    }

    function noteFullHtml(note) {
        const b = note.blood_data || {};
        const p = note.pressure_data || {};
        const m = note.bmi_data || {};
        const groups = [];
        const bloodRows = metricRow('Гемоглобин, г/л', b.hemoglobin) +
            metricRow('Лейкоциты, 10⁹/л', b.leukocytes) +
            metricRow('Лимфоциты, %', b.lymphocytes);
        const pressureRows = metricRow('Систолическое, мм рт. ст.', p.systolic) +
            metricRow('Диастолическое, мм рт. ст.', p.diastolic) +
            metricRow('Пульс, уд/мин', p.pulse_rate);
        const bmiRows = metricRow('Рост, см', m.height) + metricRow('Вес, кг', m.weight);
        if (bloodRows) groups.push(`<div class="note-group"><h4>Анализы крови</h4><dl>${bloodRows}</dl></div>`);
        if (pressureRows) groups.push(`<div class="note-group"><h4>Давление и пульс</h4><dl>${pressureRows}</dl></div>`);
        if (bmiRows) groups.push(`<div class="note-group"><h4>ИМТ</h4><dl>${bmiRows}</dl></div>`);
        return `<div class="full-note-item">
            <div class="full-note-item__head">
                <h3>${escapeHtml(formatDate(note.date))}</h3>
                <button type="button" class="full-note-item__close" id="close-full-note">Закрыть</button>
            </div>
            <p class="full-note-item__text">${note.additional_notes ? escapeHtml(note.additional_notes) : 'Без описания'}</p>
            ${groups.length ? `<div class="note-groups">${groups.join('')}</div>` : ''}
        </div>`;
    }

    function noteCardHtml(note) {
        const b = note.blood_data || {};
        const p = note.pressure_data || {};
        const m = note.bmi_data || {};
        const metrics = [];
        if (p.systolic) metrics.push(`<span class="metric metric--pressure"><b>${escapeHtml(p.systolic)}/${escapeHtml(p.diastolic || '—')}</b> давление</span>`);
        if (b.hemoglobin) metrics.push(`<span class="metric metric--blood"><b>${escapeHtml(b.hemoglobin)}</b> Hb</span>`);
        if (m.weight) metrics.push(`<span class="metric metric--bmi"><b>${escapeHtml(m.weight)}</b> кг</span>`);
        const text = note.additional_notes
            ? escapeHtml(note.additional_notes).slice(0, 120)
            : '<span class="note-item__text--muted">Без описания</span>';
        return `<article class="note-item" data-note-id="${note.note_id}" tabindex="0">
            <header class="note-item__head">
                <time class="note-item__date">${escapeHtml(formatDate(note.date))}</time>
                <span class="note-item__chevron" aria-hidden="true">›</span>
            </header>
            <p class="note-item__text">${text}</p>
            <div class="note-item__metrics">${metrics.join('')}</div>
        </article>`;
    }

    let notesSnapshot = null;

    // Делегирование событий для клика на заметку
    $('#notes-container').on('click', '.note-item', function() {
        const noteId = $(this).data('note-id');
        $.ajax({
            url: `/profile/get_note_details/${noteId}/`,
            method: 'GET',
            success: function(response) {
                if (notesSnapshot === null) {
                    notesSnapshot = $('#notes-container').html();
                }
                $('#notes-container').html(noteFullHtml(response));
            },
            error: function(error) {
                console.error('Ошибка при загрузке заметки', error);
            }
        });
    });

    $('#notes-container').on('click', '#close-full-note', function(e) {
        e.stopPropagation();
        if (notesSnapshot !== null) {
            $('#notes-container').html(notesSnapshot);
            notesSnapshot = null;
        }
    });

    $('#note-file').on('change', function() {
        $('#note-file-name').text(this.files.length ? this.files[0].name : 'Файл не выбран');
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
                    notesSnapshot = null;
                    $('#notes-container .notes-empty').remove();
                    $('#notes-container').prepend(noteCardHtml(response));
                    $('#notes-container').scrollTop(0);
                    // Очищаем поля формы
                    $('#note-date').val('');
                    $('#additional-notes').val('');
                    $('#note-file').val('');
                    $('#note-file-name').text('Файл не выбран');
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
                url: `/search_specialist/?q=${encodeURIComponent(query)}`,
                method: 'GET',
                success: function(data) {
                    $('#search-results').html('');
                    if (data.specialists.length > 0) {
                        data.specialists.forEach(function(specialist) {
                            $('#search-results').append(`
                                <div class="search-result" data-specialist-id="${specialist.id}">
                                    <p>${escapeHtml(specialist.name)}</p>
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

    function updateChatsChip(delta) {
        const $chip = $('.chats-head .chip');
        const current = parseInt($chip.text(), 10);
        if (isNaN(current)) return;
        const count = Math.max(0, current + delta);
        let word = 'ов';
        if (count % 10 === 1 && count % 100 !== 11) word = '';
        else if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) word = 'а';
        $chip.text(`${count} диалог${word}`);
    }

    function chatRowHtml(data) {
        const photo = data.specialist_photo || '/static/css/img/default-avatar.svg';
        return `
            <div class="chat-row all-chats" data-chat-id="${data.chatId}">
                <div class="chat-row__avatar">
                    <img class="avatar" src="${escapeHtml(photo)}" alt="">
                </div>
                <div class="chat-row__body">
                    <p class="chat-row__name">${escapeHtml(data.specialist_name)}</p>
                    <p class="chat-row__last">Нет сообщений</p>
                </div>
                <button class="btn btn--icon btn--ghost delete" type="button" aria-label="Удалить чат">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6"/></svg>
                </button>
            </div>`;
    }

    // Обработчик клика на результат поиска специалиста
    $('#search-results').on('click', '.search-result', function() {
        openChatWithSpecialist($(this).data('specialist-id'));
    });

    // Переход из каталога: /profile/?specialist=<id>
    const catalogSpecialistId = new URLSearchParams(window.location.search).get('specialist');
    if (catalogSpecialistId) {
        openChatWithSpecialist(catalogSpecialistId);
        window.history.replaceState({}, '', window.location.pathname);
    }

    function openChatWithSpecialist(specialistId) {
        $.ajax({
            url: '/profile/start_chat/',
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken() },
            data: {
                specialist_id: specialistId
            },
            success: function(data) {
                if (data.status !== 'success') return;
                $('#chat-messages').data('chat-id', data.chatId);
                $('#chat-with').text(data.specialist_name);
                $('#avatar-with').attr('src', data.specialist_photo);
                $('#messages-list').html('');
                $('#average-rating').text('');

                if (!$(`#chat-list .chat-row[data-chat-id="${data.chatId}"]`).length) {
                    $('#chat-list .empty').remove();
                    $('#chat-list').prepend(chatRowHtml(data));
                    updateChatsChip(1);
                }

                $('#search-specialist').val('');
                $('#search-results').hide();
                loadChat(data.chatId);
            },
            error: function(xhr) {
                console.error('Ошибка при создании чата', xhr.status, xhr.responseText);
            }
        });
    }

$(document).on('click', '.all-chats', function() {
    const chatId = $(this).data('chat-id');
    loadChat(chatId);
});

// Функция загрузки чата
    function loadChat(chatId) {
        $.ajax({
            url: `/profile/chat_detail/${encodeURIComponent(chatId)}/`,
            method: 'GET',
            success: function(data) {
                $('#chat-list').hide();
                $('#hidden').hide();
                $('#notes-picker').hide();
                $('#chat-messages').show();
                $('#messages-list').html('');
                $('#chat-with').text(data.specialist);
                $('#avatar-with').attr('src', data.specialist_photo);
                $('#chat-contact').text(data.specialist_contact);
                $('#average-rating').text("Средний рейтинг: " + data.average_rating);
                $('#chat-messages').data('chat-id', chatId);
                var currentUser = data.user;

                $('#messages-list').empty();
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
                    appendChatMessage(message.content, message.timestamp, message.sender === currentUser);
                });
            },
            error: function(error) {
                console.error('Ошибка при загрузке чата', error);
            }
        });
    }

    $(document).on('click', '.delete', function(event) {
    event.stopPropagation();
    const chatBlock = $(this).closest('.chat-row');
    const chatId = chatBlock.data('chat-id');
    if (!chatId) return;

    if (confirm('Вы уверены, что хотите удалить этот чат?')) {
        $.ajax({
            url: `/profile/delete_chat/${encodeURIComponent(chatId)}/`,
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken() },
            success: function(data) {
                if (data.status === 'success') {
                    if ($('#chat-messages').data('chat-id') == chatId) {
                        $('#chat-messages').data('chat-id', '').hide();
                        $('#chat-list').show();
                    }
                    chatBlock.remove();
                    updateChatsChip(-1);
                    if (!$('#chat-list .chat-row').length && !$('#chat-list .empty').length) {
                        $('#chat-list').append('<div class="empty"><p>Пока нет чатов. Найдите специалиста через поиск выше.</p></div>');
                    }
                } else {
                    alert('Ошибка при удалении чата: ' + data.message);
                }
            },
            error: function(xhr) {
                console.error('Ошибка при удалении чата', xhr.status, xhr.responseText);
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
                url: '/profile/send_message/',
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken() },
                data: {
                    chat_id: chatId,
                    message: messageContent
                },
                success: function(data) {
                    $('#message-input').val('');
                    appendChatMessage(data.message, data.timestamp, true);
                    updateChatPreview(chatId, data.message);
                },
                error: function(error) {
                    console.error('Ошибка при отправке сообщения', error);
                }
            });
        }
    });

    function appendChatMessage(content, timestamp, isMine) {
        const $msg = $('<div>').addClass('message ' + (isMine ? 'user-message' : 'specialist-message'));
        $('<p>').text(content).appendTo($msg);
        if (timestamp) $('<span>').text(timestamp).appendTo($msg);
        $('#messages-list').append($msg);
        const list = document.getElementById('messages-list');
        list.scrollTop = list.scrollHeight;
    }

    function updateChatPreview(chatId, text) {
        $(`#chat-list .chat-row[data-chat-id="${chatId}"] .chat-row__last`).text(text);
    }

    // Отправка заметок и анализов из профиля
    function notesPickerError(text) {
        $('#notes-picker-error').text(text || '');
    }

    function setNotesPickerBusy(busy) {
        $('#notes-picker-send').prop('disabled', busy).text(busy ? 'Отправка…' : 'Отправить');
    }

    $('#attach-notes').on('click', function() {
        const chatId = $('#chat-messages').data('chat-id');
        if (!chatId) return;

        const $picker = $('#notes-picker');
        if ($picker.is(':visible')) {
            $picker.hide();
            return;
        }

        notesPickerError('');
        $('#notes-picker-list').html('<p class="notes-picker__loading">Загружаем заметки…</p>');
        $picker.show();

        $.ajax({
            url: '/profile/notes/',
            method: 'GET',
            success: function(data) {
                const $list = $('#notes-picker-list').empty();
                if (!data.notes.length) {
                    $list.html(`<div class="empty">Заметок пока нет. Добавьте их в разделе «Настройки → Заметки».</div>`);
                    return;
                }
                data.notes.forEach(function(note) {
                    const chips = [];
                    if (note.pressure && note.pressure.systolic) {
                        chips.push(`<span class="metric metric--pressure"><b>${note.pressure.systolic}/${note.pressure.diastolic}</b> давление</span>`);
                    }
                    if (note.blood && note.blood.hemoglobin) {
                        chips.push(`<span class="metric metric--blood"><b>${escapeHtml(note.blood.hemoglobin)}</b> Hb</span>`);
                    }
                    if (note.bmi && note.bmi.weight) {
                        chips.push(`<span class="metric metric--bmi"><b>${escapeHtml(note.bmi.weight)}</b> кг</span>`);
                    }
                    const preview = note.text
                        ? escapeHtml(note.text.length > 90 ? note.text.slice(0, 90) + '…' : note.text)
                        : '<span class="note-item__text--muted">Без описания</span>';
                    $list.append(`
                        <label class="notes-picker__item">
                            <input type="checkbox" class="notes-picker__check" value="${note.id}">
                            <span class="notes-picker__body">
                                <span class="notes-picker__date">${escapeHtml(note.date)}${note.file_name ? ' · 📎' : ''}</span>
                                <span class="notes-picker__text">${preview}</span>
                                <span class="note-item__metrics">${chips.join('')}</span>
                            </span>
                        </label>`);
                });
            },
            error: function() {
                notesPickerError('Не удалось загрузить заметки.');
                $('#notes-picker-list').empty();
            }
        });
    });

    $('#notes-picker-close').on('click', function() {
        $('#notes-picker').hide();
    });

    $('#notes-picker-list').on('change', '.notes-picker__check', function() {
        const checked = $('#notes-picker-list .notes-picker__check:checked');
        if (checked.length >= 10) {
            $(this).prop('checked', false);
            notesPickerError('За один раз можно отправить до 10 заметок.');
            return;
        }
        notesPickerError('');
    });

    $('#notes-picker-send').on('click', function() {
        const chatId = $('#chat-messages').data('chat-id');
        const noteIds = $('#notes-picker-list .notes-picker__check:checked').map(function() { return this.value; }).get();
        const comment = $('#notes-picker-comment').val().trim();

        if (!noteIds.length && !comment) {
            notesPickerError('Выберите заметку или напишите комментарий.');
            return;
        }

        setNotesPickerBusy(true);
        notesPickerError('');
        $.ajax({
            url: `/profile/send_notes/${encodeURIComponent(chatId)}/`,
            method: 'POST',
            headers: { 'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').first().val() },
            data: { note_ids: noteIds, comment: comment },
            traditional: true,
            success: function(data) {
                if (data.status !== 'success') {
                    notesPickerError(data.error || 'Не удалось отправить.');
                    return;
                }
                loadChat(chatId);
                updateChatPreview(chatId, comment || 'Заметка из профиля');
                $('#notes-picker').hide();
                $('#notes-picker-comment').val('');
            },
            error: function(xhr) {
                let message = 'Не удалось отправить заметки.';
                try { message = JSON.parse(xhr.responseText).error || message; } catch (e) {}
                notesPickerError(message);
            },
            complete: function() {
                setNotesPickerBusy(false);
            }
        });
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

    function openModal() {
        modal.classList.add('is-open');
        modal.style.display = 'block';
    }

    function closeModal() {
        modal.classList.remove('is-open');
        modal.style.display = 'none';
    }

    btn.onclick = openModal;

    var openSettingsBtn = document.getElementById('openSettingsBtn');
    if (openSettingsBtn) {
        openSettingsBtn.onclick = openModal;
    }

    span.onclick = closeModal;

    window.onclick = function(event) {
        if (event.target == modal) {
            closeModal();
        }
    }

    document.querySelectorAll('.modal__tab').forEach(function(tab) {
        tab.onclick = function() {
            document.querySelectorAll('.modal__tab').forEach(function(t) { t.classList.remove('is-active'); });
            document.querySelectorAll('.modal__panel').forEach(function(p) { p.hidden = true; });
            tab.classList.add('is-active');
            document.getElementById(tab.dataset.tab).hidden = false;
        };
    });

    // Обработка формы редактирования профиля
    $('#profile-form').submit(function(e) {
        e.preventDefault(); // Предотвращаем отправку формы по умолчанию

        const formData = new FormData(this);

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
            $('#aside-avatar').attr('src', response.avatar_url);
            $('#profile-name').text(response.name);
            $('#aside-name').text(response.name + ' ' + (response.last_name || ''));
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


function redirectToTelegram() {
    window.open("https://t.me/HealthFlow_bot", "_blank");
}
