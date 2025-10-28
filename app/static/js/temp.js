const editButton = document.querySelector('.temp-class-edit');
const modalBackdrop = document.querySelector('.edit-modal-backdrop');
const closeModalButton = document.querySelector('.close-modal-btn');
const currentTemp = document.getElementById('current-temp');
const currentHumi = document.getElementById('current-humi');

const eventSource = new EventSource(streamUrl);

console.log(streamUrl);

eventSource.addEventListener('message', function (event) {
    try {
        const data = JSON.parse(event.data);

        if (currentTemp && data.temp !== null && data.temp !== undefined) {
            currentTemp.textContent = `${data.temp.toFixed(1)}℃`;
        } else if (currentTemp) {
            currentTemp.textContent = "- ℃";
        }

        if (currentHumi && data.humi !== null && data.humi !== undefined) {
            currentHumi.textContent = `${data.humi.toFixed(1)}%`;
        } else if (currentHumi) {
            currentHumi.textContent = "- %";
        }
    } catch (error) {
        console.error("SSE 데이터 처리 오류 :", error)
    }
})

function openEditModal() {
    if (modalBackdrop) {
        modalBackdrop.classList.add('show');
    }
}

function closeModal() {
    if (modalBackdrop) {
        modalBackdrop.classList.remove('show');
    }
}

if (editButton) {
    editButton.addEventListener('click', openEditModal);
}

if (closeModalButton) {
    closeModalButton.addEventListener('click', closeModal);
}