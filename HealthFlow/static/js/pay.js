document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('payment-form');
    if (!form) return;

    const cardNumber = document.getElementById('card-number');
    const cardName = document.getElementById('card-name-input');
    const validity = document.getElementById('validity-input');
    const cvv = document.getElementById('cvv');

    cardNumber.addEventListener('input', function () {
        const digits = cardNumber.value.replace(/\D/g, '').slice(0, 16);
        cardNumber.value = digits.replace(/(\d{4})(?=\d)/g, '$1 ');
    });

    validity.addEventListener('input', function () {
        const digits = validity.value.replace(/\D/g, '').slice(0, 4);
        validity.value = digits.length > 2 ? digits.slice(0, 2) + '/' + digits.slice(2) : digits;
    });

    cvv.addEventListener('input', function () {
        cvv.value = cvv.value.replace(/\D/g, '').slice(0, 3);
    });

    form.addEventListener('submit', function (event) {
        const numberOk = cardNumber.value.replace(/\D/g, '').length === 16;
        const validOk = /^\d{2}\/\d{2}$/.test(validity.value);
        const cvvOk = cvv.value.length === 3;

        if (!numberOk || !cardName.value.trim() || !validOk || !cvvOk) {
            event.preventDefault();
            let errorBox = document.querySelector('.pay__errors');
            if (!errorBox) {
                errorBox = document.createElement('ul');
                errorBox.className = 'pay__errors';
                form.querySelector('.pay__title').after(errorBox);
            }
            const item = document.createElement('li');
            item.textContent = 'Пожалуйста, проверьте данные карты.';
            errorBox.replaceChildren(item);
        }
    });
});
