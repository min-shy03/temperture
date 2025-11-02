const currentTemp = document.getElementById('current-temp');
const currentHumi = document.getElementById('current-humi');
const monthDataContainer = document.getElementById('month-data-container');
const recommendTempText = document.getElementById('recommend-temp');

// SSE를 구독하기 위한 EventSource 객체 생성
// streamUrl = temp_views에 저장한 api 주소로 서버에 접속 후 stream 함수 실행
const eventSource = new EventSource(streamUrl);

console.log(streamUrl);

eventSource.addEventListener('message', function (event) {
    try {
        // parse() = 서버로부터 받은 JSON 문자열을 자바스크립트가 쓸 수 있는 객체로 변환
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

eventSource.addEventListener('date_update', function (event) {
    console.log("날짜/추천온도 데이터 수신:", event.data);
    try {
        const data = JSON.parse(event.data);
        if (recommendTempText && data.date_str && data.recommend_temp) {
            recommendTempText.textContent = `오늘은 ${data.date_str}입니다. 추천 온도는 ${data.recommend_temp}도 입니다.`;
        }
    } catch (error) {
        console.error("SSE 날짜 데이터 처리 오류: ", error);
    }
});

eventSource.addEventListener('month_data_update', function (event) {
    console.log("월별 데이터 갱신 신호 수신", event.data);

    // .then() = 한 메소드가 끝나면 실행할 작업을 등록하는 함수 (await와 비슷한 효과다.)
    // 여기서는 fetch() 가 끝난 후 끝날 작업이 또 끝난 후 메소드를 또 지정해주었다.
    fetch(monthDataUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            if (monthDataContainer) {
                monthDataContainer.innerHTML = html;
                console.log("월별 데이터 영역이 실시간으로 교체되었습니다.");
            }
        })
        .catch(error => {
            console.error("월별 데이터 갱신 중 오류 발생:", error);
        });
});

eventSource.addEventListener('error', function (event) {
    console.error("SSE 연결 오류 발생:", event);
    // 연결이 아예 끊겼을 때
    if (event.target.readyState === EventSource.CLOSED) {
        console.log("SSE 연결이 종료되었습니다.");
        // 연결이 아직 살아 있을 때
    } else if (event.target.readyState === EventSource.CONNECTING) {
        console.log("SSE 재연결 중...");
    }
});

const editButton = document.querySelector('.temp-class-edit');
const modalBackdrop = document.querySelector('.edit-modal-backdrop');
const closeModalButton = document.querySelector('.close-modal-btn');
const tabButtons = document.querySelectorAll('.modal-tab-btn');
const tabPages = document.querySelectorAll('.modal-tab');

const csrfToken = document.getElementById('csrf_token') ? document.getElementById('csrf_token').value : "";

const formAdd = document.getElementById('form-add-location');
const addSelect = document.getElementById('add-location-select');
const addPurposeInput = document.getElementById('add-purpose');

const formEdit = document.getElementById('form-edit-location');
const editSelect = document.getElementById('edit-location-select');
const editPurposeInput = document.getElementById('edit-purpose');

const formDelete = document.getElementById('form-delete-location');
const deleteSelect = document.getElementById('delete-location-select');
const deletePurposeInput = document.getElementById('delete-purpose-readonly');

const modalToast = document.getElementById('modal-toast');
let toastTimer;

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
    if (formAdd) formAdd.reset();
    if (formEdit) formEdit.reset();
    if (formDelete) formDelete.reset();

    if (editPurposeInput) editPurposeInput.placeholder = "선택 시 목적 자동 로드";
    if (deletePurposeInput) deletePurposeInput.value = "";

    hideMessage();
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

if (editSelect) {
    editSelect.addEventListener('change', (e) => {
        const selectedLocation = e.target.value;
        editPurposeInput.placeholder = "로드 중...";

        if (!selectedLocation) {
            editPurposeInput.placeholder = "선택 시 목적 자동 로드";
            return;
        }

        const apiUrl = locationApiBaseUrl.replace('LOCATION_NAME_PLACEHOLDER', encodeURIComponent(selectedLocation));

        fetch(apiUrl, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    editPurposeInput.placeholder = data.purpose || "현재 목적 없음";
                } else {
                    showMessage(editMessage, data.message, false);
                    editPurposeInput.placeholder = "정보 로드 실패";
                }
            })
            .catch(error => {
                console.error("교실 정보 로드 실패 :", error);
                showMessage(editMessage, "오류 발생", false);
            });
    });
}

if (deleteSelect && deletePurposeInput) {
    deleteSelect.addEventListener('change', (e) => {
        const selectedLocation = e.target.value;
        deletePurposeInput.value = "로드 중...";

        if (!selectedLocation) {
            deletePurposeInput.value = "";
            return;
        }

        const apiUrl = locationApiBaseUrl.replace('LOCATION_NAME_PLACEHOLDER', encodeURIComponent(selectedLocation));

        fetch(apiUrl, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    deletePurposeInput.value = data.purpose || "현재 목적 없음";
                } else {
                    showMessage(deleteMessage, data.message, false);
                    deletePurposeInput.value = "정보 로드 실패";
                }
            })
            .catch(error => {
                console.error("교실 정보 로드 실패: ", error);
                showMessage(deleteMessage, "오류 발생", false)
            });
    });
}

if (formAdd) {
    formAdd.addEventListener('submit', (e) => {
        e.preventDefault();
        hideMessage();

        const location = addSelect.value
        const purpose = addPurposeInput.value

        if (!location) {
            showMessage(addMessage, "목적을 추가할 교실을 선택하세요.", false);
            return;
        }

        if (!purpose) {
            showMessage(addMessage, "교실 목적을 입력하세요.", false);
            return;
        }

        const apiUrl = locationApiBaseUrl.replace('LOCATION_NAME_PLACEHOLDER', encodeURIComponent(location));

        fetch(apiUrl, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ purpose: purpose })
        })
            .then(res => handleApiResponse(res, 'add'));
    });
}

if (formEdit) {
    formEdit.addEventListener('submit', (e) => {
        e.preventDefault();
        hideMessage();

        const selectedLocation = editSelect.value;
        const purpose = editPurposeInput.value;

        if (!selectedLocation) {
            showMessage(editMessage, "수정할 교실을 선택하세요.", false);
            return;
        }

        if (!purpose) {
            showMessage(editMessage, "변경할 목적을 입력하세요.", false);
            return;
        }

        const apiUrl = locationApiBaseUrl.replace('LOCATION_NAME_PLACEHOLDER', encodeURIComponent(selectedLocation));

        fetch(apiUrl, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ purpose: purpose })
        })
            .then(res => handleApiResponse(res, 'edit'));
    });
}

if (formDelete) {
    formDelete.addEventListener('submit', (e) => {
        e.preventDefault();
        hideMessage();

        const selectedLocation = deleteSelect.value;

        if (!selectedLocation) {
            showMessage(deleteMessage, "삭제할 교실을 선택하세요.", false);
            return;
        }

        if (!confirm(`정말로 '${selectedLocation} 교실을 삭제하시겠습니까?\n모든 온습도 데이터가 영구적으로 삭제됩니다.`)) {
            return;
        }

        const apiUrl = locationApiBaseUrl.replace('LOCATION_NAME_PLACEHOLDER', encodeURIComponent(selectedLocation));

        fetch(apiUrl, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
            .then(res => handleApiResponse(res, 'delete'));
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