/**
 * 파일 업로드 드래그 앤 드롭 핸들러
 *
 * 사용법:
 * const uploader = new FileUploadHandler('id_upload_files');
 */
class FileUploadHandler {
  constructor(fileInputId) {
    this.fileInput = document.getElementById(fileInputId);
    if (!this.fileInput) {
      console.error(`File input with id "${fileInputId}" not found`);
      return;
    }

    this.dropZone = this.createDropZone();
    this.fileNameDisplay = null;
    this.maxFileSize = 10 * 1024 * 1024; // 10MB

    this.init();
  }

  createDropZone() {
    const dropZone = document.createElement('div');
    dropZone.className = 'file-drop-zone';
    dropZone.innerHTML = `
      <div class="drop-zone-content">
        <i class="ri-upload-cloud-2-line drop-zone-icon"></i>
        <p class="drop-zone-text">파일을 드래그하거나 클릭하여 업로드</p>
        <p class="drop-zone-subtext">최대 10MB까지 업로드 가능</p>
      </div>
      <div class="drop-zone-selected" style="display: none;">
        <i class="ri-file-line"></i>
        <span class="selected-file-name"></span>
        <button type="button" class="remove-file-btn" title="파일 제거">
          <i class="ri-close-line"></i>
        </button>
      </div>
    `;

    return dropZone;
  }

  init() {
    // 기존 파일 인풋을 드롭존으로 교체
    this.fileInput.style.display = 'none';
    this.fileInput.parentNode.insertBefore(this.dropZone, this.fileInput);

    // 이벤트 리스너 등록
    this.dropZone.addEventListener('click', (e) => {
      if (!e.target.closest('.remove-file-btn')) {
        this.fileInput.click();
      }
    });

    this.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
    this.dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
    this.dropZone.addEventListener('drop', (e) => this.handleDrop(e));

    this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

    // 파일 제거 버튼
    const removeBtn = this.dropZone.querySelector('.remove-file-btn');
    removeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.clearFile();
    });

    // 기존 파일이 있는 경우 표시
    this.checkExistingFile();
  }

  checkExistingFile() {
    const currentFileBox = document.querySelector('.current-file-box');
    if (currentFileBox) {
      const fileName = currentFileBox.textContent.trim();
      if (fileName) {
        this.showSelectedFile(fileName);
      }
    }
  }

  handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    this.dropZone.classList.add('drag-over');
  }

  handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    this.dropZone.classList.remove('drag-over');
  }

  handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    this.dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      this.processFile(files[0]);
    }
  }

  handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
      this.processFile(files[0]);
    }
  }

  processFile(file) {
    // 파일 크기 검증
    if (file.size > this.maxFileSize) {
      showDjangoToast('파일 크기는 10MB 이하여야 합니다.', 'error');
      return;
    }

    // DataTransfer 객체를 사용하여 파일 인풋에 파일 할당
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    this.fileInput.files = dataTransfer.files;

    this.showSelectedFile(file.name);
    showDjangoToast(`"${file.name}" 파일이 선택되었습니다.`, 'success');
  }

  showSelectedFile(fileName) {
    const content = this.dropZone.querySelector('.drop-zone-content');
    const selected = this.dropZone.querySelector('.drop-zone-selected');
    const fileNameSpan = this.dropZone.querySelector('.selected-file-name');

    content.style.display = 'none';
    selected.style.display = 'flex';
    fileNameSpan.textContent = fileName;

    this.dropZone.classList.add('has-file');
  }

  clearFile() {
    this.fileInput.value = '';

    const content = this.dropZone.querySelector('.drop-zone-content');
    const selected = this.dropZone.querySelector('.drop-zone-selected');

    content.style.display = 'flex';
    selected.style.display = 'none';

    this.dropZone.classList.remove('has-file');
    showDjangoToast('파일이 제거되었습니다.', 'info');
  }
}

// 페이지 로드 시 자동 초기화
document.addEventListener('DOMContentLoaded', function() {
  const fileInput = document.getElementById('id_upload_files');
  if (fileInput) {
    new FileUploadHandler('id_upload_files');
  }
});
