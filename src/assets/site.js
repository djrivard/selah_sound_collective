/* Selah Sound Collective — site shell behaviour (nav + two-tier library filter) */
(function () {
  var t = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  if (t && links) t.addEventListener('click', function () { links.classList.toggle('open'); });

  var grid = document.getElementById('libGrid');
  if (!grid) return;
  var cards = [].slice.call(grid.querySelectorAll('[data-title]'));
  var search = document.getElementById('libSearch');
  var groupChips = [].slice.call(document.querySelectorAll('.chip[data-group]'));
  var bookRows = [].slice.call(document.querySelectorAll('.book-row'));
  var empty = document.getElementById('libEmpty');
  var hideBtn = document.getElementById('hideSoon');
  var group = 'all', book = null;
  var hideSoon = false;
  try { hideSoon = localStorage.getItem('selahHideSoon') === '1'; } catch (e) {}

  function apply() {
    var q = (search && search.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (c) {
      var okGroup = group === 'all' || c.getAttribute('data-group') === group;
      var okBook = !book || c.getAttribute('data-book') === book;
      var okText = !q || c.getAttribute('data-title').toLowerCase().indexOf(q) !== -1;
      var okSoon = !hideSoon || !c.classList.contains('soon');
      var show = okGroup && okBook && okText && okSoon;
      c.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    if (empty) empty.style.display = shown ? 'none' : 'block';
    if (hideBtn) {
      hideBtn.classList.toggle('on', hideSoon);
      hideBtn.setAttribute('aria-pressed', hideSoon ? 'true' : 'false');
      hideBtn.textContent = hideSoon ? 'Showing playable only' : 'Hide coming soon';
    }
  }

  if (hideBtn) hideBtn.addEventListener('click', function () {
    hideSoon = !hideSoon;
    try { localStorage.setItem('selahHideSoon', hideSoon ? '1' : '0'); } catch (e) {}
    apply();
  });

  function setGroup(g) {
    group = g; book = null;
    groupChips.forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-group') === g); });
    bookRows.forEach(function (r) {
      var open = r.getAttribute('data-row') === g;
      r.classList.toggle('open', open);
      if (!open) [].forEach.call(r.querySelectorAll('.chip-book'), function (b) { b.classList.remove('on'); });
    });
    apply();
  }

  groupChips.forEach(function (ch) {
    ch.addEventListener('click', function () { setGroup(ch.getAttribute('data-group')); });
  });

  bookRows.forEach(function (r) {
    [].forEach.call(r.querySelectorAll('.chip-book'), function (b) {
      b.addEventListener('click', function () {
        var name = b.getAttribute('data-book');
        if (book === name) {          // tap again to clear back to the whole testament
          book = null; b.classList.remove('on');
        } else {
          book = name;
          [].forEach.call(r.querySelectorAll('.chip-book'), function (x) { x.classList.remove('on'); });
          b.classList.add('on');
        }
        apply();
      });
    });
  });

  if (search) search.addEventListener('input', apply);
  apply();
})();

/* hero "Start Listening": bring the catalogue up ready to explore */
(function () {
  var go = document.getElementById('heroBrowse');
  if (!go) return;
  go.addEventListener('click', function (e) {
    e.preventDefault();
    var search = document.getElementById('libSearch');
    var controls = search ? search.closest('.filterbar') : null;
    (controls || search).scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(function () {
      if (search) search.focus({ preventScroll: true });
      [].forEach.call(document.querySelectorAll('.chip[data-group="ot"],.chip[data-group="nt"],.chip[data-group="other"]'),
        function (c, i) {
          setTimeout(function () { c.classList.add('flash'); }, i * 140);
          setTimeout(function () { c.classList.remove('flash'); }, 2100 + i * 140);
        });
    }, 450);
  });
})();

/* deep link: index.html?book=Psalms opens that book's shelf */
(function () {
  var book = new URLSearchParams(location.search).get('book');
  if (!book) return;
  var bchip = document.querySelector('.chip-book[data-book="' + book + '"]');
  if (!bchip) return;
  var row = bchip.closest('.book-row');
  var gchip = row && document.querySelector('.chip[data-group="' + row.getAttribute('data-row') + '"]');
  if (gchip) gchip.click();
  bchip.click();
  setTimeout(function () {
    var fb = document.querySelector('.filterbar');
    if (fb) fb.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 150);
})();
