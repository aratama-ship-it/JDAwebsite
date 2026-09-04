const scenesModal = document.getElementById('competitionScenesModal');
const scenesTrack = document.getElementById('competitionScenesTrack');

if (scenesModal && scenesTrack) {
  const pageHeader = document.querySelector('.preview-site-header');
  const pageMain = document.querySelector('.preview-page');
  const modalPanel = scenesModal.querySelector('.competition-scenes-modal__panel');
  const closeButton = scenesModal.querySelector('.competition-scenes-modal__close');
  const openButtons = Array.from(document.querySelectorAll('[data-open-scenes]'));
  const closeButtons = Array.from(scenesModal.querySelectorAll('[data-close-scenes]'));
  const slides = Array.from(scenesTrack.querySelectorAll('[data-scene]'));
  const prevButton = document.getElementById('competitionScenesPrev');
  const nextButton = document.getElementById('competitionScenesNext');
  const playButton = document.getElementById('competitionScenesPlay');
  const status = document.getElementById('competitionScenesStatus');
  const progress = document.getElementById('competitionScenesProgress');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const desktopPairLayout = window.matchMedia('(min-width: 901px) and (orientation: landscape)');
  const autoplayDelay = 6500;
  let pages = [];
  let activeIndex = 0;
  let activePageIndex = 0;
  let autoplayTimer = 0;
  let closeTimer = 0;
  let resizeFrame = 0;
  let scrollSyncTimer = 0;
  let isModalOpen = false;
  let isPlaying = !reducedMotion.matches;
  let resumeOnOpen = isPlaying;
  let usesAdaptiveDesktopLayout = desktopPairLayout.matches;
  let lastFocused = null;

  // モーダルをmainの外へ移し、背景側だけを安全に操作不能にできる構造にする。
  document.body.append(scenesModal);

  slides.forEach((slide) => {
    const image = slide.querySelector('img');
    slide.querySelector('figure').style.setProperty('--scene-image', `url("${image.getAttribute('src')}")`);
  });

  function getImageOrientation(slide) {
    const image = slide.querySelector('img');
    const width = image.naturalWidth || Number(image.getAttribute('width'));
    const height = image.naturalHeight || Number(image.getAttribute('height'));
    return width > height ? 'landscape' : 'portrait';
  }

  function getPageCount() {
    return pages.length;
  }

  function getCurrentPageIndex() {
    return activePageIndex;
  }

  function createPage(pageSlides, type) {
    const page = document.createElement('div');
    const firstIndex = slides.indexOf(pageSlides[0]);
    const lastIndex = slides.indexOf(pageSlides[pageSlides.length - 1]);
    page.className = `competition-scenes-v2__page ${type}`;
    page.dataset.scenePage = '';
    page.setAttribute('role', 'group');
    page.setAttribute('aria-roledescription', 'スライド');
    page.setAttribute('aria-label', firstIndex === lastIndex
      ? `写真 ${firstIndex + 1}`
      : `写真 ${firstIndex + 1}から${lastIndex + 1}`);
    pageSlides.forEach((slide) => page.append(slide));
    return page;
  }

  function buildPages(targetSlideIndex = activeIndex) {
    const pageDefinitions = [];

    if (!desktopPairLayout.matches) {
      slides.forEach((slide) => pageDefinitions.push({ slides: [slide], type: 'is-single' }));
    } else {
      let slideIndex = 0;
      while (slideIndex < slides.length) {
        const slide = slides[slideIndex];
        const orientation = getImageOrientation(slide);

        if (orientation === 'landscape') {
          pageDefinitions.push({ slides: [slide], type: 'is-landscape-single' });
          slideIndex += 1;
        } else if (
          slideIndex + 1 < slides.length
          && getImageOrientation(slides[slideIndex + 1]) === 'portrait'
        ) {
          pageDefinitions.push({ slides: [slide, slides[slideIndex + 1]], type: 'is-pair' });
          slideIndex += 2;
        } else {
          pageDefinitions.push({ slides: [slide], type: 'is-portrait-single' });
          slideIndex += 1;
        }
      }
    }

    pages = pageDefinitions.map(({ slides: pageSlides, type }) => createPage(pageSlides, type));
    scenesTrack.replaceChildren(...pages);

    const safeTargetIndex = Math.max(0, Math.min(targetSlideIndex, slides.length - 1));
    const targetSlide = slides[safeTargetIndex];
    const targetPageIndex = Math.max(0, pages.findIndex((page) => page.contains(targetSlide)));
    updateControls(targetPageIndex);
    scenesTrack.scrollTo({ left: targetPageIndex * scenesTrack.clientWidth, behavior: 'auto' });
  }

  function updateControls(pageIndex) {
    const pageCount = getPageCount();
    if (!pageCount) return;

    const safePageIndex = Math.max(0, Math.min(pageIndex, pageCount - 1));
    const visibleSlides = Array.from(pages[safePageIndex].querySelectorAll('[data-scene]'));
    const firstVisibleIndex = slides.indexOf(visibleSlides[0]);
    const lastVisibleIndex = slides.indexOf(visibleSlides[visibleSlides.length - 1]);
    activePageIndex = safePageIndex;
    activeIndex = firstVisibleIndex;
    const firstNumber = String(firstVisibleIndex + 1).padStart(2, '0');
    const lastNumber = String(lastVisibleIndex + 1).padStart(2, '0');
    const totalNumber = String(slides.length).padStart(2, '0');

    status.textContent = visibleSlides.length > 1
      ? `${firstNumber}–${lastNumber} / ${totalNumber}`
      : `${firstNumber} / ${totalNumber}`;
    progress.style.width = `${((safePageIndex + 1) / pageCount) * 100}%`;
    prevButton.disabled = safePageIndex === 0;
    nextButton.disabled = safePageIndex === pageCount - 1;
    prevButton.setAttribute('aria-label', desktopPairLayout.matches ? '前の大会写真ページへ' : '前の大会写真へ');
    nextButton.setAttribute('aria-label', desktopPairLayout.matches ? '次の大会写真ページへ' : '次の大会写真へ');
    scenesTrack.setAttribute(
      'aria-label',
      desktopPairLayout.matches ? '大会写真スライド、縦写真は2枚、横写真は1枚表示' : '大会写真スライド'
    );
    pages.forEach((page, candidatePageIndex) => {
      page.setAttribute('aria-hidden', candidatePageIndex === safePageIndex ? 'false' : 'true');
    });
    slides.forEach((slide) => {
      slide.setAttribute('aria-hidden', visibleSlides.includes(slide) ? 'false' : 'true');
    });
  }

  function updatePlayButton() {
    playButton.setAttribute('aria-pressed', String(isPlaying));
    playButton.setAttribute('aria-label', isPlaying ? '自動送りを停止' : '自動送りを再開');
  }

  function scheduleAutoplay() {
    window.clearTimeout(autoplayTimer);
    if (!isModalOpen || !isPlaying || document.hidden) return;
    autoplayTimer = window.setTimeout(() => {
      goToPage((getCurrentPageIndex() + 1) % getPageCount(), false);
    }, autoplayDelay);
  }

  function goToPage(pageIndex, stopAutoplay = true) {
    const targetPageIndex = Math.max(0, Math.min(pageIndex, getPageCount() - 1));
    scenesTrack.scrollTo({
      left: targetPageIndex * scenesTrack.clientWidth,
      behavior: reducedMotion.matches ? 'auto' : 'smooth'
    });
    updateControls(targetPageIndex);
    if (stopAutoplay) {
      isPlaying = false;
      resumeOnOpen = false;
      updatePlayButton();
    }
    scheduleAutoplay();
  }

  function syncFromScroll() {
    const pageIndex = scenesTrack.clientWidth > 0 ? Math.round(scenesTrack.scrollLeft / scenesTrack.clientWidth) : 0;
    updateControls(pageIndex);
  }

  function setBackgroundInert(inert) {
    pageHeader.inert = inert;
    pageMain.inert = inert;
  }

  function openModal(opener = null, reset = false) {
    window.clearTimeout(closeTimer);
    lastFocused = opener || (document.activeElement instanceof HTMLElement ? document.activeElement : null);
    scenesModal.hidden = false;
    isModalOpen = true;
    isPlaying = resumeOnOpen && !reducedMotion.matches;
    setBackgroundInert(true);
    document.body.classList.add('scenes-modal-open');

    if (reset) {
      scenesTrack.scrollTo({ left: 0, behavior: 'auto' });
      updateControls(0);
    } else {
      const pageIndex = getCurrentPageIndex();
      scenesTrack.scrollTo({ left: pageIndex * scenesTrack.clientWidth, behavior: 'auto' });
      updateControls(pageIndex);
    }

    updatePlayButton();
    window.requestAnimationFrame(() => {
      scenesModal.classList.add('is-open');
      window.setTimeout(() => closeButton.focus({ preventScroll: true }), 40);
    });
    scheduleAutoplay();
  }

  function closeModal() {
    if (!isModalOpen) return;
    resumeOnOpen = isPlaying;
    isPlaying = false;
    isModalOpen = false;
    window.clearTimeout(autoplayTimer);
    updatePlayButton();
    scenesModal.classList.remove('is-open');
    document.body.classList.remove('scenes-modal-open');
    setBackgroundInert(false);

    closeTimer = window.setTimeout(() => {
      scenesModal.hidden = true;
    }, reducedMotion.matches ? 0 : 280);

    if (lastFocused && document.contains(lastFocused)) {
      lastFocused.focus({ preventScroll: true });
    }
  }

  openButtons.forEach((button) => {
    button.addEventListener('click', () => openModal(button));
  });

  closeButtons.forEach((button) => {
    button.addEventListener('click', closeModal);
  });

  prevButton.addEventListener('click', () => goToPage(getCurrentPageIndex() - 1));
  nextButton.addEventListener('click', () => goToPage(getCurrentPageIndex() + 1));
  playButton.addEventListener('click', () => {
    isPlaying = !isPlaying;
    resumeOnOpen = isPlaying;
    updatePlayButton();
    scheduleAutoplay();
  });

  scenesTrack.addEventListener('pointerdown', () => {
    if (!isPlaying) return;
    isPlaying = false;
    resumeOnOpen = false;
    updatePlayButton();
    scheduleAutoplay();
  }, { passive: true });

  scenesTrack.addEventListener('scroll', () => {
    window.clearTimeout(scrollSyncTimer);
    scrollSyncTimer = window.setTimeout(syncFromScroll, 90);
  }, { passive: true });

  scenesTrack.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      goToPage(getCurrentPageIndex() - 1);
    }
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      goToPage(getCurrentPageIndex() + 1);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (!isModalOpen) return;

    if (event.key === 'Escape') {
      event.preventDefault();
      closeModal();
      return;
    }

    if (event.key !== 'Tab') return;
    const focusable = Array.from(modalPanel.querySelectorAll('button:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])'))
      .filter((element) => !element.hidden);
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  window.addEventListener('resize', () => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      const isAdaptiveDesktopLayout = desktopPairLayout.matches;
      if (isAdaptiveDesktopLayout !== usesAdaptiveDesktopLayout) {
        usesAdaptiveDesktopLayout = isAdaptiveDesktopLayout;
        buildPages(activeIndex);
        return;
      }

      updateControls(activePageIndex);
      scenesTrack.scrollTo({ left: activePageIndex * scenesTrack.clientWidth, behavior: 'auto' });
    });
  });

  document.addEventListener('visibilitychange', scheduleAutoplay);

  buildPages(0);
  updatePlayButton();

  // ホームを読み込んだ時に一度だけ自動表示する。閉じた後は上部ボタンから再表示できる。
  window.requestAnimationFrame(() => {
    window.setTimeout(() => openModal(null, true), 140);
  });
}
