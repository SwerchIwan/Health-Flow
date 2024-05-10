document.addEventListener("DOMContentLoaded", function() {
    const btnLightTheme = document.querySelector(".change-color .button:nth-child(1)");
    const btnDarkTheme = document.querySelector(".change-color .button:nth-child(2)");
    const animation = new GradientAnimation(); // Создаем экземпляр анимации

    // Обработчик события для кнопки светлой темы
    btnLightTheme.addEventListener("click", function() {
        animation.setTheme("light");
    });

    // Обработчик события для кнопки темной темы
    btnDarkTheme.addEventListener("click", function() {
        animation.setTheme("dark");
    });
});

class GradientAnimation {
    constructor() {
        this.cnv = document.querySelector(`canvas`);
        this.ctx = this.cnv.getContext(`2d`);
        this.targetCompositeMode = "lighter"; // Новое свойство для хранения целевого режима наложения градиента
        // Устанавливаем ширину и высоту canvas
        this.cnv.width = window.innerWidth;
        this.cnv.height = 1080;

        // Масштабируем ctx
        this.ctx.scale(this.cnv.width / window.innerWidth, 1080 / this.cnv.height);

        this.circlesNum = 15;
        this.minRadius = 900;
        this.maxRadius = 900;
        this.speed = .003;

        this.createCircles();
        this.drawAnimation();
        this.setTheme("light");
    }

    setTheme(theme) {
    if (theme === "light") {
        this.compositeMode = "lighter";
        document.body.style.backgroundColor = "#ffffff"; // Светлая тема
    } else if (theme === "dark") {
        this.compositeMode = "color-burn";
        document.body.style.backgroundColor = "#000000"; // Темная тема
        this.cnv.style.opacity = 0.5; // Уменьшаем прозрачность канваса до половины
    }
    this.drawAnimation(); // Перерисовываем анимацию после изменения темы
}


    createCircles() {
        this.circles = [];
        for (let i = 0; i < this.circlesNum; ++i) {
            this.circles.push(new Circle(this.cnv.width, this.cnv.height, this.minRadius, this.maxRadius));
        }
    }

    drawCircles() {
        this.circles.forEach(circle => circle.draw(this.ctx, this.speed, this.compositeMode));
    }

    clearCanvas() {
        this.ctx.clearRect(0, 0, this.cnv.width, this.cnv.height);
    }

    drawAnimation() {
        this.clearCanvas();
        this.drawCircles();
        window.requestAnimationFrame(() => this.drawAnimation());
    }
}

class Circle {
    constructor(w, h, minR, maxR) {
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.angle = Math.random() * Math.PI * 2;
        this.radius = Math.random() * (maxR - minR) + minR;
        this.firstColor = `hsla(${Math.random() * 360}, 100%, 50%, 1)`;
        this.secondColor = 'hsla(199, 45%, 47%, 0)';
    }
    draw(ctx, speed, compositeMode) {
        this.angle += speed;
        const x = this.x + Math.cos(this.angle) * 200;
        const y = this.y + Math.sin(this.angle) * 200;
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, this.radius);
        gradient.addColorStop(0, this.firstColor);
        gradient.addColorStop(1, this.secondColor);

        ctx.globalCompositeOperation = compositeMode; // Устанавливаем режим наложения

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, this.radius, 0, Math.PI * 2);
        ctx.fill();
    }
}

window.onload = () => {
    new GradientAnimation();
}

