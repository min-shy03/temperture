const gradeSelect = document.getElementById('cleaning-grade-select');

function changeTimeTable() {
    if (gradeSelect) {
        const selectedGrade = gradeSelect.value;

        // select에서 각 학년 선택되면 새로운 url 생성 후 페이지 전환
        const newUrl = `/cleaning/?grade=${selectedGrade}`;

        window.location.href = newUrl;
    }
}

if (gradeSelect) {
    gradeSelect.addEventListener('change', changeTimeTable);
}

const editButton = document.querySelector('.cleaning-member-edit');
const modalBackdrop = document.querySelector('.edit-modal-backdrop');
const closeModalButton = document.querySelector('.close-modal-btn');
const tabButtons = document.querySelectorAll('.modal-tab-btn');
const tabPages = document.querySelectorAll('.modal-tab');

const csrfToken = document.getElementById('csrf_token') ? document.getElementById('csrf_token').value : "";
const modalToast = document.getElementById('modal-toast');
let toastTimer;

const formAdd = document.getElementById('form-add-student');

const formEdit = document.getElementById('form-edit-student');
const editGradeSelect = document.getElementById('edit-grade-select');
const editStudentSelect = document.getElementById('edit-student-select');
const editStudentFields = document.getElementById('edit-student-fields');
const editNameInput = document.getElementById('edit-student-name');
const editGenderInput = document.getElementById('edit-student-gender');
const editPositionInput = document.getElementById('edit-student-position');

const formDelete = document.getElementById('form-delete-student');
const deleteGradeSelect = document.getElementById('delete-grade-select');
const deleteStudentSelect = document.getElementById('delete-student-select');
const deleteStudentFields = document.getElementById('delete-student-fields');
const deleteNameInput = document.getElementById('delete-student-name');
const deletePositionInput = document.getElementById('delete-student-position');

function showMessage(message, isSuccess = false) {
    if (!modalToast) return;
    if (toastTimer) {
        clearTimeout(toastTimer);
    }

    modalToast.textContent = message;

    modalToast.className = 'modal-message';
    modalToast.classList.add(isSuccess ? 'success' : 'error');
    modalToast.classList.add('show');

    // setTimeout() = 특정 시간 뒤에 이 코드를 딱 한 번만 실행해라.
    toastTimer = setTimeout(() => {
        modalToast.classList.remove('show');
    }, 3000);
}

function hideMessage() {
    if (modalToast) {
        modalToast.classList.remove('show');
    }
    if (toastTimer) {
        clearTimeout(toastTimer);
    }
}

function openEditModal() {
    if (modalBackdrop) {
        modalBackdrop.classList.add('show');
    }
}

function closeModal() {
    if (modalBackdrop) {
        modalBackdrop.classList.remove('show');
        resetModalToDefault();
    }
}

if (editButton) {
    editButton.addEventListener('click', openEditModal);
}

if (closeModalButton) {
    closeModalButton.addEventListener('click', closeModal);
}

function resetModalToDefault() {
    // 1. "추가", "수정", "삭제" 폼의 모든 입력값 초기화
    if (formAdd) formAdd.reset();
    if (formEdit) formEdit.reset();
    if (formDelete) formDelete.reset();

    // 2. "수정" 탭 초기화
    const editStudentSelect = document.getElementById('edit-student-select');
    const editStudentFields = document.getElementById('edit-student-fields');
    if (editStudentSelect) {
        // 학생 선택 드롭다운을 "비활성화"
        editStudentSelect.disabled = true;
        // 학생 목록을 기본값으로 되돌림
        editStudentSelect.innerHTML = '<option value="">-- 학생을 선택하세요 --</option>';
    }
    if (editStudentFields) {
        // 하단 폼(이름, 성별, 직위) 숨기기
        editStudentFields.classList.add('hidden');
    }

    // 3. "삭제" 탭 초기화
    const deleteStudentSelect = document.getElementById('delete-student-select');
    const deleteStudentFields = document.getElementById('delete-student-fields');
    if (deleteStudentSelect) {
        // 학생 선택 드롭다운을 "비활성화"
        deleteStudentSelect.disabled = true;
        // 학생 목록을 기본값으로 되돌림
        deleteStudentSelect.innerHTML = '<option value="">-- 학생을 선택하세요 --</option>';
    }
    if (deleteStudentFields) {
        // 하단 폼(이름, 직위) 숨기기
        deleteStudentFields.classList.add('hidden');
    }

    // 4. 떠 있는 토스트 메시지 숨기기
    hideMessage();

    // 5. 기본 탭인 "추가" 탭으로 강제 전환
    switchTab('add');
}

tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        switchTab(tabName);
    });
})

function switchTab(tabName) {
    hideMessage();
    tabButtons.forEach(btn => btn.classList.remove('active'));

    const activeButton = document.querySelector(`.modal-tab-btn[data-tab="${tabName}"]`);
    if (activeButton) activeButton.classList.add('active');

    tabPages.forEach(page => page.classList.remove('active'));

    const activePage = document.getElementById(`tab-${tabName}`);
    if (activePage) activePage.classList.add('active');
}

if (formAdd) {
    formAdd.addEventListener('submit', async function (event) {
        event.preventDefault();
        hideMessage();

        const formData = new FormData(formAdd);
        const studentData = Object.fromEntries(formData.entries());

        if (!studentData.grade || !studentData.name || !studentData.gender || !studentData.position) {
            showMessage('모든 항목을 입력해주세요.', false);
            return;
        }

        try {
            const response = await fetch('/cleaning/api/add-member', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(studentData)
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(result.message, true);
                formAdd.reset();

                const uncheckedList = document.querySelector('.unchecked-box .student-list');
                const newLi = document.createElement('li');
                const newName = studentData.name;
                newLi.textContent = newName;

                if (uncheckedList) {
                    const existingItems = uncheckedList.querySelectorAll('li');

                    let insertionPoint = null;

                    for (const currentItem of existingItems) {
                        const currentName = currentItem.textContent;

                        if (newName.localeCompare(currentName) < 0) {
                            insertionPoint = currentItem;
                            break;
                        }
                    }

                    if (insertionPoint) {
                        uncheckedList.insertBefore(newLi, insertionPoint);
                    } else {
                        uncheckedList.appendChild(newLi);
                    }
                }
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('학생 추가 오류:', error);
            showMessage(error.message || '요청 중 오류가 발생했습니다.', false);
        }
    });
}

if (editGradeSelect) {
    editGradeSelect.addEventListener('change', async function () {
        const grade = editGradeSelect.value;

        editStudentSelect.disabled = true;
        editStudentSelect.innerHTML = '<option value="">-- 학생을 선택하세요 --</option>';
        editStudentFields.classList.add('hidden');
        hideMessage();

        if (!grade) return;

        try {
            const response = await fetch(`/cleaning/api/grade-members?grade=${grade}`);
            if (!response.ok) throw new Error('학생 목록 로드 실패');

            const students = await response.json();

            students.forEach(student => {
                const option = document.createElement('option');
                option.value = student.id;
                option.textContent = `${student.name} (${student.position})`;
                editStudentSelect.appendChild(option);
            });

            editStudentSelect.disabled = false;
        } catch (error) {
            showMessage(error.message, false);
        }
    })
}

if (editStudentSelect) {
    editStudentSelect.addEventListener('change', async function () {
        const studentId = editStudentSelect.value;
        hideMessage();

        if (!studentId) {
            editStudentFields.classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`/cleaning/api/member/${studentId}`);
            if (!response.ok) throw new Error('학생 정보 로드 실패');

            const student = await response.json();

            editNameInput.value = student.name;
            editGenderInput.value = student.gender;
            editPositionInput.value = student.position;

            editStudentFields.classList.remove('hidden');
        } catch (error) {
            showMessage(error.message, false);
        }
    });
}

if (formEdit) {
    formEdit.addEventListener('submit', async function (event) {
        event.preventDefault();
        hideMessage();

        const studentId = editStudentSelect.value;
        if (!studentId) {
            showMessage("수정할 학생을 선택하세요.", false);
            return;
        }

        const updatedData = {
            gender: editGenderInput.value,
            position: editPositionInput.value
        };

        try {
            const response = await fetch(`/cleaning/api/member/${studentId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(updatedData)
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(result.message, true);
                setTimeout(() => {
                    closeModal();
                    window.location.reload();
                }, 2000);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            showMessage(error.message, false);
        }
    });
}

if (deleteGradeSelect) {
    deleteGradeSelect.addEventListener('change', async function () {
        const grade = deleteGradeSelect.value;

        deleteStudentSelect.disabled = true;
        deleteStudentSelect.innerHTML = '<option value="">-- 학생을 선택하세요 --</option>';
        deleteStudentFields.classList.add('hidden');
        hideMessage();

        if (!grade) return;

        try {
            const response = await fetch(`/cleaning/api/grade-members?grade=${grade}`);
            if (!response.ok) throw new Error('학생 목록 로드 실패');

            const students = await response.json();

            students.forEach(student => {
                const option = document.createElement('option');
                option.value = student.id;
                option.textContent = `${student.name} (${student.position})`;
                deleteStudentSelect.appendChild(option);
            });

            deleteStudentSelect.disabled = false;
        } catch (error) {
            showMessage(error.message, false);
        }
    });
}

if (deleteStudentSelect) {
    deleteStudentSelect.addEventListener('change', async function () {
        const studentId = deleteStudentSelect.value;
        hideMessage();

        if (!studentId) {
            deleteStudentFields.classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`/cleaning/api/member/${studentId}`);
            if (!response.ok) throw new Error('학생 정보 로드 실패');

            const student = await response.json();

            deleteNameInput.value = student.name;
            deletePositionInput.value = student.position;

            deleteStudentFields.classList.remove('hidden');
        } catch (error) {
            showMessage(error.message, false);
        }
    });
}

if (formDelete) {
    formDelete.addEventListener('submit', async function (event) {
        event.preventDefault();
        hideMessage();

        const studentId = deleteStudentSelect.value;
        // 확인 메시지를 위해 <option>의 텍스트를 가져옵니다.
        const studentName = deleteStudentSelect.options[deleteStudentSelect.selectedIndex].text;

        if (!studentId) {
            showMessage("삭제할 학생을 선택하세요.", false);
            return;
        }

        // (중요) 삭제 확인
        if (!confirm(`정말로 '${studentName}' 학생을 삭제하시겠습니까?`)) {
            return; // '취소' 누르면 중단
        }

        try {
            const response = await fetch(`/cleaning/api/member/${studentId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(result.message, true);
                setTimeout(() => {
                    closeModal();
                    window.location.reload();
                }, 2000);
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            showMessage(error.message, false);
        }
    });
}

function handleApiResponse(response, tabName) {
    response.json().then(data => {

        showMessage(data.message, data.success);

        if (data.success) {
            setTimeout(() => {
                const currentUrl = new URL(window.location.href);

                if (tabName === 'delete') {
                    currentUrl.searchParams.delete('location');
                } else if (data.location) {
                    currentUrl.searchParams.set('location', data.location);
                }

                window.location.href = currentUrl.href;

            }, 2000);
        }
    }).catch(error => {
        console.error("API 응답 처리 실패:", error);
        showMessage("요청 중 오류가 발생했습니다.", false);
    });
}

const drawButton = document.getElementById('cleaning-member-draw')

if (drawButton) {
    drawButton.addEventListener('click', async function () {
        const currentGrade = gradeSelect.value;

        if (!confirm(`${currentGrade}학년 당번을 새로 뽑으시겠습니까?`)) {
            return;
        }

        try {
            const response = await fetch(`/cleaning/api/draw?grade=${currentGrade}`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            const result = await response.json();

            if (response.ok) {
                alert(result.message);
                window.location.reload();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('청소 당번 뽑기 오류:', error);
            alert(error.message || '요청 중 오류가 발생했습니다.');
        }
    });
}