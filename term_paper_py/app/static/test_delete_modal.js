'use strict';

function modalShown(event) {
    let button = event.relatedTarget;
    let testId = button.dataset.testId;
    let newUrl = `/testing/${testId}/delete`;
    let form = document.getElementById('deleteModalForm');
    form.action = newUrl;
}

let modal = document.getElementById('deleteModal');
modal.addEventListener('show.bs.modal', modalShown);