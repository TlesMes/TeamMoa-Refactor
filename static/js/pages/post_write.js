// 공유 게시글 작성/수정 페이지 전용 JavaScript

$(document).ready(function () {
    // Summernote 에디터 초기화
    $("#id_content").summernote({
        placeholder: "내용을 입력해주세요.",
        height: 500,
        minHeight: 500,
        maxHeight: 500,
        lang: "ko-KR",
        toolbar: [
            ["style", ["style"]],
            ["font", ["bold", "underline", "clear"]],
            ["color", ["color"]],
            ["para", ["ul", "ol", "paragraph"]],
            ["table", ["table"]],
            ["insert", ["link", "picture", "video"]],
            ["view", ["fullscreen", "help"]],
        ],
    });

    // 스타일 조정
    $("p").css("margin-bottom", "0");
    $(".note-resizebar").css("display", "none");
});

// 페이지 이탈 경고 처리
var checkUnload = true;

$(window).on("beforeunload", function () {
    if (checkUnload) {
        return "이 페이지를 벗어나면 작성된 내용은 저장되지 않습니다.";
    }
});

$("#write").on("click", function () {
    checkUnload = false;
    $("submit").submit();
});