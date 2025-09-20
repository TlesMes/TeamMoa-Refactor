// 노드 상세 페이지 전용 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const deleteNodeBtn = document.getElementById('delete-node-btn');
    if (deleteNodeBtn) {
        deleteNodeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const deleteUrl = this.dataset.deleteUrl;
            showConfirmModal('이 노드를 삭제하시겠습니까?', () => {
                document.getElementById('delete-node-form').submit();
            });
        });
    }
});