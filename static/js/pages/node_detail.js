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

    // 추천 버튼 AJAX 처리
    const recommendBtn = document.getElementById('recommendBtn');
    const recommendCount = document.getElementById('recommendCount');

    if (recommendBtn && recommendCount) {
        // 백 버튼에서 팀ID, 마인드맵ID 추출
        const backBtn = document.querySelector('.node-detail-back-btn');
        const backHref = backBtn ? backBtn.getAttribute('href') : '';
        // /mindmaps/mindmap_detail_page/{team_id}/{mindmap_id}
        const teamId = backHref.match(/mindmap_detail_page\/(\d+)\/(\d+)/)?.[1];
        const mindmapId = backHref.match(/mindmap_detail_page\/(\d+)\/(\d+)/)?.[2];

        // URL에서 노드ID 추출
        const pathParts = window.location.pathname.split('/');
        // URL: /mindmaps/node_detail_page/{pk}/{node_id}
        const nodeId = pathParts[4];

        if (!teamId || !mindmapId || !nodeId) {
            console.error('필수 ID를 찾을 수 없습니다:', { teamId, mindmapId, nodeId });
            return;
        }

        recommendBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            e.stopPropagation();

            try {
                recommendBtn.disabled = true;

                const result = await window.mindmapApi.toggleNodeRecommend(teamId, mindmapId, nodeId);

                if (result.success) {
                    // 카운트 업데이트
                    recommendCount.textContent = `추천: ${result.recommendation_count}`;
                    // 토스트 메시지
                    window.handleApiResponse(result);
                }
            } catch (error) {
                window.handleApiError(error);
            } finally {
                recommendBtn.disabled = false;
            }
        });
    }
});