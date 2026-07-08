// マーキー（更新情報の流れるバー）：項目数や画面幅が変わっても継ぎ目なくループするよう、
// 元の項目セットを画面幅以上になるまで複製してから、その複製ブロックをもう一度繰り返して
// ちょうど2分割のトラックを作る（CSSのtranslateX(-50%)で前半→後半が完全に一致し、途切れず巻き戻る）
//
// 表示内容は marquee-updates.txt から読み込む（Claudeを使わずメモ帳等で編集→保存→ページ再読み込みだけで更新できるようにするため）。
// file:// で開いた場合などfetchが使えない時は、HTML側にあらかじめ書かれている既定の項目をそのまま使う。
const marqueeTrack = document.getElementById('marqueeTrack');
if (marqueeTrack) {
  const speed = 26.5; // px/秒（元のデザインの速度を維持）

  function setItemsFromLines(lines) {
    marqueeTrack.innerHTML = '';
    lines.forEach((line) => {
      const span = document.createElement('span');
      span.textContent = line;
      marqueeTrack.appendChild(span);
    });
  }

  function runMarqueeLoop() {
    const originalHTML = marqueeTrack.innerHTML;

    function setupMarquee() {
      marqueeTrack.style.animation = 'none';
      marqueeTrack.innerHTML = originalHTML;
      const wrapWidth = marqueeTrack.parentElement.getBoundingClientRect().width;

      let block = originalHTML;
      let guard = 0;
      while (marqueeTrack.scrollWidth < wrapWidth && guard < 50) {
        block += originalHTML;
        marqueeTrack.innerHTML = block;
        guard += 1;
      }

      marqueeTrack.innerHTML = block + block;
      const halfWidth = marqueeTrack.scrollWidth / 2;
      marqueeTrack.style.animation = `scroll-left ${halfWidth / speed}s linear infinite`;
    }

    setupMarquee();
    window.addEventListener('resize', setupMarquee);
  }

  fetch('marquee-updates.txt?_=' + Date.now())
    .then((res) => (res.ok ? res.text() : Promise.reject()))
    .then((text) => {
      const lines = text
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line && !line.startsWith('#'));
      if (lines.length > 0) setItemsFromLines(lines);
    })
    .catch(() => {
      // marquee-updates.txt が読めない場合はHTMLに書かれている既定の項目を使う
    })
    .finally(runMarqueeLoop);
}

// ヘッダーはスクロールしても見た目を変えず、そのまま上部に固定表示する

// ハンバーガーメニュー（モバイル）の簡易トグル
const hamburger = document.getElementById('hamburger');
const mainNav = document.getElementById('mainNav');

hamburger.addEventListener('click', () => {
  mainNav.classList.toggle('open');
});

// 「大会情報」ドロップダウン：PCはホバーで開くが、モバイル(タッチ)はホバーが効かないため
// クリックでも開閉できるようにする(CSSの.is-openクラスで表示を切り替える)。
document.querySelectorAll('.nav-item.has-dropdown > .nav-trigger').forEach((trigger) => {
  trigger.addEventListener('click', (e) => {
    e.preventDefault();
    trigger.closest('.nav-item').classList.toggle('is-open');
  });
});

// ヒーローのスライドショー（Red Bull風：画像とコンテンツを一緒に切り替え）
const heroSlideshow = document.getElementById('heroSlideshow');
if (heroSlideshow) {
  const slides = heroSlideshow.querySelectorAll('.hero-slide');
  const dots = document.querySelectorAll('.hero-dot');
  let current = 0;
  let timer;

  function goToSlide(index) {
    slides[current].classList.remove('is-active');
    dots[current].classList.remove('is-active');
    current = index;
    slides[current].classList.add('is-active');
    dots[current].classList.add('is-active');
  }

  function nextSlide() {
    goToSlide((current + 1) % slides.length);
  }

  function startAutoplay() {
    timer = setInterval(nextSlide, 5000);
  }

  function resetAutoplay() {
    clearInterval(timer);
    startAutoplay();
  }

  dots.forEach((dot, i) => {
    dot.addEventListener('click', () => {
      goToSlide(i);
      resetAutoplay();
    });
  });

  startAutoplay();
}

// CHAMPIONS カルーセル：回転寿司のように時間経過で一方向に流れ続け、
// カーソルがセクション(カード含む)の上にある間だけ止まる。矢印クリック／ドラッグでの操作も可能。
const championsWrap = document.getElementById('championsWrap');
if (championsWrap) {
  const track = document.getElementById('championsTrack');

  // 表示順をリロードごとにランダム化（Fisher-Yates）
  const shuffledCards = Array.from(track.children);
  for (let i = shuffledCards.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffledCards[i], shuffledCards[j]] = [shuffledCards[j], shuffledCards[i]];
  }
  shuffledCards.forEach((card) => track.appendChild(card));

  // シャッフル済みの並びをもう一度複製して2セット分のトラックを作る
  // (マーキーと同じ「ちょうど半分の位置でtranslateXを巻き戻す」手法で、途切れず一方向に流れ続けるようにする)
  shuffledCards.forEach((card) => track.appendChild(card.cloneNode(true)));

  const prevBtn = document.getElementById('championsPrev');
  const nextBtn = document.getElementById('championsNext');
  const progressMarker = document.getElementById('championsProgressMarker');
  const progressBar = progressMarker.parentElement;
  const markerWidth = 20;
  const athletesSection = document.getElementById('athletes');

  const SPEED = 22; // px/秒。ゆっくり流れる速さ
  let offset = 0; // 現在のtranslateX量(px、正の値)
  let halfWidth = 0; // 複製した片側(1セット分)の幅
  let paused = false;
  let dragging = false;

  function measure() {
    halfWidth = track.scrollWidth / 2;
  }

  function wrapOffset() {
    if (halfWidth <= 0) return;
    offset = ((offset % halfWidth) + halfWidth) % halfWidth;
  }

  function applyOffset(animate) {
    track.style.transition = animate ? 'transform 0.4s ease' : 'none';
    track.style.transform = `translateX(-${offset}px)`;
    const trackWidth = progressBar.getBoundingClientRect().width;
    const ratio = halfWidth === 0 ? 0 : offset / halfWidth;
    progressMarker.style.left = `${ratio * trackWidth - markerWidth / 2}px`;
  }

  measure();
  applyOffset(false);
  window.addEventListener('resize', measure);

  function step(delta) {
    offset += delta;
    wrapOffset();
  }

  prevBtn.addEventListener('click', () => {
    step(-halfWidth / shuffledCards.length);
    applyOffset(true);
  });

  nextBtn.addEventListener('click', () => {
    step(halfWidth / shuffledCards.length);
    applyOffset(true);
  });

  // ポイントをドラッグして移動できるようにする
  function dragMove(clientX) {
    const trackRect = progressBar.getBoundingClientRect();
    let x = clientX - trackRect.left;
    x = Math.max(0, Math.min(trackRect.width, x));
    const ratio = trackRect.width === 0 ? 0 : x / trackRect.width;
    offset = ratio * halfWidth;
    applyOffset(false);
  }

  progressMarker.addEventListener('pointerdown', (e) => {
    dragging = true;
    progressMarker.classList.add('is-dragging');
    progressMarker.setPointerCapture(e.pointerId);
    dragMove(e.clientX);
  });

  progressMarker.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    dragMove(e.clientX);
  });

  progressMarker.addEventListener('pointerup', () => {
    dragging = false;
    progressMarker.classList.remove('is-dragging');
  });

  // カーソルがセクション(カード・矢印・進捗バーを含む)の上にある間は自動で流れるのを止める
  (athletesSection || championsWrap).addEventListener('mouseenter', () => { paused = true; });
  (athletesSection || championsWrap).addEventListener('mouseleave', () => { paused = false; });

  let lastTime = null;
  function tick(now) {
    if (lastTime === null) lastTime = now;
    const dt = now - lastTime;
    lastTime = now;
    if (!paused && !dragging) {
      step((SPEED * dt) / 1000);
      applyOffset(false);
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// お問い合わせフォームのファイル添付：選択したファイル名を表示
const cfFileInput = document.getElementById('cf-file');
const cfFileName = document.getElementById('cfFileName');
if (cfFileInput) {
  cfFileInput.addEventListener('change', () => {
    if (cfFileInput.files.length === 0) {
      cfFileName.textContent = '選択されていません';
    } else if (cfFileInput.files.length === 1) {
      cfFileName.textContent = cfFileInput.files[0].name;
    } else {
      cfFileName.textContent = `${cfFileInput.files.length}件のファイルを選択中`;
    }
  });
}

// サイト内検索
const SEARCH_INDEX = [
  { title: 'トップ', keywords: 'トップ ホーム top index', path: 'index.html#top' },
  { title: '協会について', keywords: '協会について about 沿革 目的 本協会', path: 'external/about/index.html' },
  { title: '大会情報 (CHAMPIONS)', keywords: '大会情報 大会 選手 チャンピオン champions', path: 'index.html#athletes' },
  { title: 'PICK UP', keywords: 'pickup ピックアップ 注目', path: 'index.html#news' },
  { title: '全日本ディアボロ選手権大会 (AJDC)', keywords: 'AJDC 全日本 選手権大会', path: 'external/AJDC/index.html' },
  { title: '東京国際ディアボロ競技会 (TIDC)', keywords: 'TIDC 東京国際 東京国際ディアボロ競技会', path: 'external/TIDC/jp/index.html' },
  { title: '大阪国際ディアボロ競技会 (OIDC)', keywords: 'OIDC 大阪国際 大阪国際ディアボロ競技会', path: 'external/OIDC/index.html' },
  { title: 'TAR UMT OTP TOURNAMENT 2.0', keywords: 'OTP マレーシア tournament TAR UMT', path: 'external/otp2/index.html' },
  { title: '採点規則', keywords: '採点規則 ルール rule ディアボロ競技採点規則', path: 'external/rule/index.html' },
  { title: '記録一覧', keywords: '記録一覧 records 記録', path: 'external/records/index.html' },
  { title: 'ディアボロ検定', keywords: '検定 certification 級 ディアボロ検定 トリック', path: 'external/certification/index.html' },
  { title: '事務所・店舗へのアクセス', keywords: 'アクセス access 事務所 店舗 地図 営業時間', path: 'external/access/index.html' },
  { title: '更新情報', keywords: '更新情報 news updates', path: 'external/news/index.html' },
  { title: 'お問い合わせ', keywords: 'お問い合わせ contact フォーム', path: 'external/contact/index.html' },
  { title: 'オンラインショップ', keywords: 'オンラインショップ ショップ shop store', path: 'https://diabolo.shop-pro.jp' },
];

const siteSearchEl = document.getElementById('siteSearch');
const siteSearchInput = document.getElementById('siteSearchInput');
const siteSearchResults = document.getElementById('siteSearchResults');
const siteSearchToggle = document.getElementById('siteSearchToggle');
const snsLinksEl = document.getElementById('snsLinks');
if (siteSearchEl && siteSearchInput && siteSearchResults && siteSearchToggle) {
  const root = (typeof SITE_ROOT === 'string') ? SITE_ROOT : '';

  function openSearch() {
    siteSearchEl.classList.add('is-active');
    if (snsLinksEl) snsLinksEl.classList.add('is-hidden');
    siteSearchInput.focus();
  }

  function closeSearch() {
    siteSearchEl.classList.remove('is-active');
    if (snsLinksEl) snsLinksEl.classList.remove('is-hidden');
    siteSearchResults.classList.remove('is-open');
    siteSearchInput.value = '';
    siteSearchResults.innerHTML = '';
  }

  siteSearchToggle.addEventListener('click', () => {
    if (siteSearchEl.classList.contains('is-active')) {
      closeSearch();
    } else {
      openSearch();
    }
  });

  function resolvePath(path) {
    return path.startsWith('http') ? path : root + path;
  }

  function renderResults(query) {
    const q = query.trim().toLowerCase();
    if (!q) {
      siteSearchResults.classList.remove('is-open');
      siteSearchResults.innerHTML = '';
      return;
    }
    const matches = SEARCH_INDEX.filter((item) =>
      (item.title + ' ' + item.keywords).toLowerCase().includes(q)
    ).slice(0, 6);

    if (matches.length === 0) {
      siteSearchResults.innerHTML = '<div class="site-search-empty">該当する結果がありません</div>';
    } else {
      siteSearchResults.innerHTML = matches
        .map((m) => `<a class="site-search-result" href="${resolvePath(m.path)}">${m.title}</a>`)
        .join('');
    }
    siteSearchResults.classList.add('is-open');
  }

  siteSearchInput.addEventListener('input', () => renderResults(siteSearchInput.value));
  siteSearchInput.addEventListener('focus', () => {
    if (siteSearchInput.value) renderResults(siteSearchInput.value);
  });

  siteSearchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const first = siteSearchResults.querySelector('.site-search-result');
      if (first) window.location.href = first.getAttribute('href');
    } else if (e.key === 'Escape') {
      closeSearch();
    }
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.site-search')) {
      closeSearch();
    }
  });
}

// CHAMPIONS カード：カーソル追従のキラカード（ホログラム）演出
function bindAthleteCardHolo(card) {
  const maxTilt = 5;

  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * 100;
    const py = ((e.clientY - rect.top) / rect.height) * 100;
    const rotateY = ((px / 100) - 0.5) * maxTilt;
    const rotateX = ((py / 100) - 0.5) * -maxTilt;

    card.style.setProperty('--mx', `${px}%`);
    card.style.setProperty('--my', `${py}%`);
    card.style.transform = `translateY(-6px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    card.classList.add('is-holo');
  });

  card.addEventListener('mouseleave', () => {
    card.classList.remove('is-holo');
    card.style.transform = '';
  });
}

document.querySelectorAll('.athlete-card').forEach(bindAthleteCardHolo);
