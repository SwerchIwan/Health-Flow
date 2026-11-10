document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('bmiChart');
    if (!canvas) return;

    const line = (label, data, rgb) => ({
        label: label,
        data: data,
        borderColor: `rgba(${rgb}, 1)`,
        backgroundColor: `rgba(${rgb}, 0.12)`,
        fill: true,
        tension: 0.35,
        pointRadius: 2,
        pointHoverRadius: 4,
        spanGaps: true
    });

    fetch('/profile/get_bmi_data/')
        .then(response => response.json())
        .then(data => {
            new Chart(canvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        line('Вес (кг)', data.weights, '75, 192, 192'),
                        line('Рост (м)', data.heights, '153, 102, 255'),
                        line('Гемоглобин', data.hemoglobin, '255, 99, 132'),
                        line('Лейкоциты', data.leukocytes, '54, 162, 235'),
                        line('Лимфоциты', data.lymphocytes, '255, 206, 86'),
                        line('Систолическое', data.systolic, '75, 192, 192'),
                        line('Диастолическое', data.diastolic, '153, 102, 255'),
                        line('Пульс', data.pulse_rate, '255, 159, 64')
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { boxWidth: 12, usePointStyle: true, font: { size: 11 } }
                        }
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, font: { size: 10 } } },
                        y: {
                            beginAtZero: false,
                            grid: { color: 'rgba(34, 60, 80, 0.08)' },
                            ticks: { font: { size: 10 } }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching BMI data:', error));
});
