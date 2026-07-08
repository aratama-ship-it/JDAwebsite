// チャンピオンカード：カーソル追従のキラカード（ホログラム）演出
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

// CHAMPIONS POKER：読み込み時、および引き直しボタンで5枚のカードをランダム抽選（重複あり・5枚揃いもあり得る）
const championsPokerGrid = document.getElementById('championsPokerGrid');
const championsPokerReload = document.getElementById('championsPokerReload');

if (championsPokerGrid) {
  // テスト段階のため images/poker/ 配下の5枚のみに限定（本番用に増やす場合はここに追加）
  const pokerPool = [
    { img: 'final_athlete_1.jpg', name: 'TAKAHUMI KAN', desc: '全日本選手権 3連覇' },
    { img: 'final_athlete_2.jpg', name: 'KAZUKI TADA', desc: '世界ジュニア王者' },
    { img: 'final_athlete_3.jpg', name: 'JOHEI KANNO', desc: 'フリースタイル部門 新王者' },
    { img: 'final_athlete_4.jpg', name: 'HIROMIKI TORII', desc: '全日本選手権 準優勝' },
    { img: 'final_athlete_5.jpg', name: 'TAKEMI TORII', desc: '東京国際競技会 優勝' },
  ];

  function drawPokerHand() {
    const pokerHand = Array.from({ length: 5 }, () => pokerPool[Math.floor(Math.random() * pokerPool.length)]);

    championsPokerGrid.innerHTML = pokerHand.map((athlete) => `
      <div class="poker-card">
        <div class="poker-card-inner">
          <div class="poker-card-face poker-card-face--back">
            <img src="../../images/poker/cardback.webp" alt="カードの裏面">
          </div>
          <div class="poker-card-face poker-card-face--champion">
            <div class="athlete-card">
              <div class="athlete-card-shine"></div>
              <img src="../../images/poker/${athlete.img}" alt="">
              <div class="athlete-overlay">
                <h4>${athlete.name}</h4>
                <p>${athlete.desc}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    `).join('');

    championsPokerGrid.querySelectorAll('.poker-card').forEach((card) => {
      card.addEventListener('click', () => card.classList.toggle('is-flipped'));
    });
    championsPokerGrid.querySelectorAll('.poker-card-face--champion .athlete-card').forEach(bindAthleteCardHolo);
  }

  drawPokerHand();

  if (championsPokerReload) {
    championsPokerReload.addEventListener('click', () => {
      championsPokerReload.classList.add('is-spinning');
      drawPokerHand();
      setTimeout(() => championsPokerReload.classList.remove('is-spinning'), 500);
    });
  }
}
