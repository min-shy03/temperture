const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
// 학기 선택 기능
const gradeSelect = document.getElementById('grade-select');
const semesterSelect = document.getElementById('semester-select');

function changeTimeTable() {
    if (gradeSelect && semesterSelect) {
        const selectedGrade = gradeSelect.value;
        const selectedSemester = semesterSelect.value;

        const newUrl = `/time-table/?grade=${selectedGrade}&semester=${selectedSemester}`;

        window.location.href = newUrl;
    }
}

if (gradeSelect) {
    gradeSelect.addEventListener('change', changeTimeTable);
}

if (semesterSelect) {
    semesterSelect.addEventListener('change', changeTimeTable);
}


// 시간표 수정 기능
const editButton = document.querySelector('.time-table-edit');
const timeTable = document.querySelector('.time-table');
const allCells = document.querySelectorAll('.time-table-class');
const modalForm = document.getElementById('time-table-modal-form');
const modalBackdrop = document.querySelector('.edit-modal-backdrop');
const modalCloseButton = document.querySelector('.close-modal-btn');
const modalCellInfo = document.querySelector('#time-table-cell-info');
const modalDayInput = document.getElementById('time-table-modal-day');
const modalPeriodInput = document.getElementById('time-table-modal-period');
const modalLectureInput = document.getElementById('time-table-modal-lecture');
const modalProfInput = document.getElementById('time-table-modal-professor');
const modalRoomInput = document.getElementById('time-table-modal-classroom');
const modalDeleteBtn = document.querySelector('.delete-btn');
const colorSwatchesContainer = document.querySelector('.color-swatches')
const allColorSwatches = colorSwatchesContainer ? colorSwatchesContainer.querySelectorAll('.color-swatch') : [];
const hiddenColorInput = document.getElementById('modal-color')

function openEditModal(event) {
    const clickedCell = event.currentTarget;
    const day = clickedCell.dataset.day;
    const period = clickedCell.dataset.period;

    let dayKorean = day;
    if (day === 'mon') dayKorean = '월';
    else if (day === 'tue') dayKorean = '화';
    else if (day === 'wed') dayKorean = '수';
    else if (day === 'thu') dayKorean = '목';
    else if (day === 'fri') dayKorean = '금';

    modalCellInfo.textContent = `${dayKorean}요일 ${period}교시`

    if (modalDayInput) modalDayInput.value = day;
    if (modalPeriodInput) modalPeriodInput.value = period;

    if (modalLectureInput) modalLectureInput.value = clickedCell.dataset.lectureName || '';
    if (modalProfInput) modalProfInput.value = clickedCell.dataset.professor || '';
    if (modalRoomInput) modalRoomInput.value = clickedCell.dataset.classroom || '';

    const currentColor = clickedCell.dataset.color || '#FFFFFF';
    if (hiddenColorInput) {
        hiddenColorInput.value = currentColor;
    }

    allColorSwatches.forEach(button => {
        if (button.dataset.color === currentColor) {
            button.classList.add('selected');
        } else {
            button.classList.remove('selected');
        }
    });

    if (modalBackdrop) {
        modalBackdrop.classList.add('show');
    }
}

function closeModal() {
    if (modalBackdrop) {
        modalBackdrop.classList.remove('show');
    }
}

function enterEditMode(event) {
    alert("시간표를 수정합니다.")

    timeTable.classList.add('time-table-edit-mode');
    editButton.innerText = "시간표 수정완료";

    allCells.forEach(cell => {
        cell.addEventListener('click', openEditModal);
    })

    editButton.removeEventListener('click', enterEditMode);
    editButton.addEventListener('click', exitEditMode);
}

function exitEditMode() {
    alert("시간표 수정을 마칩니다.")

    timeTable.classList.remove('time-table-edit-mode');
    editButton.innerText = "시간표 수정하기";

    allCells.forEach(cell => {
        cell.removeEventListener('click', openEditModal);
    })

    editButton.removeEventListener('click', exitEditMode);
    editButton.addEventListener('click', enterEditMode);
}

function handleColorSelect(event) {
    console.log("handleColorSelect 함수 실행됨! 클릭된 버튼:", event.currentTarget);
    const selectedButton = event.currentTarget;
    const selectedColor = selectedButton.dataset.color;

    allColorSwatches.forEach(button => {
        button.classList.remove('selected');
    })

    selectedButton.classList.add('selected');

    if (hiddenColorInput) {
        hiddenColorInput.value = selectedColor;
    }
}

allColorSwatches.forEach(button => {
    button.addEventListener('click', handleColorSelect);
})

// 비동기 함수를 이용해 데이터 통신 (async = 이 함수가 비동기 함수임을 알리는 장치)
async function handleFormSubmit(event) {
    event.preventDefault();

    const formData = new FormData(modalForm);
    const data = Object.fromEntries(formData.entries());
    const headers = {
        'Content-Type': 'application/json',
    };

    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }

    try {
        const response = await fetch('/time-table/api/update', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.message || '서버 저장 실패');
        }

        console.log("서버 응답 :", result);
        alert(result.message || '저장 완료');

        const targetCell = document.querySelector(`td[data-day="${data.day}"][data-period="${data.period}"]`);
        if (targetCell) {
            targetCell.innerHTML = `
                <div style="background-color: ${data.color}; padding: 5px; border-radius: 4px; height: 100%;">
                    <p>${data.lecture_name}</p>
                    <p>${data.professor}</p>
                    <p>${data.classroom}</p>
                </div>
            `;

            targetCell.dataset.lectureName = data.lecture_name;
            targetCell.dataset.professor = data.professor;
            targetCell.dataset.classroom = data.classroom;
            targetCell.dataset.color = data.color;
        }

        closeModal();

    } catch (error) {
        console.error("저장 중 오류:", error);
        alert(`저장 실패: ${error.message}`)
    }
}

async function handleDelete() {
    const grade = document.getElementById('time-table-modal-grade').value;
    const semester = document.getElementById('time-table-modal-semester').value;
    const day = modalDayInput.value;
    const period = modalPeriodInput.value;

    const data = { grade, semester, day, period };
    console.log("삭제 - 서버로 전송할 데이터:", data);

    const headers = {
        'Content-Type': 'application/json',
    };

    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }

    try {
        const response = await fetch('/time-table/api/delete', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });

        const result = await response.json()

        if (!response.ok || !result.success) {
            throw new Error(result.message || '서버 삭제 실패');
        }

        console.log("서버 응답:", result);
        alert(result.message || '삭제 완료');

        const targetCell = document.querySelector(`td[data-day="${data.day}"][data-period="${data.period}"]`);
        if (targetCell) {
            targetCell.innerHTML = '';
            targetCell.style.backgroundColor = '';

            delete targetCell.dataset.lectureName;
            delete targetCell.dataset.professor;
            delete targetCell.dataset.classroom;
            delete targetCell.dataset.color;
        }

        closeModal();

    } catch (error) {
        console.error("삭제 중 오류:", error);
        alert(`삭제 실패: ${error.message}`);
    }
}

if (editButton) {
    editButton.addEventListener('click', enterEditMode);
}

if (modalCloseButton) {
    modalCloseButton.addEventListener('click', closeModal);
}

if (modalForm) {
    modalForm.addEventListener('submit', handleFormSubmit);
}

if (modalDeleteBtn) {
    modalDeleteBtn.addEventListener('click', handleDelete);
}