const userTableRow = document.querySelectorAll('.user_row');
const allUserFios = document.querySelectorAll('.user_row__name');
const modalWindow = document.querySelector('.modal');
const modalSuccessText = modalWindow.querySelector('.modal-body span');
const closeModalWindowBtn = modalWindow.querySelector('.btn-secondary');
const deleteUserModalWindowBtn = modalWindow.querySelector('.btn-primary');
const deleteUserInputId = document.querySelector('#user_delete_id')

userTableRow.forEach((el) => {
    const userFullNameRow = el.querySelector('.user_row__name');
    const deleteUserBtn = el.querySelector('.user_row__delete');
    const userFio = userFullNameRow.textContent;

    deleteUserBtn.addEventListener('click', () => {
        const userIdBlock = deleteUserBtn.querySelector('div').textContent.trim()
        deleteUserInputId.value = userIdBlock;
        modalSuccessText.textContent = userFio;
        modalWindow.style.display = 'block'
        modalWindow.style.backgroundColor = 'rgba(0, 0, 0, 0.4)'
        document.body.classList.add('modal-open')
    })
})

closeModalWindowBtn.addEventListener('click', () => {
    modalWindow.style.display = 'none'
    document.body.classList.remove('modal-open')
})
